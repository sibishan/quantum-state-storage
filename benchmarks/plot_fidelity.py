"""
Plot fidelity benchmark results from benchmarks/results/fidelity.json

Generates:
  1. Combined ideal and noisy fidelity vs n
  2. Noisy fidelity distribution (box plot per n)
  3. Simulation time vs n (ideal and noisy)
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

COLORS = ["#2563eb", "#dc2626", "#16a34a", "#f59e0b", "#8b5cf6"]

OUT_DIR = "benchmarks/plots/fidelity"
os.makedirs(OUT_DIR, exist_ok=True)


def load_data(path="benchmarks/results/fidelity.json"):
    with open(path) as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────
# Plot 1: Combined ideal and noisy fidelity vs n
# ─────────────────────────────────────────────────────────────────────
def plot_combined_fidelity(data):
    ideal_results = data["ideal_results"]
    noisy_summary = data["noisy_summary"]

    # Ideal: mean fidelity per n (across all decrypt modes and states)
    ideal_ns = sorted(set(r["n_clones"] for r in ideal_results))
    ideal_means = []
    for n in ideal_ns:
        sub = [r["fidelity"] for r in ideal_results if r["n_clones"] == n]
        ideal_means.append(np.mean(sub))

    fig, ax = plt.subplots(figsize=(8, 5))

    # Ideal line
    ax.plot(ideal_ns, ideal_means, 'o-', color=COLORS[2], linewidth=2,
            markersize=8, label="Ideal (statevector)", zorder=3)

    # Noisy with error bars
    if noisy_summary:
        noisy_ns = [row["n_clones"] for row in noisy_summary]
        noisy_means = [row["mean_fidelity"] for row in noisy_summary]
        noisy_stds = [row["std_fidelity"] for row in noisy_summary]
        noisy_mins = [row["min_fidelity"] for row in noisy_summary]

        ax.errorbar(noisy_ns, noisy_means, yerr=noisy_stds, fmt='s-',
                    color=COLORS[1], capsize=5, capthick=1.5, linewidth=2,
                    markersize=8, label="Noisy — Heron R2 (mean ± std)", zorder=3)
        ax.scatter(noisy_ns, noisy_mins, marker='v', color=COLORS[3], s=60,
                   label="Noisy — min fidelity", zorder=4)

    ax.set_xlabel("Number of clones (n)")
    ax.set_ylabel("Decryption Fidelity")
    ax.set_title("Decryption Fidelity: Ideal vs Noisy Simulation")
    ax.set_xticks(ideal_ns)
    ax.legend()
    ax.set_ylim(0, 1.05)

    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/combined_fidelity.png")
    plt.close(fig)
    print(f"  Saved {OUT_DIR}/combined_fidelity.png")


# ─────────────────────────────────────────────────────────────────────
# Plot 2: Noisy fidelity distribution (box plot)
# ─────────────────────────────────────────────────────────────────────
def plot_noisy_fidelity_boxplot(data):
    results = data["noisy_results"]
    if not results:
        print("  Skipping noisy boxplot (no data)")
        return

    ns = sorted(set(r["n_clones"] for r in results))
    fid_by_n = [[r["fidelity"] for r in results if r["n_clones"] == n] for n in ns]

    fig, ax = plt.subplots(figsize=(8, 5))

    bp = ax.boxplot(fid_by_n, labels=[str(n) for n in ns], patch_artist=True,
                    showmeans=True, meanprops=dict(marker='D', markerfacecolor='white',
                                                    markeredgecolor='black', markersize=6))

    for patch, color in zip(bp['boxes'], COLORS):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)

    ax.set_xlabel("Number of clones (n)")
    ax.set_ylabel("Decryption Fidelity")
    ax.set_title("Fidelity Distribution Under Heron R2 Noise Model")

    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/noisy_fidelity_boxplot.png")
    plt.close(fig)
    print(f"  Saved {OUT_DIR}/noisy_fidelity_boxplot.png")


# ─────────────────────────────────────────────────────────────────────
# Plot 3: Simulation time vs n (ideal and noisy)
# ─────────────────────────────────────────────────────────────────────
def plot_simulation_times(data):
    ideal = data["ideal_results"]
    noisy = data["noisy_results"]

    # Ideal: average sim_time per n (across all modes and states)
    ideal_ns = sorted(set(r["n_clones"] for r in ideal))
    ideal_times = []
    for n in ideal_ns:
        sub = [r["sim_time_s"] for r in ideal if r["n_clones"] == n]
        ideal_times.append(np.mean(sub))

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(ideal_ns, ideal_times, 'o-', color=COLORS[0], linewidth=2,
            markersize=8, label="Ideal (statevector)")

    if noisy:
        noisy_ns = sorted(set(r["n_clones"] for r in noisy))
        noisy_times = []
        for n in noisy_ns:
            sub = [r["sim_time_s"] for r in noisy if r["n_clones"] == n]
            noisy_times.append(np.mean(sub))
        ax.plot(noisy_ns, noisy_times, 's-', color=COLORS[1], linewidth=2,
                markersize=8, label="Noisy (density matrix)")

    ax.set_xlabel("Number of clones (n)")
    ax.set_ylabel("Mean simulation time (s)")
    ax.set_title("Simulation Time vs Number of Clones")
    ax.set_xticks(ideal_ns)
    ax.legend()
    ax.set_yscale("log")

    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/simulation_times.png")
    plt.close(fig)
    print(f"  Saved {OUT_DIR}/simulation_times.png")


# ─────────────────────────────────────────────────────────────────────
def main():
    print("Generating fidelity benchmark plots...")
    data = load_data()

    plot_combined_fidelity(data)
    plot_noisy_fidelity_boxplot(data)
    plot_simulation_times(data)

    print(f"\nAll fidelity plots saved to {OUT_DIR}/")


if __name__ == "__main__":
    main()