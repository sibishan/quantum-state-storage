import json, time, os
import numpy as np
from datetime import datetime

from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import (
    Statevector, DensityMatrix, partial_trace,
    state_fidelity, random_statevector,
)
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

from protocol import Protocol


FIDELITY_TOL = 1e-9

IDEAL_CONFIG = {
    "clone_counts": [2, 3, 4, 5],
    "num_states": 100,
    "decrypt_modes": ["first", "last"],
}

NOISY_CONFIG = {
    "clone_counts": [2, 3, 4, 5],
    "num_states": 100,
    "error_rates": [
        {"label": "heron_r2", "1q": 1e-4, "2q": 5e-3},
    ],
}


def decrypt_index_for_mode(mode, n):
    if mode == "first":
        return 0
    elif mode == "last":
        return n - 1
    raise ValueError(f"Unknown mode: {mode}")


def build_protocol_circuit(n_clones, input_sv, decrypt_idx):
    p = Protocol(num_qubits=1, num_clones=n_clones)

    prep = QuantumCircuit(1)
    prep.initialize(input_sv.data, 0)

    p.store_qubit(prep, 0)
    p.retrieve_qubit(0, decrypt_idx)

    qc = p.get_qc()
    return qc, qc.num_qubits


def run_ideal_trial(n_clones, input_sv, decrypt_idx):
    t0 = time.perf_counter()
    qc, total_q = build_protocol_circuit(n_clones, input_sv, decrypt_idx)
    t_build = time.perf_counter() - t0

    t0 = time.perf_counter()
    sv = Statevector(qc)
    trace_out = list(range(1, total_q))
    dm_a = partial_trace(sv, trace_out)
    fid = float(state_fidelity(input_sv, dm_a))
    t_sim = time.perf_counter() - t0

    return {
        "n_clones":       n_clones,
        "decrypt_index":  decrypt_idx,
        "fidelity":       fid,
        "fidelity_pass":  abs(fid - 1.0) < FIDELITY_TOL,
        "total_qubits":   total_q,
        "build_time_s":   round(t_build, 6),
        "sim_time_s":     round(t_sim, 6),
    }


def make_noise_model(err_1q, err_2q):
    nm = NoiseModel()
    if err_1q > 0:
        nm.add_all_qubit_quantum_error(
            depolarizing_error(err_1q, 1), ['sx', 'x', 'rz'])
    if err_2q > 0:
        nm.add_all_qubit_quantum_error(
            depolarizing_error(err_2q, 2), ['cz'])
    return nm


def run_noisy_trial(n_clones, input_sv, decrypt_idx, err_1q, err_2q):
    qc, total_q = build_protocol_circuit(n_clones, input_sv, decrypt_idx)

    t0 = time.perf_counter()
    qc_t = transpile(qc,
                     basis_gates=['cz', 'id', 'rz', 'sx', 'x', 'reset'],
                     optimization_level=0)
    t_transpile = time.perf_counter() - t0

    qc_t.save_density_matrix()

    nm = make_noise_model(err_1q, err_2q)
    sim = AerSimulator(method='density_matrix', noise_model=nm)

    t0 = time.perf_counter()
    result = sim.run(qc_t, shots=1).result()
    t_sim = time.perf_counter() - t0

    dm_full = DensityMatrix(result.data()['density_matrix'])
    trace_out = list(range(1, total_q))
    dm_a = partial_trace(dm_full, trace_out)
    fid = float(state_fidelity(input_sv, dm_a))

    ops = dict(qc_t.count_ops())

    return {
        "n_clones":       n_clones,
        "decrypt_index":  decrypt_idx,
        "fidelity":       fid,
        "total_qubits":   total_q,
        "cz_gates":       ops.get("cz", 0),
        "circuit_depth":  qc_t.depth(),
        "transpile_s":    round(t_transpile, 6),
        "sim_time_s":     round(t_sim, 6),
        "error_rate_1q":  err_1q,
        "error_rate_2q":  err_2q,
    }


def run_ideal_benchmark():
    cfg = IDEAL_CONFIG
    states = [(s, random_statevector(2, seed=s))
              for s in range(cfg["num_states"])]

    results = []
    done = 0
    total = (len(cfg["clone_counts"])
             * len(cfg["decrypt_modes"])
             * cfg["num_states"])

    print(f"\n{'='*55}")
    print(f" IDEAL benchmark  ({total} trials)")
    print(f"{'='*55}")

    for n in cfg["clone_counts"]:
        for mode in cfg["decrypt_modes"]:
            d_idx = decrypt_index_for_mode(mode, n)
            for seed, sv in states:
                res = run_ideal_trial(n, sv, d_idx)
                res["state_seed"] = seed
                res["decrypt_mode"] = mode
                res["simulation"] = "ideal"
                results.append(res)
                done += 1
                if done % 100 == 0:
                    print(f"  ... {done}/{total}")

    fids = [r["fidelity"] for r in results]
    all_pass = all(r["fidelity_pass"] for r in results)
    print(f"  Done.  mean F = {np.mean(fids):.12f}  |  "
          f"max |1-F| = {max(abs(f-1) for f in fids):.2e}  |  "
          f"all pass = {all_pass}")
    return results


