"""Recompute paper Figures 5–13 from the public CSVs."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.special import ndtr

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/datasets/combined"
RESULTS = ROOT / "reproduction_results"

LABELS = {
    "Network_TX": r"$N_{Tx}$ (Kbps)", "Network_RX": r"$N_{Rx}$ (Kbps)",
    "Power": "Power (W)", "CPU1_Temperature": "CPU 1 temperature (°C)",
    "CPU_Load": "CPU (%)", "Ram_Used": "RAM used (GB)",
    "CPU2_Temperature": "CPU 2 temperature (°C)",
}
# Table 3, in Mean, SD, Min, Max order.
PAPER_DIST = {
    "Network_TX": ((2.286e6, 1.466e7, 0, 1.124e9), (1.455e7, 1.941e8, 0, 5.997e9)),
    "Network_RX": ((2.875e6, 1.771e7, 0, 1.065e9), (2.559e7, 2.094e8, 0, 5.263e9)),
    "Power": ((205.58, 65.55, 55.86, 448), (546.44, 122.07, 260, 806)),
    "CPU1_Temperature": ((57, 11.06, 29.14, 82.01), (59.52, 11.60, 26.66, 79.23)),
}
# Both printed Fig. 6 CoV captions say TX. The author's notebook computes
# panel (c) from RX and panel (d) from TX. Use each panel's printed annotations.
PAPER_COV = {
    "Network_RX": (("5.5", "4.49", "1.97", "18.00", "3.29", "6.28"),
                   ("4.8", "3.87", "1.99", "20.60", "3.05", "4.74")),
    "Network_TX": (("5.03", "3.93", "1.81", "18.10", "3.28", "6.03"),
                   ("3.93", "3.19", "1.49", "27.87", "2.39", "3.95")),
    "Power": (("0.24", "0.25", "0.002", "0.37", "0.19", "0.29"),
              ("0.16", "0.18", "0.007", "0.31", "0.14", "0.18")),
    "CPU1_Temperature": (("0.13", "0.14", "0.015", "0.23", "0.10", "0.17"),
                         ("0.14", "0.14", "0.05", "0.28", "0.11", "0.15")),
}
PAPER_PEAK = {
    7: ("CPU_Load", (6.3, 2.33)), 8: ("Ram_Used", (1.6, 2.72)),
    11: ("Power", (1.59, 1.23)), 12: ("CPU1_Temperature", (1.34, 1.24)),
}
PAPER_COLUMNS = {
    "Ncpux": "CPU_cores_used", "Nvm": "No_Of_Running_vms", "Nrx": "Network_RX",
    "Ntx": "Network_TX", "R": "Ram", "CPU": "CPU_Load", "Pc": "Power",
    "Tcpu1": "CPU1_Temperature", "Tcpu2": "CPU2_Temperature", "Rx": "Ram_Used",
    "fs1": "Fan_speed1", "fs2": "Fan_speed2", "fs3": "Fan_speed3",
    "fs4": "Fan_speed4", "Tinlet": "Inlet_Temperature",
}
COLORS = ("#1f77b4", "#ff7f0e")


def save_plot(fig, folder, name):
    fig.savefig(folder / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(folder / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def save_csv(rows, folder, name):
    pd.DataFrame(rows).to_csv(folder / f"{name}.csv", index=False, float_format="%.8g")


def compare(rows, metric, dataset, method, statistic, count, paper, value):
    reference = float(paper)
    error = abs(value - reference)
    rows.append({
        "Metric": metric, "Dataset": f"D{dataset}", "Method": method, "Count": count,
        "Statistic": statistic, "Paper": reference, "Reproduced": value,
        "Absolute_Error": error,
        "Relative_Error_Percent": 100 * error / abs(reference) if reference else np.nan,
        "Rounded_Match": round(float(value), len(paper.partition(".")[2])) == reference
        if isinstance(paper, str) else None,
    })


def kde_cdf(values):
    """Evaluate seaborn's default cumulative Gaussian KDE on the full sample."""
    sample = np.sort(values.to_numpy())
    bandwidth = sample.std(ddof=1) * len(sample) ** (-.2)
    support = np.linspace(sample[0] - 3 * bandwidth, sample[-1] + 3 * bandwidth, 200)
    left = sample.searchsorted(support - 9 * bandwidth)
    right = sample.searchsorted(support + 9 * bandwidth, side="right")
    # Beyond 9 standard deviations a Gaussian CDF differs from 0 or 1 by < 2e-19.
    cumulative = np.array([
        (lo + ndtr((point - sample[lo:hi]) / bandwidth).sum()) / len(sample)
        for point, lo, hi in zip(support, left, right)
    ])
    return support, cumulative - cumulative[0]


