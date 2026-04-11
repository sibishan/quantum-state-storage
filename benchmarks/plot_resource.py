"""
Plot resource scaling benchmark results from benchmarks/results/resource_scaling.json

Generates:
  1. Clone sweep combined (4 panels): qubits vs n, CZ vs n, depth vs n, gate breakdown
  2. Qubit sweep combined (3 panels): qubits vs m, CZ vs m, depth vs m — per n side by side
  3. Component comparison (3 panels): CZ, total gates, depth — n=2 and n=3 together
  4. Timing breakdown: clone sweep (normalised to protocol)
  5. Timing breakdown: qubit sweep (normalised to protocol)
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
    "legend.fontsize":  9,
    "figure.dpi":       150,
    "savefig.dpi":      200,
    "savefig.bbox":     "tight",
})

COMPONENT_COLORS = {
    "protocol":          "#2563eb",
    "qarray_set_get":    "#f59e0b",
    "qarray_append_get": "#8b5cf6",
    "qstack_push_pop":   "#16a34a",
}

COMPONENT_LABELS = {
    "protocol":          "Protocol",
    "qarray_set_get":    "QArray (set/get)",
    "qarray_append_get": "QArray (append/get)",
    "qstack_push_pop":   "QStack (push/pop)",
}

COMPONENT_MARKERS = {
    "protocol":          "o",
    "qarray_set_get":    "s",
    "qarray_append_get": "D",
    "qstack_push_pop":   "^",
}

THEORETICAL_QUBITS = lambda m, n: m + 2 * m * n

OUT_DIR = "benchmarks/plots/resource_scaling"
os.makedirs(OUT_DIR, exist_ok=True)


def load_data(path="benchmarks/results/resource_scaling.json"):
    with open(path) as f:
        return json.load(f)


def get_components(results):
    return sorted(set(r["label"] for r in results))


def get_protocol_time(results, sweep_key, sweep_val, time_field):
    """Get the protocol's time for a given sweep parameter value."""
    for r in results:
        if r["label"] == "protocol" and r[sweep_key] == sweep_val:
            val = r.get(time_field)
            if val is not None and val > 0:
                return val
    return None