def run_noisy_benchmark():
    cfg = NOISY_CONFIG
    states = [(s, random_statevector(2, seed=s))
              for s in range(cfg["num_states"])]

    results = []
    done = 0
    total = (len(cfg["clone_counts"])
             * len(cfg["error_rates"])
             * cfg["num_states"])

    print(f"\n{'='*55}")
    print(f" NOISY benchmark  ({total} trials)")
    print(f"{'='*55}")

    for n in cfg["clone_counts"]:
        for er in cfg["error_rates"]:
            label = er["label"]
            e1, e2 = er["1q"], er["2q"]
            for seed, sv in states:
                try:
                    res = run_noisy_trial(n, sv, 0, e1, e2)
                except Exception as exc:
                    print(f"  ERROR n={n} seed={seed} {label}: {exc}")
                    continue
                res["state_seed"] = seed
                res["noise_label"] = label
                res["simulation"] = "noisy"
                results.append(res)
                done += 1
                if done % 50 == 0:
                    print(f"  ... {done}/{total}")

    if results:
        fids = [r["fidelity"] for r in results]
        print(f"  Done.  mean F = {np.mean(fids):.6f}  |  "
              f"min F = {np.min(fids):.6f}")
    return results


def ideal_summary(results):
    rows = []
    for n in sorted(set(r["n_clones"] for r in results)):
        sub = [r["fidelity"] for r in results if r["n_clones"] == n]
        rows.append({
            "n_clones":      n,
            "trials":        len(sub),
            "mean_fidelity": float(np.mean(sub)),
            "min_fidelity":  float(np.min(sub)),
            "max_deviation": float(max(abs(f - 1) for f in sub)),
        })
    return rows


def noisy_summary(results):
    rows = []
    keys = sorted(set((r["n_clones"], r["noise_label"]) for r in results))
    for n, lab in keys:
        sub = [r["fidelity"] for r in results
               if r["n_clones"] == n and r["noise_label"] == lab]
        rows.append({
            "n_clones":      n,
            "noise_label":   lab,
            "trials":        len(sub),
            "mean_fidelity": float(np.mean(sub)),
            "std_fidelity":  float(np.std(sub)),
            "min_fidelity":  float(np.min(sub)),
            "max_fidelity":  float(np.max(sub)),
        })
    return rows


def main():
    print("Encrypted Cloning Protocol — Fidelity Benchmark")
    print(f"Timestamp: {datetime.now().isoformat()}")

    t_start = time.perf_counter()

    ideal_results = run_ideal_benchmark()
    noisy_results = run_noisy_benchmark()

    wall = time.perf_counter() - t_start

    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "wall_time_s": round(wall, 2),
            "ideal_config": IDEAL_CONFIG,
            "noisy_config": NOISY_CONFIG,
            "fidelity_tolerance": FIDELITY_TOL,
        },
        "ideal_summary": ideal_summary(ideal_results),
        "noisy_summary": noisy_summary(noisy_results) if noisy_results else [],
        "ideal_results": ideal_results,
        "noisy_results": noisy_results,
    }

    out_path = "benchmarks/results/fidelity.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*55}")
    print(f" SUMMARY")
    print(f"{'='*55}")
    print(f"  Total wall time : {wall:.1f}s")
    print(f"\n  Ideal (per n):")
    for row in output["ideal_summary"]:
        print(f"    n={row['n_clones']}: mean F={row['mean_fidelity']:.12f}  "
              f"max|1-F|={row['max_deviation']:.2e}  "
              f"({row['trials']} trials)")

    if output["noisy_summary"]:
        print(f"\n  Noisy (per n, noise level):")
        for row in output["noisy_summary"]:
            print(f"    n={row['n_clones']} {row['noise_label']:>4s}: "
                  f"mean F={row['mean_fidelity']:.6f} "
                  f"+/- {row['std_fidelity']:.6f}  "
                  f"min={row['min_fidelity']:.6f}  "
                  f"({row['trials']} trials)")

    print(f"\n  Saved -> {out_path}")


if __name__ == "__main__":
    main()