def distribution(sets, column, kind, folder, stem):
    fig, ax = plt.subplots(figsize=(8, 6), layout="constrained")
    rows = []
    for dataset, ((raw, clean), color) in enumerate(zip(sets, COLORS), 1):
        values = raw[column].dropna()
        if kind == "pdf":
            # Same histogram and Scott-bandwidth KDE as Fig. 1/3.
            sns.distplot(values, ax=ax, color=color, label=f"D{dataset}")
            for method, frame in (("Valid values", raw), ("Complete rows", clean)):
                v = frame[column].dropna()
                for stat, ref, result in zip(
                    ("Mean", "SD", "Min", "Max"), PAPER_DIST[column][dataset - 1],
                    (v.mean(), v.std(), v.min(), v.max()),
                ):
                    compare(rows, column, dataset, method, stat, len(v), ref, result)
        else:
            support, cumulative = kde_cdf(values)
            ax.plot(support, cumulative, color=color, label=f"D{dataset}")
    ax.set(xlabel=LABELS[column], ylabel="Density" if kind == "pdf" else "CDF")
    ax.legend(loc="upper right" if kind == "pdf" else "lower right")
    if kind == "cdf":
        ax.set_ylim(0, 1.02)
        ax.grid(alpha=.25, linestyle="--")
    save_plot(fig, folder, stem)
    return rows


def plot_cov(sets, column, folder, stem):
    fig, ax = plt.subplots(figsize=(8, 6), layout="constrained")
    rows = []
    stats = ("Mean", "Median", "Min", "Max", "Q1", "Q3")
    for dataset, ((raw, clean), color) in enumerate(zip(sets, COLORS), 1):
        for method, frame in (("Valid values", raw), ("Complete rows", clean)):
            groups = frame.groupby("Series")[column].agg(["mean", "std"])
            cov = (groups["std"] / groups["mean"]).replace([np.inf, -np.inf], np.nan).dropna()
            results = (cov.mean(), cov.median(), cov.min(), cov.max(),
                       cov.quantile(.25), cov.quantile(.75))
            for stat, ref, result in zip(stats, PAPER_COV[column][dataset - 1], results):
                compare(rows, column, dataset, method, stat, len(cov), ref, result)
            if method == "Valid values":
                linestyle = "--" if dataset == 1 else ":"
                sns.ecdfplot(cov, ax=ax, color=color, label=f"D{dataset}", linestyle=linestyle)
                ax.text(.025 + .27 * (dataset - 1), .96,
                        f"D{dataset}\n" + "\n".join(f"{n} = {v:.3g}" for n, v in zip(stats, results)),
                        transform=ax.transAxes, va="top", size=10, color=color,
                        bbox={"facecolor": "white", "alpha": .83, "edgecolor": "none"})
    ax.set(xlabel="Coefficient of variation", ylabel="CDF", ylim=(0, 1.02),
           title=LABELS[column].split(" (", 1)[0])
    ax.grid(alpha=.25, linestyle="--")
    ax.legend(loc="lower right")
    save_plot(fig, folder, stem)
    return rows


