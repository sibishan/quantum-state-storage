import json, time, os
from datetime import datetime

from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import random_statevector

from protocol import Protocol
from qarray import QArray
from qstack import QStack


BASIS_GATES = ['cz', 'id', 'rz', 'sx', 'x', 'reset']

CLONE_SWEEP = {
    "clone_counts": [2, 3, 4, 5, 6, 7, 8],
    "num_qubits": 1,
}

QUBIT_SWEEP = {
    "qubit_counts": [1, 2, 3, 4],
    "clone_counts": [2, 3],
}

THEORETICAL_2Q_PER_QUBIT = lambda n: 21 * n + 11

THEORETICAL_QUBITS = lambda m, n: m + 2 * m * n


def make_prep_circuit(seed=42):
    sv = random_statevector(2, seed=seed)
    qc = QuantumCircuit(1)
    qc.initialize(sv.data, 0)
    return qc


def extract_metrics(qc, label, transpile_to_basis=True):
    t0 = time.perf_counter()
    if transpile_to_basis:
        qc_t = transpile(qc, basis_gates=BASIS_GATES, optimization_level=0)
    else:
        qc_t = qc
    transpile_time = time.perf_counter() - t0

    ops = dict(qc_t.count_ops())

    non_gate = {'barrier', 'measure', 'save_statevector', 'save_density_matrix'}
    total_gates = sum(v for k, v in ops.items() if k not in non_gate)
    cz_gates = ops.get('cz', 0)

    t0 = time.perf_counter()
    try:
        from qiskit.quantum_info import Statevector
        _ = Statevector(qc)
        sim_time = time.perf_counter() - t0
    except Exception:
        sim_time = None

    return {
        "label":          label,
        "total_qubits":   qc_t.num_qubits,
        "total_gates":    total_gates,
        "cz_gates":       cz_gates,
        "circuit_depth":  qc_t.depth(),
        "gate_breakdown": {k: v for k, v in ops.items() if k not in non_gate},
        "transpile_time_s": round(transpile_time, 6),
        "sim_time_s":       round(sim_time, 6) if sim_time is not None else None,
    }


def bench_protocol_raw(m, n):
    t0 = time.perf_counter()
    p = Protocol(num_qubits=m, num_clones=n)
    init_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    for i in range(m):
        p.store_qubit(make_prep_circuit(seed=i), index=i)
    encrypt_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    for i in range(m):
        p.retrieve_qubit(a_index=i, c_index=0)
    decrypt_time = time.perf_counter() - t0

    metrics = extract_metrics(p.get_qc(), label="protocol")
    metrics["init_time_s"] = round(init_time, 6)
    metrics["encrypt_time_s"] = round(encrypt_time, 6)
    metrics["decrypt_time_s"] = round(decrypt_time, 6)
    metrics["build_total_s"] = round(init_time + encrypt_time + decrypt_time, 6)
    return metrics


def bench_qarray_set_get(m, n):
    t0 = time.perf_counter()
    qa = QArray(num_qubits=m, num_clones=n)
    init_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    for i in range(m):
        qa.set(index=i, qc=make_prep_circuit(seed=i))
    encrypt_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    for i in range(m):
        qa.get(a_index=i, c_index=0)
    decrypt_time = time.perf_counter() - t0

    metrics = extract_metrics(qa.generate_circuit(), label="qarray_set_get")
    metrics["init_time_s"] = round(init_time, 6)
    metrics["encrypt_time_s"] = round(encrypt_time, 6)
    metrics["decrypt_time_s"] = round(decrypt_time, 6)
    metrics["build_total_s"] = round(init_time + encrypt_time + decrypt_time, 6)
    return metrics


def bench_qarray_append_get(m, n):
    t0 = time.perf_counter()
    qa = QArray(num_qubits=m, num_clones=n)
    init_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    for i in range(m):
        qa.append(qc=make_prep_circuit(seed=i))
    encrypt_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    for i in range(m):
        qa.get(a_index=i, c_index=0)
    decrypt_time = time.perf_counter() - t0

    metrics = extract_metrics(qa.generate_circuit(), label="qarray_append_get")
    metrics["init_time_s"] = round(init_time, 6)
    metrics["encrypt_time_s"] = round(encrypt_time, 6)
    metrics["decrypt_time_s"] = round(decrypt_time, 6)
    metrics["build_total_s"] = round(init_time + encrypt_time + decrypt_time, 6)
    return metrics


