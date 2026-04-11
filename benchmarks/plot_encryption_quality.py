"""
Plot encryption quality benchmark results from benchmarks/results/encryption_quality.json

Generates:
  1. Mean purity per register type (A, S, N) vs n — bar chart
  2. Per-clone signal purity distribution (box plot per n)
  3. Per-clone noise purity distribution (box plot per n)
  4. Combined heatmap: mean purity across (register type, n)
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import os

# ── Style ────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "white",
    "axes.grid":        True,
    "grid.alpha":       0.3,
    "font.size":        11,
    "axes.titlesize":   13,
    "axes.labelsize":   12,
    "legend.fontsize":  10,
    "figure.dpi":       150,
    "savefig.dpi":      200,
    "savefig.bbox":     "tight",
})

COLORS = {
    "A": "#dc2626",
    "S": "#2563eb",
    "N": "#16a34a",
}

OUT_DIR = "benchmarks/plots/encryption_quality"
os.makedirs(OUT_DIR, exist_ok=True)


def load_data(path="benchmarks/results/encryption_quality.json"):
    with open(path) as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────
# Plot 1: Heatmap — mean purity across (register type, n)
# ─────────────────────────────────────────────────────────────────────
def plot_purity_heatmap(data):
    summary = data["summary"]
    ns = [row["n_clones"] for row in summary]
    labels = ["Qubit A", "Signal (S)", "Noise (N)"]

    matrix = np.array([
        [row["a_mean_purity"] for row in summary],
        [row["signal_mean_purity"] for row in summary],
        [row["noise_mean_purity"] for row in summary],
    ])

    fig, ax = plt.subplots(figsize=(8, 4))
    im = ax.imshow(matrix, cmap="RdYlGn_r", aspect="auto",
                   vmin=0.4999, vmax=0.5001)

    ax.set_xticks(range(len(ns)))
    ax.set_xticklabels([str(n) for n in ns])
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Number of clones (n)")
    ax.set_title("Mean Purity Heatmap (Expected: 0.5)")

    # Annotate cells
    for i in range(len(labels)):
        for j in range(len(ns)):
            ax.text(j, i, f"{matrix[i, j]:.10f}", ha="center", va="center",
                    fontsize=9, color="black")

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Mean purity")

    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/purity_heatmap.png")
    plt.close(fig)
    print(f"  Saved {OUT_DIR}/purity_heatmap.png")


# ─────────────────────────────────────────────────────────────────────
def main():
    print("Generating encryption quality plots...")
    data = load_data()

    plot_purity_heatmap(data)

    print(f"\nAll encryption quality plots saved to {OUT_DIR}/")


if __name__ == "__main__":
    main()