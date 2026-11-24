"""Redraw the archived Figure 14b from the 20 measured power scores."""
import pandas as pd

from fig5_to_fig13 import ROOT
from fig14 import plot

if __name__ == "__main__":
    output = ROOT / "rerun"
    output.mkdir(exist_ok=True)
    frame = pd.read_csv(ROOT / "results" / "closest_setting.csv").query("Target == 'Power'")
    plot(frame.rename(columns={"RMSE_Reported": "RMSE_Normalized"}), output,
         scale_labels=("CPU fraction", "kW"), show_reference=True, panels="b")