def bench_qstack_push_pop(m, n):
    t0 = time.perf_counter()
    qs = QStack(num_qubits=m, num_clones=n)
    init_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    for i in range(m):
        qs.push(qc=make_prep_circuit(seed=i))
    encrypt_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    for i in range(m):
        qs.pop(c_index=0)
    decrypt_time = time.perf_counter() - t0

    metrics = extract_metrics(qs.generate_circuit(), label="qstack_push_pop")
    metrics["init_time_s"] = round(init_time, 6)
    metrics["encrypt_time_s"] = round(encrypt_time, 6)
    metrics["decrypt_time_s"] = round(decrypt_time, 6)
    metrics["build_total_s"] = round(init_time + encrypt_time + decrypt_time, 6)
    return metrics


def run_clone_sweep():
    cfg = CLONE_SWEEP
    m = cfg["num_qubits"]
    results = []

    print(f"\n{'='*55}")
    print(f" CLONE SWEEP  (m={m}, n={cfg['clone_counts']})")
    print(f"{'='*55}")

    for n in cfg["clone_counts"]:
        theoretical_2q = THEORETICAL_2Q_PER_QUBIT(n) * m
        theoretical_q = THEORETICAL_QUBITS(m, n)

        row_base = {
            "sweep":       "clone",
            "m":           m,
            "n":           n,
            "theoretical_2q_per_qubit": THEORETICAL_2Q_PER_QUBIT(n),
            "theoretical_2q_total":     theoretical_2q,
            "theoretical_qubits":       theoretical_q,
        }

        for bench_fn in [bench_protocol_raw, bench_qarray_set_get, bench_qstack_push_pop]:
            metrics = bench_fn(m, n)
            metrics["qubits_match_theory"] = (metrics["total_qubits"] == theoretical_q)
            metrics["2q_overhead_vs_theory"] = metrics["cz_gates"] - theoretical_2q
            metrics["2q_overhead_ratio"] = round(metrics["cz_gates"] / theoretical_2q, 4) if theoretical_2q > 0 else None
            row = {**row_base, **metrics}
            results.append(row)

        print(f"  n={n} done")

    return results


def run_qubit_sweep():
    cfg = QUBIT_SWEEP
    results = []

    for n in cfg["clone_counts"]:
        print(f"\n{'='*55}")
        print(f" QUBIT SWEEP  (n={n}, m={cfg['qubit_counts']})")
        print(f"{'='*55}")

        for m in cfg["qubit_counts"]:
            theoretical_2q = THEORETICAL_2Q_PER_QUBIT(n) * m
            theoretical_q = THEORETICAL_QUBITS(m, n)

            row_base = {
                "sweep":       "qubit",
                "m":           m,
                "n":           n,
                "theoretical_2q_per_qubit": THEORETICAL_2Q_PER_QUBIT(n),
                "theoretical_2q_total":     theoretical_2q,
                "theoretical_qubits":       theoretical_q,
            }

            for bench_fn in [bench_protocol_raw, bench_qarray_set_get,
                             bench_qarray_append_get, bench_qstack_push_pop]:
                metrics = bench_fn(m, n)
                metrics["qubits_match_theory"] = (metrics["total_qubits"] == theoretical_q)
                metrics["2q_overhead_vs_theory"] = metrics["cz_gates"] - theoretical_2q
                metrics["2q_overhead_ratio"] = round(metrics["cz_gates"] / theoretical_2q, 4) if theoretical_2q > 0 else None
                row = {**row_base, **metrics}
                results.append(row)

            print(f"  m={m} done")

    return results