# ─────────────────────────────────────────────────────────────────────
# Plot 1: Clone sweep combined — qubits, CZ, depth, gate breakdown
# ─────────────────────────────────────────────────────────────────────
def plot_clone_sweep_combined(data):
    results = data["clone_sweep_results"]
    components = get_components(results)
    ns = sorted(set(r["n"] for r in results))

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    ax_q, ax_cz, ax_depth, ax_break = axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]

    # ── Panel 1: Total qubits vs n ──
    theo_q = [THEORETICAL_QUBITS(1, n) for n in ns]
    ax_q.plot(ns, theo_q, 'k--', linewidth=2, label="Theoretical: m(2n+1)", zorder=1)

    for comp in components:
        sub = sorted([r for r in results if r["label"] == comp], key=lambda r: r["n"])
        ax_q.plot([r["n"] for r in sub], [r["total_qubits"] for r in sub],
                  marker=COMPONENT_MARKERS.get(comp, "o"),
                  color=COMPONENT_COLORS.get(comp, "gray"),
                  label=COMPONENT_LABELS.get(comp, comp),
                  linewidth=1.5, markersize=7, zorder=2)

    ax_q.set_xlabel("Number of clones (n)")
    ax_q.set_ylabel("Total qubits")
    ax_q.set_title("Total Qubits vs Clones")
    ax_q.set_xticks(ns)
    ax_q.legend(fontsize=8)

    # ── Panel 2: CZ gate count vs n ──
    for comp in components:
        sub = sorted([r for r in results if r["label"] == comp], key=lambda r: r["n"])
        ax_cz.plot([r["n"] for r in sub], [r["cz_gates"] for r in sub],
                   marker=COMPONENT_MARKERS.get(comp, "o"),
                   color=COMPONENT_COLORS.get(comp, "gray"),
                   label=COMPONENT_LABELS.get(comp, comp),
                   linewidth=2, markersize=7)

    ax_cz.set_xlabel("Number of clones (n)")
    ax_cz.set_ylabel("CZ gate count")
    ax_cz.set_title("Two-Qubit (CZ) Gates vs Clones")
    ax_cz.set_xticks(ns)
    ax_cz.legend(fontsize=8)

    # ── Panel 3: Circuit depth vs n ──
    for comp in components:
        sub = sorted([r for r in results if r["label"] == comp], key=lambda r: r["n"])
        ax_depth.plot([r["n"] for r in sub], [r["circuit_depth"] for r in sub],
                      marker=COMPONENT_MARKERS.get(comp, "o"),
                      color=COMPONENT_COLORS.get(comp, "gray"),
                      label=COMPONENT_LABELS.get(comp, comp),
                      linewidth=2, markersize=7)

    ax_depth.set_xlabel("Number of clones (n)")
    ax_depth.set_ylabel("Circuit depth")
    ax_depth.set_title("Circuit Depth vs Clones")
    ax_depth.set_xticks(ns)
    ax_depth.legend(fontsize=8)

    # ── Panel 4: Gate breakdown stacked bar (protocol only) ──
    proto = sorted([r for r in results if r["label"] == "protocol"], key=lambda r: r["n"])
    if proto:
        all_types = set()
        for r in proto:
            all_types.update(r["gate_breakdown"].keys())
        all_types = sorted(all_types)

        gate_colors = plt.cm.Set2(np.linspace(0, 1, len(all_types)))
        proto_ns = [r["n"] for r in proto]
        bottoms = np.zeros(len(proto_ns))

        for i, gt in enumerate(all_types):
            vals = [r["gate_breakdown"].get(gt, 0) for r in proto]
            ax_break.bar(proto_ns, vals, bottom=bottoms, label=gt,
                         color=gate_colors[i], alpha=0.85)
            bottoms += np.array(vals)

        ax_break.set_xlabel("Number of clones (n)")
        ax_break.set_ylabel("Gate count")
        ax_break.set_title("Gate Type Breakdown (Protocol)")
        ax_break.set_xticks(proto_ns)
        ax_break.legend(title="Gate type", fontsize=7, loc='upper left')

    fig.suptitle("Clone Sweep — Resource Scaling (m=1)", fontsize=15, y=1.02)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/clone_sweep_combined.png")
    plt.close(fig)
    print(f"  Saved {OUT_DIR}/clone_sweep_combined.png")


# ─────────────────────────────────────────────────────────────────────
# Plot 2: Qubit sweep combined — qubits, CZ, depth (per n side by side)
# ─────────────────────────────────────────────────────────────────────
def plot_qubit_sweep_combined(data):
    results = data["qubit_sweep_results"]
    ns = sorted(set(r["n"] for r in results))
    components = get_components(results)

    fig, axes = plt.subplots(len(ns), 3, figsize=(16, 5 * len(ns)), squeeze=False)

    metrics = [
        ("total_qubits", "Total Qubits"),
        ("cz_gates", "CZ Gate Count"),
        ("circuit_depth", "Circuit Depth"),
    ]

    for row, n in enumerate(ns):
        ms = sorted(set(r["m"] for r in results if r["n"] == n))

        for col, (metric, ylabel) in enumerate(metrics):
            ax = axes[row, col]

            # Theoretical line for qubits
            if metric == "total_qubits":
                theo = [THEORETICAL_QUBITS(m, n) for m in ms]
                ax.plot(ms, theo, 'k--', linewidth=2, label="Theoretical: m(2n+1)",
                        zorder=1)

            for comp in components:
                sub = sorted([r for r in results if r["n"] == n and r["label"] == comp],
                             key=lambda r: r["m"])
                if sub:
                    ax.plot([r["m"] for r in sub], [r[metric] for r in sub],
                            marker=COMPONENT_MARKERS.get(comp, "o"),
                            color=COMPONENT_COLORS.get(comp, "gray"),
                            label=COMPONENT_LABELS.get(comp, comp),
                            linewidth=1.5, markersize=7, zorder=2)

            ax.set_xlabel("Number of stored qubits (m)")
            ax.set_xticks(ms)

            if col == 0:
                ax.set_ylabel(f"n = {n} clones\n\n{ylabel}")
            else:
                ax.set_ylabel(ylabel)

            if row == 0:
                ax.set_title(ylabel)

            ax.legend(fontsize=7)

    fig.suptitle("Qubit Sweep — Resource Scaling", fontsize=15, y=1.02)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/qubit_sweep_combined.png")
    plt.close(fig)
    print(f"  Saved {OUT_DIR}/qubit_sweep_combined.png")


