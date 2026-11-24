"""Train the ten Figure 14 regressors and plot the next-10-minute RMSE."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.tree import DecisionTreeRegressor
from threadpoolctl import threadpool_limits
import torch
from torch import nn
from xgboost import XGBRegressor

from fig5_to_fig13 import COLORS, DATA, RESULTS, save_plot

ORDER = ("LR", "PR", "LaR", "RR", "CNN", "RNN", "XGB", "LGBM", "RF", "DT")
TARGETS = ("CPU_Load", "Power")
PAPER = {"CPU_Load": ("CNN", .015, .014), "Power": ("RF", .0016, .018)}
# Bar heights digitized from the authors' load_forecast.pdf and power_forecast.pdf.
# These are graphical estimates on the published scale, separate from the prose values.
PAPER_BARS = {
    "CPU_Load": (
        (.060286, .061690, .072238, .060286, .015776, .015930, .026163, .085381, .014558, .021501),
        (.075062, .072901, .075061, .075062, .014820, .014792, .032515, .087790, .025423, .036626),
    ),
    "Power": (
        (.040294, .030895, .047809, .040294, .018920, .018891, .013830, .076983, .006677, .010288),
        (.044867, .259351, .044867, .044867, .014131, .014312, .023674, .023667, .018168, .026139),
    ),
}
SEED = 42
LOOKBACK = 6
INTERVAL = np.timedelta64(10, "m")


def prepare(dataset, target, split="chronological", *, standardize_features=True):
    raw = pd.read_csv(DATA / f"dataset{dataset}_combined.csv", parse_dates=["Time"])
    features = raw.columns.drop(["Time", "Series", "Ram", "CPU_cores", *TARGETS]).tolist()
    frame = raw[["Series", "Time", target, *features]].dropna(subset=["Series", "Time"])
    frame["Series"] = frame["Series"].str.strip()
    # Aggregate duplicate readings before constructing regular sequences.
    if frame.duplicated(["Series", "Time"]).any():
        frame = frame.groupby(["Series", "Time"], as_index=False).mean()
    frame = frame.sort_values(["Series", "Time"], ignore_index=True)
    times = frame["Time"].to_numpy()
    hosts = frame["Series"].to_numpy()
    x = frame[features].to_numpy(dtype=np.float32)
    y = frame[target].to_numpy(dtype=np.float32)
    edges = (hosts[1:] == hosts[:-1]) & (times[1:] - times[:-1] == INTERVAL)
    end = np.arange(LOOKBACK - 1, len(frame) - 1)
    valid = np.isfinite(y[end + 1])
    finite = np.isfinite(x).all(axis=1)
    for lag in range(LOOKBACK):
        valid &= edges[end - lag] & finite[end - lag]
    end = end[valid]

    label_times = times[end + 1]
    train_count = int(.7 * len(end))
    if split == "random":
        shuffled = np.random.default_rng(SEED).permutation(end)
        train, test = np.sort(shuffled[:train_count]), np.sort(shuffled[train_count:])
        cutoff = pd.NaT
    elif split == "per_server":
        # Each server contributes its earlier 70% and later 30% of eligible labels.
        boundaries = np.flatnonzero(hosts[end[1:]] != hosts[end[:-1]]) + 1
        groups = np.split(end, boundaries)
        cutoffs = [int(.7 * len(group)) for group in groups]
        train = np.concatenate([group[:cut] for group, cut in zip(groups, cutoffs)])
        test = np.concatenate([group[cut:] for group, cut in zip(groups, cutoffs)])
        cutoff = pd.NaT
    else:
        cutoff = np.sort(label_times)[train_count]
        train = end[label_times < cutoff]
        test = end[label_times >= cutoff]
    if standardize_features:
        x_scaler = StandardScaler().fit(x[train])
        x = x_scaler.transform(x)
    lower, upper = float(y[train + 1].min()), float(y[train + 1].max())
    if upper <= lower:
        raise ValueError(f"D{dataset} {target} has a constant training target")
    y = (y - lower) / (upper - lower)
    return x, y, train, test, cutoff, lower, upper, features


class LSTMRegressor(nn.Module):
    def __init__(self, features, width=32):
        super().__init__()
        self.lstm = nn.LSTM(features, width, batch_first=True)
        self.output = nn.Linear(width, 1)

    def forward(self, x):
        states, _ = self.lstm(x)
        return self.output(states[:, -1]).squeeze(-1)


def neural_prediction(name, x, y, train, test, epochs, *, width=32, deep_cnn=False):
    torch.manual_seed(SEED)
    rng = np.random.default_rng(SEED)
    model = (
        nn.Sequential(nn.Conv1d(x.shape[1], width, 3), nn.ReLU(),
                      nn.Flatten(), nn.Linear(width * (LOOKBACK - 2), 1), nn.Flatten(0))
        if name == "CNN" else LSTMRegressor(x.shape[1], width)
    )
    if name == "CNN" and deep_cnn:
        model = nn.Sequential(
            nn.Conv1d(x.shape[1], width, 3), nn.ReLU(),
            nn.Conv1d(width, width, 3), nn.ReLU(),
            nn.Flatten(), nn.Linear(width * (LOOKBACK - 4), width), nn.ReLU(),
            nn.Linear(width, 1), nn.Flatten(0),
        )
    offsets = np.arange(1 - LOOKBACK, 1)
    optimizer = torch.optim.Adam(model.parameters())

    def batch_features(index):
        values = torch.from_numpy(x[index[:, None] + offsets])
        return values.transpose(1, 2) if name == "CNN" else values

    for epoch in range(epochs):
        model.train()
        shuffled = rng.permutation(train)
        for start in range(0, len(shuffled), 2048):
            index = shuffled[start:start + 2048]
            optimizer.zero_grad(set_to_none=True)
            loss = nn.functional.mse_loss(model(batch_features(index)), torch.from_numpy(y[index + 1]))
            loss.backward()
            optimizer.step()
        print(f"  {name} epoch {epoch + 1}/{epochs}", flush=True)

    model.eval()
    with torch.inference_mode():
        return np.concatenate([
            model(batch_features(test[start:start + 8192])).numpy()
            for start in range(0, len(test), 8192)
        ])


def tree_and_linear_models(threads):
    return {
        "LR": LinearRegression(),
        "PR": make_pipeline(PolynomialFeatures(degree=2, include_bias=False), LinearRegression()),
        "LaR": Lasso(),
        "RR": Ridge(),
        "XGB": XGBRegressor(n_jobs=threads, random_state=SEED),
        "LGBM": LGBMRegressor(n_jobs=threads, random_state=SEED, verbosity=-1),
        "RF": RandomForestRegressor(n_jobs=threads, random_state=SEED),
        "DT": DecisionTreeRegressor(random_state=SEED),
    }


def full_forest_prediction(x_train, y_train, x_test, threads, progress=False):
    """Fit the default 100 trees in bounded batches using one RNG stream."""
    random_state = np.random.RandomState(SEED)
    forest = RandomForestRegressor(n_jobs=threads, random_state=random_state)
    total_trees = forest.n_estimators
    prediction_sum = np.zeros(len(x_test), dtype=np.float64)
    for start in range(0, total_trees, 10):
        count = min(10, total_trees - start)
        forest.set_params(n_estimators=count)
        forest.fit(x_train, y_train)
        prediction_sum += count * forest.predict(x_test)
        if progress:
            print(f"  RF trees: {start + count}/{total_trees}", flush=True)
    return prediction_sum / total_trees


def score(folder, args, datasets=(1, 2)):
    rows = []
    torch.set_num_threads(args.threads)
    with threadpool_limits(limits=args.threads):
        for dataset in datasets:
            for target in TARGETS:
                split = getattr(args, "split", "chronological")
                x, y, train, test, cutoff, low, high, features = prepare(dataset, target, split)
                print(f"D{dataset} {target}: {len(train):,} train / {len(test):,} test", flush=True)
                models = tree_and_linear_models(args.threads)
                x_test = x[test]
                actual = y[test + 1]
                for name in ORDER:
                    selected = train
                    if name in ("CNN", "RNN"):
                        predicted = neural_prediction(name, x, y, train, test, args.epochs)
                    elif name == "RF" and args.rf_train_limit == 0:
                        predicted = full_forest_prediction(
                            x[train], y[train + 1], x_test, args.threads, progress=True
                        )
                    else:
                        if name == "RF" and args.rf_train_limit and len(train) > args.rf_train_limit:
                            selected = np.random.default_rng(SEED).choice(
                                train, size=args.rf_train_limit, replace=False
                            )
                        model = models[name]
                        model.fit(x[selected], y[selected + 1])
                        if name == "PR":
                            predicted = np.concatenate([
                                model.predict(x_test[start:start + 32768])
                                for start in range(0, len(x_test), 32768)
                            ])
                        else:
                            predicted = model.predict(x_test)
                    rmse = float(np.sqrt(np.mean(np.square(predicted - actual), dtype=np.float64)))
                    print(f"  {name}: RMSE={rmse:.6f}", flush=True)
                    paper_model, *paper_values = PAPER[target]
                    ref = paper_values[dataset - 1] if name == paper_model else np.nan
                    rows.append({
                        "Dataset": f"D{dataset}", "Target": target, "Model": name,
                        "Split": split,
                        "RMSE_Normalized": rmse, "RMSE_Original_Units": rmse * (high - low),
                        "Paper_RMSE": ref, "Absolute_Error_vs_Paper": abs(rmse - ref),
                        "Train_Eligible": len(train), "Train_Used": len(selected), "Test_Count": len(test),
                        "Test_Start": cutoff, "Target_Train_Min": low, "Target_Train_Max": high,
                        "Lookback_Readings": LOOKBACK if name in ("CNN", "RNN") else 1,
                        "Neural_Epochs": args.epochs if name in ("CNN", "RNN") else 0,
                        "Features": "|".join(features),
                    })
                    pd.DataFrame(rows).to_csv(folder / "figure14_comparison.csv",
                                              index=False, float_format="%.8g")
    return pd.DataFrame(rows)


def plot(frame, folder, scale_labels=("train min–max scale", "train min–max scale"),
         show_reference=False, panels="ab", title_suffix=""):
    for panel, target, label, scale_label in zip("ab", TARGETS, ("CPU load", "Power"), scale_labels):
        if panel not in panels:
            continue
        fig, ax = plt.subplots(figsize=(10, 5.5), layout="constrained")
        positions = np.arange(len(ORDER))
        scores = frame[frame["Target"] == target]
        plotted = scores["RMSE_Normalized"]
        if show_reference:
            plotted = pd.concat([plotted, scores["Paper_Bar_RMSE_Approx"]])
        upper = plotted.quantile(.90)
        inset = None
        if plotted.max() > 4 * upper:
            inset = ax.inset_axes([.34, .30, .61, .53])
            inset.set(xticks=positions, xticklabels=ORDER, ylim=(0, upper * 1.15),
                      title="Detail at lower RMSE values")
            inset.tick_params(labelsize=8)
            inset.grid(axis="y", alpha=.2)
        for dataset, color, shift in zip(("D1", "D2"), COLORS, (-.19, .19)):
            ordered = scores[scores["Dataset"] == dataset].set_index("Model").loc[list(ORDER)]
            values = ordered["RMSE_Normalized"]
            ax.bar(positions + shift, values, width=.38, color=color, label=dataset)
            if inset is not None:
                inset.bar(positions + shift, values, width=.38, color=color)
            if show_reference:
                reference = ordered["Paper_Bar_RMSE_Approx"]
                ax.scatter(positions + shift, reference, marker="_", s=100, color="black",
                           label="Published bar" if dataset == "D1" else None, zorder=3)
                if inset is not None:
                    inset.scatter(positions + shift, reference, marker="_", s=55, color="black",
                                  zorder=3)
        ax.set(xticks=positions, xticklabels=ORDER, ylabel=f"RMSE ({scale_label})",
               xlabel="Model", title=f"{label} prediction, 10 minutes ahead{title_suffix}")
        ax.legend()
        ax.grid(axis="y", alpha=.25)
        ax.set_axisbelow(True)
        save_plot(fig, folder, f"figure14{panel}_{target.lower()}")


def finish(frame, folder):
    expected = {(f"D{dataset}", target, model)
                for dataset in (1, 2) for target in TARGETS for model in ORDER}
    keys = list(frame[["Dataset", "Target", "Model"]].itertuples(index=False, name=None))
    if len(keys) != len(expected) or set(keys) != expected:
        raise ValueError("Figure 14 requires one score for each dataset, target, and model")
    frame["Paper_Bar_RMSE_Approx"] = [
        PAPER_BARS[target][int(dataset[1:]) - 1][ORDER.index(model)]
        for dataset, target, model in keys
    ]
    frame["Absolute_Error_vs_Paper_Bar"] = (
        frame["RMSE_Normalized"] - frame["Paper_Bar_RMSE_Approx"]
    ).abs()
    frame.to_csv(folder / "figure14_comparison.csv", index=False, float_format="%.8g")
    plot(frame, folder)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--threads", type=int, default=6)
    parser.add_argument("--rf-train-limit", type=int, default=100000,
                        help="RF training rows per run; 0 uses the full training split")
    parser.add_argument("--plot-existing", action="store_true",
                        help="Regenerate plots from a completed comparison CSV without training")
    parser.add_argument("--split", choices=("chronological", "random"), default="chronological")
    args = parser.parse_args()
    if args.epochs < 1 or args.threads < 1 or args.rf_train_limit < 0:
        parser.error("epochs and threads must be positive; RF limit must be non-negative")
    name = "figure14" if args.split == "chronological" else "figure14_random"
    if args.rf_train_limit != 100000:
        name += "_rf_full" if args.rf_train_limit == 0 else f"_rf_{args.rf_train_limit}"
    folder = RESULTS / name
    folder.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(folder / "figure14_comparison.csv") if args.plot_existing else score(folder, args)
    finish(frame, folder)


if __name__ == "__main__":
    main()