def print_clone_sweep_summary(results):
    print(f"\n{'='*100}")
    print(f" CLONE SWEEP SUMMARY (m=1)")
    print(f"{'='*100}")
    print(f"  {'n':>3}  {'label':<22}  {'qubits':>6}  {'q_ok':>4}  {'CZ':>6}  "
          f"{'theory':>6}  {'ratio':>6}  {'depth':>6}  "
          f"{'enc_s':>8}  {'dec_s':>8}  {'sim_s':>8}")
    print(f"  {'─'*3}  {'─'*22}  {'─'*6}  {'─'*4}  {'─'*6}  "
          f"{'─'*6}  {'─'*6}  {'─'*6}  "
          f"{'─'*8}  {'─'*8}  {'─'*8}")

    for r in sorted(results, key=lambda x: (x["n"], x["label"])):
        q_ok = "✓" if r["qubits_match_theory"] else "✗"
        ratio = f"{r['2q_overhead_ratio']:.2f}x" if r["2q_overhead_ratio"] else "—"
        sim = f"{r['sim_time_s']:.4f}" if r.get("sim_time_s") is not None else "—"
        print(f"  {r['n']:>3}  {r['label']:<22}  {r['total_qubits']:>6}  {q_ok:>4}  "
              f"{r['cz_gates']:>6}  {r['theoretical_2q_total']:>6}  "
              f"{ratio:>6}  {r['circuit_depth']:>6}  "
              f"{r['encrypt_time_s']:>8.4f}  {r['decrypt_time_s']:>8.4f}  "
              f"{sim:>8}")


def print_qubit_sweep_summary(results):
    for n in sorted(set(r["n"] for r in results)):
        sub = [r for r in results if r["n"] == n]
        print(f"\n{'='*100}")
        print(f" QUBIT SWEEP SUMMARY (n={n})")
        print(f"{'='*100}")
        print(f"  {'m':>3}  {'label':<22}  {'qubits':>6}  {'q_ok':>4}  {'CZ':>6}  "
              f"{'theory':>6}  {'ratio':>6}  {'depth':>6}  "
              f"{'enc_s':>8}  {'dec_s':>8}  {'sim_s':>8}")
        print(f"  {'─'*3}  {'─'*22}  {'─'*6}  {'─'*4}  {'─'*6}  "
              f"{'─'*6}  {'─'*6}  {'─'*6}  "
              f"{'─'*8}  {'─'*8}  {'─'*8}")

        for r in sorted(sub, key=lambda x: (x["m"], x["label"])):
            q_ok = "✓" if r["qubits_match_theory"] else "✗"
            ratio = f"{r['2q_overhead_ratio']:.2f}x" if r["2q_overhead_ratio"] else "—"
            sim = f"{r['sim_time_s']:.4f}" if r.get("sim_time_s") is not None else "—"
            print(f"  {r['m']:>3}  {r['label']:<22}  {r['total_qubits']:>6}  {q_ok:>4}  "
                  f"{r['cz_gates']:>6}  {r['theoretical_2q_total']:>6}  "
                  f"{ratio:>6}  {r['circuit_depth']:>6}  "
                  f"{r['encrypt_time_s']:>8.4f}  {r['decrypt_time_s']:>8.4f}  "
                  f"{sim:>8}")


def main():
    print("Encrypted Cloning Protocol — Circuit Resource Scaling Benchmark")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Basis gates: {BASIS_GATES}")

    t_start = time.perf_counter()

    clone_results = run_clone_sweep()
    qubit_results = run_qubit_sweep()

    wall = time.perf_counter() - t_start

    print_clone_sweep_summary(clone_results)
    print_qubit_sweep_summary(qubit_results)

    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "basis_gates": BASIS_GATES,
            "wall_time_s": round(wall, 2),
            "clone_sweep_config": CLONE_SWEEP,
            "qubit_sweep_config": QUBIT_SWEEP,
        },
        "clone_sweep_results": clone_results,
        "qubit_sweep_results": qubit_results,
    }

    out_path = "benchmarks/results/resource_scaling.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone in {wall:.1f}s  —  saved to {out_path}")


if __name__ == "__main__":
    main()