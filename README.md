# Encrypted Cloning Data Structures

A Python software framework that abstracts the encrypted quantum cloning protocol of [Yamaguchi & Kempf (2026)](https://doi.org/10.1103/y4y1-1ll6) behind familiar data-structure interfaces. It provides `QArray` (indexed access) and `QStack` (LIFO access) on top of a `Protocol` class that encapsulates the underlying Qiskit quantum operations.

> Built for **Computing Science Studio 2** (UTS, 2026) — *Data Structures Enabling Quantum Encrypted Multi-Cloud Storage*.

---

## Background

The no-cloning theorem prevents arbitrary unknown quantum states from being copied, which has historically blocked redundant quantum cloud storage. Yamaguchi & Kempf (2026) recently introduced an **encrypted cloning protocol** that bypasses this constraint: an unknown state can be cloned `n` times in encrypted form, but only **one** clone can ever be deterministically decrypted — preserving fidelity 1.0 while remaining consistent with no-cloning.

This repository provides the first software framework that lifts that protocol from gate-level circuit construction to high-level data structures, so users can `set` / `get` / `push` / `pop` quantum states without writing protocol circuits by hand. The framework enforces three invariants:

1. **One-time decryption** — at most one of the `n` signal-noise pairs per slot is consumed.
2. **No-cloning** — mutations (`insert`, `remove`, `reverse`) use retrieve–swap–store cycles, never copies.
3. **No-measurement** — operations like `peek` / `contains` are intentionally excluded.

---

## Features

- **`Protocol`** — encapsulates the encrypted cloning unitary `U_enc` and decryption unitary `U_dec` as Qiskit operations.
- **`QArray`** — random-access storage with `set`, `get`, `insert`, `append`, `remove`, `reverse`.
- **`QStack`** — LIFO storage with `push` and `pop`.
- **Validated** against ideal and noisy (IBM Heron R2) simulations: fidelity 1.0 ideal, `m(2n+1)` qubit scaling, individual qubit purity matching the theoretical 0.5.
- **Zero overhead** — `QArray` and `QStack` produce identical circuits to the raw `Protocol` for the same operation sequences.

---

## Installation

Requires **Python 3.14+**. Clone and install dependencies:

```bash
git clone https://github.com/sibishan/encrypted-cloning-data-structures.git
cd encrypted-cloning-data-structures
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Core dependencies: `qiskit==2.3.1`, `qiskit-aer==0.17.2`, `numpy==2.4.3`.

---

## Quick Start

### Protocol — store and retrieve a single state

```python
from qiskit import QuantumCircuit
from protocol import Protocol

# 1 storage slot, 2 encrypted clones per slot
p = Protocol(num_qubits=1, num_clones=2)

# Prepare an arbitrary single-qubit state
qc = QuantumCircuit(1)
qc.ry(0.7, 0)
qc.rz(1.1, 0)

p.store_qubit(qc, index=0)        # encrypt into 2 clones
p.retrieve_qubit(a_index=0, c_index=0)  # decrypt clone 0 back into A_0

p.draw()
```

### QArray — indexed access

```python
from qarray import QArray

arr = QArray(num_qubits=4, num_clones=2)

arr.set(0, qc_a)        # store at index 0
arr.append(qc_b)        # store at the next free index
arr.insert(1, qc_c)     # shift right, store at index 1
arr.get(a_index=2, c_index=0)
arr.remove(0)           # uncompute index 0, shift left
arr.reverse()

circuit = arr.generate_circuit()   # locks the array, returns a QuantumCircuit
```

### QStack — LIFO access

```python
from qstack import QStack

stk = QStack(num_qubits=3, num_clones=2)

stk.push(qc_a)
stk.push(qc_b)
top = stk.pop(c_index=0)   # decrypt the most recently pushed state

print(stk)                 # ASCII visualisation of the stack
circuit = stk.generate_circuit()
```

Note: after `generate_circuit()` the data structure is locked and further mutations raise `RuntimeError`.

---

## Project Structure

```
encrypted-cloning-data-structures/
├── protocol.py         # Protocol class — encrypted cloning operations
├── qarray.py           # QArray — indexed-access data structure
├── qstack.py           # QStack — LIFO data structure
├── utils.py            # Helpers (incl. circuit-cutting utility)
├── benchmarks/         # Fidelity, purity, and resource-scaling experiments
├── tests/              # Unit tests and edge-case scripts
├── presentation/       # Circuit figures (Figures 4–18 in the report)
├── requirements.txt
├── license.txt
├── .gitignore
└── README.md
```

---

## API Overview

### `Protocol(num_qubits, num_clones)`

| Method | Description |
|---|---|
| `store_qubit(qc, index)` | Apply `U_enc` to encrypt the state at `A[index]` into `n` clones. |
| `retrieve_qubit(a_index, c_index)` | Apply `U_dec` to decrypt clone `c_index` back into `A[a_index]`. |
| `swap_a(p, q)` | Swap data qubits `A[p]` and `A[q]` (only when neither is cloned). |
| `uncompute_a(index)` | Reset `A[index]` and its clones; reinitialise Bell pairs. |
| `get_qc()` / `draw()` | Return / visualise the underlying `QuantumCircuit`. |

### `QArray(num_qubits, num_clones)`

`set`, `get`, `insert`, `append`, `remove`, `reverse`, `is_empty`, `is_full`, `size`, `clear`, `generate_circuit`, `draw`.

### `QStack(num_qubits, num_clones)`

`push`, `pop`, `is_empty`, `is_full`, `size`, `clear`, `generate_circuit`, `draw`.

---

### Validation summary

| Metric | Configuration | Result |
|---|---|---|
| Ideal decryption fidelity | `m=1`, `n ∈ {2,3,4,5}`, 800 trials | **1.0** across all trials |
| Single-qubit purity | `n ∈ {2,3,4,5}`, 400 trials | **0.5** across all qubits (A, S, N) |
| Total qubit count | All sweeps | Matches **m(2n + 1)** scaling |
| Heron R2 noisy fidelity | `n=2 → n=5`, 400 trials | ≈ 0.92 → 0.50 (gradual decay, matches hardware trend) |
| Data-structure overhead vs `Protocol` | All sweeps | Identical circuits → zero execution-time overhead |

---

## Circuit-Cutting Utility

Storage and retrieval are emitted as a single monolithic circuit, separated by Qiskit `barrier` instructions. `utils.cut_circuit(qc, idx)` splits a circuit at the `idx`-th barrier so storage and retrieval can be executed in separate runs — matching the real-world pattern of storing now and retrieving later.

---

## Authors

Computing Science Studio 2 — University of Technology Sydney, 2026.

- Aaron Abraham Thomas
- Callum Burke
- Jarrod Wallace
- Joshua Tan
- Michael Minaca
- Sibishan Ravindran

---

## License

See [`license.txt`](license.txt).