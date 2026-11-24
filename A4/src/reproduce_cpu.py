"""Reproduce the Figure 14a sensitivity run or replot its archived scores."""
import argparse

import numpy as np
import pandas as pd
import torch
from threadpoolctl import threadpool_limits

from fig5_to_fig13 import ROOT
from fig14 import (ORDER, PAPER_BARS, full_forest_prediction,
                   neural_prediction, plot, prepare, tree_and_linear_models)


def reproduce():
    rows = []
    for dataset, threads in ((1, 6), (2, 5)):
        torch.set_num_threads(threads)
        with threadpool_limits(threads):
            x, y, train, test, _, low, high, _ = prepare(dataset, "CPU_Load", "random")
            interval = high - low
            train_y = y[train + 1]
            test_y = y[test + 1]
            x_train, x_test = x[train], x[test]
            models = tree_and_linear_models(threads)
            for i, name in enumerate(ORDER):
                if name in ("CNN", "RNN"):
                    predicted = neural_prediction(name, x, y, train, test, 18, width=64,
                                                  deep_cnn=(name == "CNN"))
                elif name == "RF":
                    predicted = full_forest_prediction(x_train, train_y, x_test, 6, progress=True)
                else:
                    target = train_y * interval + low if name == "LaR" else train_y
                    model = models[name].fit(x_train, target)
                    if name == "PR":
                        predicted = np.concatenate([
                            model.predict(x_test[j:j + 32768])
                            for j in range(0, len(x_test), 32768)
                        ])
                    elif name == "LGBM":
                        predicted = model.predict(x_test, num_iteration=9)
                    else:
                        predicted = model.predict(x_test)
                    if name == "LaR":
                        predicted = (predicted - low) / interval
                error = np.sqrt(np.mean((predicted.astype(np.float64) - test_y) ** 2))
                rows.append({"Dataset": f"D{dataset}", "Model": name, "Target": "CPU_Load",
                             "Train_Used": len(train), "Test_Count": len(test),
                             "RMSE_Reported": error * interval / 100,
                             "Paper_Bar_RMSE_Approx": PAPER_BARS["CPU_Load"][dataset - 1][i]})
                print(rows[-1], flush=True)
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot-existing", action="store_true")
    args = parser.parse_args()
    output = ROOT / "rerun"
    output.mkdir(exist_ok=True)
    if args.plot_existing:
        frame = pd.read_csv(ROOT / "results" / "cpu_comparison.csv")
    else:
        frame = reproduce()
        frame.to_csv(output / "cpu_comparison.csv", index=False)
    plot(frame.rename(columns={"RMSE_Reported": "RMSE_Normalized"}), output,
         scale_labels=("CPU fraction", "kW"), show_reference=True, panels="a",
         title_suffix="\nLightGBM sensitivity: 9 boosting rounds")


if __name__ == "__main__":
    main()