def temporal(sets, number, folder):
    column, paper = PAPER_PEAK[number]
    rows = []
    for dataset, (raw, clean) in enumerate(sets, 1):
        for method, frame in (("Valid values", raw), ("Complete rows", clean)):
            hourly = frame.resample("h", on="Time")[column].agg(["mean", "max", "min", "count"])
            ratio = hourly["max"] / hourly["mean"].where(hourly["mean"].ne(0))
            compare(rows, column, dataset, method, "Mean hourly peak-to-mean", ratio.count(),
                    paper[dataset - 1], ratio.mean())
            if method == "Valid values":
                panel = f"figure{number}{'ab'[dataset - 1]}_d{dataset}"
                hourly.assign(peak_to_mean=ratio).to_csv(folder / f"{panel}_hourly.csv",
                                                        float_format="%.8g")
                fig, ax = plt.subplots(figsize=(13, 5), layout="constrained")
                for stat in ("mean", "max", "min"):
                    values = hourly[stat]
                    if number == 8 and dataset == 2:
                        values = values.where(values > 0)
                    ax.plot(values.index, values, label=stat, linewidth=1)
                if number == 8 and dataset == 2:
                    ax.set_yscale("log")
                ax.xaxis.set_major_locator(mdates.MonthLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
                ax.set(xlabel="Time", ylabel=LABELS[column], title=f"D{dataset}")
                ax.legend()
                save_plot(fig, folder, panel)
    if number == 12:
        for dataset, (raw, clean) in enumerate(sets, 1):
            for method, frame in (("Valid values", raw), ("Complete rows", clean)):
                hours = frame.resample("h", on="Time")["CPU2_Temperature"].agg(["mean", "max"])
                ratio = hours["max"] / hours["mean"].where(hours["mean"].ne(0))
                compare(rows, "CPU2_Temperature", dataset, method, "Mean hourly peak-to-mean",
                        ratio.count(), (1.44, 1.25)[dataset - 1], ratio.mean())
    save_csv(rows, folder, f"figure{number}_comparison")


def correlations(sets, folder):
    orders = (tuple(PAPER_COLUMNS), ("CPU", "Pc", "Tcpu1", "Tcpu2", "Nrx", "Ntx",
                                     "R", "Ncpux", "Rx", "Nvm"))
    counts = []
    for dataset, ((raw, _), order) in enumerate(zip(sets, orders), 1):
        selected = [PAPER_COLUMNS[name] for name in order]
        subset = raw[selected].dropna()
        subset.columns = list(order)
        matrix = subset.corr(method="pearson")
        panel = f"figure13{'ab'[dataset - 1]}_d{dataset}"
        matrix.to_csv(folder / f"{panel}_pearson.csv", float_format="%.8f")
        counts.append({"Dataset": f"D{dataset}", "Count": len(subset), "Columns": len(order)})
        fig, ax = plt.subplots(figsize=(9, 7), layout="constrained")
        sns.heatmap(matrix, cmap="vlag", vmin=-1, vmax=1, square=True, ax=ax,
                    cbar_kws={"label": "Pearson r"})
        ax.xaxis.tick_top()
        ax.tick_params(axis="x", labelrotation=90)
        ax.tick_params(axis="y", labelrotation=0)
        ax.set_title(f"D{dataset}", pad=12)
        save_plot(fig, folder, panel)
    save_csv(counts, folder, "figure13_counts")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("figures", type=int, nargs="*", help="Figure numbers (default 5–13)")
    args = parser.parse_args()
    figures = args.figures or list(range(5, 14))
    if any(n not in range(5, 14) for n in figures):
        parser.error("figure numbers must be between 5 and 13")
    plt.rcParams.update({"axes.labelsize": 19, "xtick.labelsize": 14,
                         "ytick.labelsize": 14, "legend.fontsize": 14})
    sets = []
    for dataset in (1, 2):
        raw = pd.read_csv(DATA / f"dataset{dataset}_combined.csv", parse_dates=["Time"])
        sets.append((raw, raw.dropna()))
    for number in figures:
        folder = RESULTS / f"figure{number}"
        folder.mkdir(parents=True, exist_ok=True)
        print(f"Figure {number}", flush=True)
        if number in (5, 10):
            columns = ("Network_TX", "Network_RX") if number == 5 else ("Power", "CPU1_Temperature")
            rows = []
            for panel, column in zip("ab", columns):
                rows.extend(distribution(sets, column, "pdf", folder,
                                         f"figure{number}{panel}_{column.lower()}_pdf"))
            save_csv(rows, folder, f"figure{number}_comparison")
        elif number in (6, 9):
            cdf = ("Network_RX", "Network_TX") if number == 6 else ("Power", "CPU1_Temperature")
            for panel, column in zip("ab", cdf):
                distribution(sets, column, "cdf", folder, f"figure{number}{panel}_{column.lower()}_cdf")
            rows = []
            for panel, column in zip("cd", cdf):
                rows.extend(plot_cov(sets, column, folder, f"figure{number}{panel}_{column.lower()}_cov"))
            save_csv(rows, folder, f"figure{number}_cov_comparison")
        elif number in PAPER_PEAK:
            temporal(sets, number, folder)
        else:
            correlations(sets, folder)


if __name__ == "__main__":
    main()
