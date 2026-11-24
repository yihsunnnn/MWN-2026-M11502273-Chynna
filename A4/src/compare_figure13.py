"""Estimate Figure 13 reference coefficients from the authors' PDF color bars."""
import argparse
import csv
from itertools import combinations
from pathlib import Path

import numpy as np
import pypdfium2 as pdf


def compare_pdf(source, matrix, dataset):
    with matrix.open(newline="") as handle:
        reader = csv.reader(handle)
        labels = next(reader)[1:]
        values = {row[0]: dict(zip(labels, map(float, row[1:]))) for row in reader}
    with pdf.PdfDocument(source) as document:
        page = document[0]
        text = page.get_textpage().get_text_range().splitlines()
        if text[:len(labels)] != labels:
            raise ValueError(f"PDF and CSV axis labels differ for {dataset}")
        heatmap, colorbar = [obj.get_bounds() for obj in page.get_objects() if obj.type == 3]
        scale = 3
        height = page.get_height()
        bitmap = page.render(scale=scale)
        pixels = np.asarray(bitmap.to_pil().convert("RGB"), dtype=np.int32)

    def sample(x, y):
        return pixels[round((height - y) * scale), round(x * scale)]

    left, bottom, right, top = colorbar
    levels = np.linspace(-0.999, 0.999, 1999)
    colors = np.stack([sample((left + right) / 2, bottom + (v + 1) / 2 * (top - bottom))
                       for v in levels])
    left, bottom, right, top = heatmap
    n = len(labels)
    for i, j in combinations(range(n), 2):
        color = sample(left + (j + .5) * (right - left) / n,
                       top - (i + .5) * (top - bottom) / n)
        distance = ((colors - color) ** 2).sum(axis=1)
        estimate = float(np.median(levels[distance == distance.min()]))
        observed = values[labels[i]][labels[j]]
        yield {"Dataset": dataset, "Feature_A": labels[i], "Feature_B": labels[j],
               "Paper_Color_Estimate": round(estimate, 4), "Reproduced_Pearson_r": observed,
               "Signed_Delta": round(observed - estimate, 5),
               "Absolute_Delta": round(abs(observed - estimate), 5)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("author_corr_directory", type=Path)
    args = parser.parse_args()
    results = Path(__file__).resolve().parent.parent / "results"
    rows = []
    for panel, dataset in (("a", "d1"), ("b", "d2")):
        rows.extend(compare_pdf(args.author_corr_directory / f"corr_{dataset}_bar.pdf",
                                results / f"figure13{panel}_{dataset}_pearson.csv", dataset.upper()))
    with (results / "figure13_comparison.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