# ─────────────────────────────────────────────────────────────────────
# Plot 3: Component comparison — CZ, total gates, depth (n=2 & n=3)
# ─────────────────────────────────────────────────────────────────────
def plot_component_comparison(data):
    results = data["qubit_sweep_results"]
    target_ns = [n for n in sorted(set(r["n"] for r in results)) if n in [2, 3]]
    components = sorted(set(r["label"] for r in results))

    if not target_ns:
        print("  Skipping component comparison (no n=2 or n=3 data)")
        return

    metrics = [
        ("cz_gates", "CZ Gate Count"),
        ("total_gates", "Total Gate Count"),
        ("circuit_depth", "Circuit Depth"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # Line styles to distinguish n values
    n_styles = {2: "-", 3: "--"}
    n_alphas = {2: 1.0, 3: 0.75}

    for ax, (metric, title) in zip(axes, metrics):
        for n in target_ns:
            for comp in components:
                sub = sorted([r for r in results if r["n"] == n and r["label"] == comp],
                             key=lambda r: r["m"])
                if sub:
                    ax.plot([r["m"] for r in sub], [r[metric] for r in sub],
                            marker=COMPONENT_MARKERS.get(comp, "o"),
                            color=COMPONENT_COLORS.get(comp, "gray"),
                            linestyle=n_styles.get(n, "-"),
                            alpha=n_alphas.get(n, 1.0),
                            label=f"{COMPONENT_LABELS.get(comp, comp)} (n={n})",
                            linewidth=2, markersize=7)

        ax.set_xlabel("Stored qubits (m)")
        ax.set_ylabel(title)
        ax.set_title(title)
        ms = sorted(set(r["m"] for r in results))
        ax.set_xticks(ms)
        ax.legend(fontsize=6, ncol=1)

    fig.suptitle("Component Comparison: n=2 (solid) vs n=3 (dashed)", fontsize=14, y=1.02)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/component_comparison.png")
    plt.close(fig)
    print(f"  Saved {OUT_DIR}/component_comparison.png")


# ─────────────────────────────────────────────────────────────────────
# Plot 4: Timing breakdown — clone sweep (normalised to protocol)
# ─────────────────────────────────────────────────────────────────────
def plot_timing_clone_sweep(data):
    results = data["clone_sweep_results"]
    components = get_components(results)
    ns = sorted(set(r["n"] for r in results))

    time_fields = [
        ("encrypt_time_s", "Encrypt"),
        ("decrypt_time_s", "Decrypt"),
        ("sim_time_s", "Simulate"),
    ]
    time_colors = ["#2563eb", "#dc2626", "#16a34a"]

    fig, axes = plt.subplots(1, len(time_fields), figsize=(6 * len(time_fields), 5),
                             sharey=True)

    for ax, (field, field_label), color in zip(axes, time_fields, time_colors):
        for comp in components:
            sub = sorted([r for r in results if r["label"] == comp], key=lambda r: r["n"])
            ns_c = [r["n"] for r in sub]

            ratios = []
            for r in sub:
                proto_time = get_protocol_time(results, "n", r["n"], field)
                raw = r.get(field)
                if proto_time and raw is not None:
                    ratios.append(raw / proto_time)
                else:
                    ratios.append(0)

            ax.plot(ns_c, ratios,
                    marker=COMPONENT_MARKERS.get(comp, "o"),
                    color=COMPONENT_COLORS.get(comp, "gray"),
                    label=COMPONENT_LABELS.get(comp, comp),
                    linewidth=2, markersize=7)

        ax.axhline(y=1.0, color="black", linestyle="--", linewidth=1, alpha=0.4)
        ax.set_xlabel("Number of clones (n)")
        ax.set_title(field_label)
        ax.set_xticks(ns)
        ax.legend(fontsize=8)

    axes[0].set_ylabel("Time (normalised to Protocol = 1.0)")
    fig.suptitle("Timing Overhead vs Protocol — Clone Sweep (m=1)", fontsize=14, y=1.02)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/timing_clone_sweep.png")
    plt.close(fig)
    print(f"  Saved {OUT_DIR}/timing_clone_sweep.png")


# ─────────────────────────────────────────────────────────────────────
# Plot 5: Timing breakdown — qubit sweep (normalised to protocol)
# ─────────────────────────────────────────────────────────────────────
def plot_timing_qubit_sweep(data):
    results = data["qubit_sweep_results"]
    ns = sorted(set(r["n"] for r in results))

    time_fields = [
        ("encrypt_time_s", "Encrypt"),
        ("decrypt_time_s", "Decrypt"),
        ("sim_time_s", "Simulate"),
    ]
    time_colors = ["#2563eb", "#dc2626", "#16a34a"]

    for n in ns:
        sub_n = [r for r in results if r["n"] == n]
        components = sorted(set(r["label"] for r in sub_n))
        ms = sorted(set(r["m"] for r in sub_n))

        fig, axes = plt.subplots(1, len(time_fields),
                                 figsize=(6 * len(time_fields), 5), sharey=True)

        for ax, (field, field_label), color in zip(axes, time_fields, time_colors):
            for comp in components:
                sub = sorted([r for r in sub_n if r["label"] == comp],
                             key=lambda r: r["m"])

                ratios = []
                ms_c = []
                for r in sub:
                    proto_time = get_protocol_time(sub_n, "m", r["m"], field)
                    raw = r.get(field)
                    if proto_time and raw is not None:
                        ratios.append(raw / proto_time)
                        ms_c.append(r["m"])
                    else:
                        ratios.append(0)
                        ms_c.append(r["m"])

                ax.plot(ms_c, ratios,
                        marker=COMPONENT_MARKERS.get(comp, "o"),
                        color=COMPONENT_COLORS.get(comp, "gray"),
                        label=COMPONENT_LABELS.get(comp, comp),
                        linewidth=2, markersize=7)

            ax.axhline(y=1.0, color="black", linestyle="--", linewidth=1, alpha=0.4)
            ax.set_xlabel("Number of stored qubits (m)")
            ax.set_title(field_label)
            ax.set_xticks(ms)
            ax.legend(fontsize=8)

        axes[0].set_ylabel("Time (normalised to Protocol = 1.0)")
        fig.suptitle(f"Timing Overhead vs Protocol — Qubit Sweep (n={n})",
                     fontsize=14, y=1.02)
        fig.tight_layout()
        fig.savefig(f"{OUT_DIR}/timing_qubit_sweep_n{n}.png")
        plt.close(fig)
        print(f"  Saved {OUT_DIR}/timing_qubit_sweep_n{n}.png")


# ─────────────────────────────────────────────────────────────────────
def main():
    print("Generating resource scaling plots...")
    data = load_data()

    plot_clone_sweep_combined(data)
    plot_qubit_sweep_combined(data)
    plot_component_comparison(data)
    plot_timing_clone_sweep(data)
    plot_timing_qubit_sweep(data)

    print(f"\nAll resource scaling plots saved to {OUT_DIR}/")


if __name__ == "__main__":
    main()