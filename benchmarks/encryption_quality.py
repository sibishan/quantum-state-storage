import os
import json
import time
import numpy as np
from datetime import datetime

from qiskit import QuantumCircuit
from qiskit.quantum_info import (
    Statevector, DensityMatrix, partial_trace,
    random_statevector, purity,
)

from protocol import Protocol


PURITY_TOL = 1e-9
EXPECTED_PURITY = 0.5

CONFIG = {
    "clone_counts": [2, 3, 4, 5],
    "num_states": 100,
}


def find_qubit_index(qc, register):
    for idx, bit in enumerate(qc.qubits):
        if bit in register:
            return idx
    raise RuntimeError(f"Register {register.name} not found in circuit")


def get_single_qubit_purity(statevector, qubit_idx, total_qubits):
    trace_out = [i for i in range(total_qubits) if i != qubit_idx]
    dm = partial_trace(statevector, trace_out)
    return float(purity(dm))


def run_trial(n_clones, input_sv):
    proto = Protocol(num_qubits=1, num_clones=n_clones)

    prep = QuantumCircuit(1)
    prep.initialize(input_sv.data, 0)
    proto.store_qubit(prep, index=0)

    qc = proto.get_qc()
    total_q = qc.num_qubits

    sv = Statevector(qc)

    a_idx = find_qubit_index(qc, proto.A[0]['reg'])

    signal_indices = []
    for j in range(n_clones):
        idx = find_qubit_index(qc, proto.S[0, j]['reg'])
        signal_indices.append(idx)

    noise_indices = []
    for j in range(n_clones):
        idx = find_qubit_index(qc, proto.N[0, j]['reg'])
        noise_indices.append(idx)

    a_purity = get_single_qubit_purity(sv, a_idx, total_q)

    signal_purities = []
    for j, s_idx in enumerate(signal_indices):
        p = get_single_qubit_purity(sv, s_idx, total_q)
        signal_purities.append({"clone_index": j, "purity": p})

    noise_purities = []
    for j, n_idx in enumerate(noise_indices):
        p = get_single_qubit_purity(sv, n_idx, total_q)
        noise_purities.append({"clone_index": j, "purity": p})

    return {
        "n_clones":         n_clones,
        "total_qubits":     total_q,
        "a_purity":         a_purity,
        "a_is_mixed":       abs(a_purity - EXPECTED_PURITY) < PURITY_TOL,
        "signal_purities":  signal_purities,
        "all_signals_mixed": all(
            abs(s["purity"] - EXPECTED_PURITY) < PURITY_TOL
            for s in signal_purities
        ),
        "noise_purities":   noise_purities,
        "all_noise_mixed":  all(
            abs(n["purity"] - EXPECTED_PURITY) < PURITY_TOL
            for n in noise_purities
        ),
    }


def run_benchmark():
    cfg = CONFIG
    states = [(s, random_statevector(2, seed=s)) for s in range(cfg["num_states"])]

    results = []
    done = 0
    total = len(cfg["clone_counts"]) * cfg["num_states"]

    print(f"\n{'='*55}")
    print(f" ENCRYPTION QUALITY BENCHMARK")
    print(f" n = {cfg['clone_counts']}, {cfg['num_states']} random states each")
    print(f"{'='*55}")

    for n in cfg["clone_counts"]:
        for seed, sv in states:
            res = run_trial(n, sv)
            res["state_seed"] = seed
            results.append(res)
            done += 1
            if done % 100 == 0:
                print(f"  ... {done}/{total}")

    return results


def build_summary(results):
    rows = []
    for n in sorted(set(r["n_clones"] for r in results)):
        sub = [r for r in results if r["n_clones"] == n]

        a_purities = [r["a_purity"] for r in sub]
        all_signal_purities = [
            s["purity"] for r in sub for s in r["signal_purities"]
        ]
        all_noise_purities = [
            n["purity"] for r in sub for n in r["noise_purities"]
        ]

        rows.append({
            "n_clones":       n,
            "trials":         len(sub),
            # Qubit A
            "a_mean_purity":  float(np.mean(a_purities)),
            "a_max_dev":      float(max(abs(p - EXPECTED_PURITY) for p in a_purities)),
            "a_all_mixed":    all(r["a_is_mixed"] for r in sub),
            # Signal qubits
            "signal_mean_purity": float(np.mean(all_signal_purities)),
            "signal_max_dev":     float(max(abs(p - EXPECTED_PURITY) for p in all_signal_purities)),
            "signal_all_mixed":   all(r["all_signals_mixed"] for r in sub),
            # Noise qubits
            "noise_mean_purity":  float(np.mean(all_noise_purities)),
            "noise_max_dev":      float(max(abs(p - EXPECTED_PURITY) for p in all_noise_purities)),
            "noise_all_mixed":    all(r["all_noise_mixed"] for r in sub),
        })
    return rows


def print_summary(summary):
    print(f"\n{'='*80}")
    print(f" ENCRYPTION QUALITY SUMMARY")
    print(f" Expected purity: {EXPECTED_PURITY} (maximally mixed)")
    print(f"{'='*80}")
    print(f"  {'n':>3}  {'trials':>6}  "
          f"{'A_purity':>10}  {'A_ok':>4}  "
          f"{'S_purity':>10}  {'S_ok':>4}  "
          f"{'N_purity':>10}  {'N_ok':>4}")
    print(f"  {'─'*3}  {'─'*6}  "
          f"{'─'*10}  {'─'*4}  "
          f"{'─'*10}  {'─'*4}  "
          f"{'─'*10}  {'─'*4}")

    for row in summary:
        a_ok = "✓" if row["a_all_mixed"] else "✗"
        s_ok = "✓" if row["signal_all_mixed"] else "✗"
        n_ok = "✓" if row["noise_all_mixed"] else "✗"
        print(f"  {row['n_clones']:>3}  {row['trials']:>6}  "
              f"{row['a_mean_purity']:>10.8f}  {a_ok:>4}  "
              f"{row['signal_mean_purity']:>10.8f}  {s_ok:>4}  "
              f"{row['noise_mean_purity']:>10.8f}  {n_ok:>4}")

    print(f"\n  Max deviations from {EXPECTED_PURITY}:")
    for row in summary:
        print(f"    n={row['n_clones']}: A={row['a_max_dev']:.2e}  "
              f"S={row['signal_max_dev']:.2e}  "
              f"N={row['noise_max_dev']:.2e}")


def main():
    print("Encrypted Cloning Protocol — Encryption Quality Benchmark")
    print(f"Timestamp: {datetime.now().isoformat()}")

    t_start = time.perf_counter()
    results = run_benchmark()
    wall = time.perf_counter() - t_start

    summary = build_summary(results)
    print_summary(summary)

    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "wall_time_s": round(wall, 2),
            "config": CONFIG,
            "expected_purity": EXPECTED_PURITY,
            "purity_tolerance": PURITY_TOL,
        },
        "summary": summary,
        "results": results,
    }

    out_path = "benchmarks/results/encryption_quality.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone in {wall:.1f}s  —  saved to {out_path}")


if __name__ == "__main__":
    main()