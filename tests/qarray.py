import os
from qiskit import QuantumCircuit
from qiskit.quantum_info import random_statevector

from qarray import QArray

OUT_DIR = "tests/out/qarray"


def make_state(label: str) -> QuantumCircuit:
    """Create a 1-qubit circuit initialized to a random state.
    Adds a label so you can visually distinguish different states."""
    qc = QuantumCircuit(1)
    psi = random_statevector(2)
    qc.initialize(psi, 0)
    qc.metadata = {"label": label}
    return qc


def save(array, test_name: str, step: str):
    """Draw the array circuit and save to tests/out/qarray/<test>/<step>.png"""
    path = os.path.join(OUT_DIR, test_name)
    os.makedirs(path, exist_ok=True)
    import matplotlib.pyplot as plt
    fig = array.draw()
    fig.savefig(os.path.join(path, f"{step}.png"), bbox_inches="tight")
    plt.close(fig)
    print(f"  saved: {path}/{step}.png")


# ═══════════════════════════════════════════════════════════════════════════
#  TEST 1 — Set single slot
#  Expected: only slot 0 should contain state A, rest empty
# ═══════════════════════════════════════════════════════════════════════════

def test_01_set_single():
    print("\n── Test 01: Set single slot ──")
    arr = QArray(num_qubits=4, num_clones=1)
    A = make_state("A")

    save(arr, "01_set_single", "0_empty")

    arr.set(0, A)
    save(arr, "01_set_single", "1_set0_A")


# ═══════════════════════════════════════════════════════════════════════════
#  TEST 2 — Set all slots
#  Expected: every slot filled, each with a distinguishable state
# ═══════════════════════════════════════════════════════════════════════════

def test_02_set_all():
    print("\n── Test 02: Set all slots ──")
    arr = QArray(num_qubits=4, num_clones=1)
    A, B, C, D = [make_state(l) for l in "ABCD"]

    arr.set(0, A)
    arr.set(1, B)
    arr.set(2, C)
    arr.set(3, D)
    save(arr, "02_set_all", "0_A_B_C_D")


# ═══════════════════════════════════════════════════════════════════════════
#  TEST 3 — Set then overwrite
#  Expected: slot 1 should show state X, not the original B
# ═══════════════════════════════════════════════════════════════════════════

def test_03_set_overwrite():
    print("\n── Test 03: Set then overwrite ──")
    arr = QArray(num_qubits=3, num_clones=1)
    A, B, X = make_state("A"), make_state("B"), make_state("X")

    arr.set(0, A)
    arr.set(1, B)
    arr.set(2, A)
    save(arr, "03_set_overwrite", "0_A_B_A")

    arr.set(1, X) # this should fail because index 1 alr holds a qubit
    save(arr, "03_set_overwrite", "1_A_X_A")


# ═══════════════════════════════════════════════════════════════════════════
#  TEST 4 — Reverse (even length)
#  Expected: [A, B, C, D] → [D, C, B, A]
# ═══════════════════════════════════════════════════════════════════════════

def test_04_reverse_even():
    print("\n── Test 04: Reverse (even) ──")
    arr = QArray(num_qubits=4, num_clones=1)
    A, B, C, D = [make_state(l) for l in "ABCD"]

    arr.set(0, A)
    arr.set(1, B)
    arr.set(2, C)
    arr.set(3, D)
    save(arr, "04_reverse_even", "0_A_B_C_D")

    arr.reverse()
    save(arr, "04_reverse_even", "1_D_C_B_A")


# ═══════════════════════════════════════════════════════════════════════════
#  TEST 5 — Reverse (odd length)
#  Expected: [A, B, C] → [C, B, A]  (middle stays)
# ═══════════════════════════════════════════════════════════════════════════

def test_05_reverse_odd():
    print("\n── Test 05: Reverse (odd) ──")
    arr = QArray(num_qubits=3, num_clones=1)
    A, B, C = [make_state(l) for l in "ABC"]

    arr.set(0, A)
    arr.set(1, B)
    arr.set(2, C)
    save(arr, "05_reverse_odd", "0_A_B_C")

    arr.reverse()
    save(arr, "05_reverse_odd", "1_C_B_A")


# ═══════════════════════════════════════════════════════════════════════════
#  TEST 6 — Double reverse restores original
#  Expected: [A, B, C] → reverse → reverse → [A, B, C]
# ═══════════════════════════════════════════════════════════════════════════

def test_06_double_reverse():
    print("\n── Test 06: Double reverse ──")
    arr = QArray(num_qubits=3, num_clones=1)
    A, B, C = [make_state(l) for l in "ABC"]

    arr.set(0, A)
    arr.set(1, B)
    arr.set(2, C)
    save(arr, "06_double_reverse", "0_A_B_C")

    arr.reverse()
    save(arr, "06_double_reverse", "1_C_B_A")

    arr.reverse()
    save(arr, "06_double_reverse", "2_A_B_C_restored")


# ═══════════════════════════════════════════════════════════════════════════
#  TEST 7 — Remove first
#  Expected: [A, B, C] → remove(0) → [B, C]
# ═══════════════════════════════════════════════════════════════════════════

def test_07_remove_first():
    print("\n── Test 07: Remove first ──")
    arr = QArray(num_qubits=3, num_clones=1)
    A, B, C = [make_state(l) for l in "ABC"]

    arr.set(0, A)
    arr.set(1, B)
    arr.set(2, C)
    save(arr, "07_remove_first", "0_A_B_C")

    arr.remove(0)
    save(arr, "07_remove_first", "1_B_C")


# ═══════════════════════════════════════════════════════════════════════════
#  TEST 8 — Remove middle
#  Expected: [A, B, C] → remove(1) → [A, C]
# ═══════════════════════════════════════════════════════════════════════════

def test_08_remove_middle():
    print("\n── Test 08: Remove middle ──")
    arr = QArray(num_qubits=3, num_clones=1)
    A, B, C = [make_state(l) for l in "ABC"]

    arr.set(0, A)
    arr.set(1, B)
    arr.set(2, C)
    save(arr, "08_remove_middle", "0_A_B_C")

    arr.remove(1)
    save(arr, "08_remove_middle", "1_A_C")


# ═══════════════════════════════════════════════════════════════════════════
#  TEST 9 — Remove last
#  Expected: [A, B, C] → remove(2) → [A, B]
# ═══════════════════════════════════════════════════════════════════════════

def test_09_remove_last():
    print("\n── Test 09: Remove last ──")
    arr = QArray(num_qubits=3, num_clones=1)
    A, B, C = [make_state(l) for l in "ABC"]

    arr.set(0, A)
    arr.set(1, B)
    arr.set(2, C)
    save(arr, "09_remove_last", "0_A_B_C")

    arr.remove(2)
    save(arr, "09_remove_last", "1_A_B")


# ═══════════════════════════════════════════════════════════════════════════
#  TEST 10 — Insert at beginning
#  Expected: [B, C] → insert(0, A) → [A, B, C]
# ═══════════════════════════════════════════════════════════════════════════

def test_10_insert_beginning():
    print("\n── Test 10: Insert at beginning ──")
    arr = QArray(num_qubits=2, num_clones=1)
    A, B, C = [make_state(l) for l in "ABC"]

    arr.set(0, B)
    arr.set(1, C)
    save(arr, "10_insert_begin", "0_B_C")

    arr.insert(0, A) # this should fail because array is alr full
    save(arr, "10_insert_begin", "1_A_B_C")


# ═══════════════════════════════════════════════════════════════════════════
#  TEST 11 — Insert in middle
#  Expected: [A, C] → insert(1, B) → [A, B, C]
# ═══════════════════════════════════════════════════════════════════════════

def test_11_insert_middle():
    print("\n── Test 11: Insert in middle ──")
    arr = QArray(num_qubits=3, num_clones=1)
    A, B, C = [make_state(l) for l in "ABC"]

    arr.set(0, A)
    arr.set(1, C)
    save(arr, "11_insert_middle", "0_A_C")

    arr.insert(1, B)
    save(arr, "11_insert_middle", "1_A_B_C")


# ═══════════════════════════════════════════════════════════════════════════
#  TEST 12 — Get does not mutate
#  Expected: circuit before and after get(index) should retrive the state to qubit A{index}
# ═══════════════════════════════════════════════════════════════════════════

def test_12_get_no_mutate():
    print("\n── Test 12: Get does not mutate ──")
    arr = QArray(num_qubits=3, num_clones=1)
    A, B, C = [make_state(l) for l in "ABC"]

    arr.set(0, A)
    arr.set(1, B)
    arr.set(2, C)
    save(arr, "12_get_no_mutate", "0_before_get")

    _ = arr.get(1)
    save(arr, "12_get_no_mutate", "1_after_get")


# ═══════════════════════════════════════════════════════════════════════════
#  TEST 13 — Remove then insert restores original
#  Expected: [A, B, C] → remove(1) → [A, C] → insert(1, B) → [A, B, C]
# ═══════════════════════════════════════════════════════════════════════════

def test_13_remove_insert_roundtrip():
    print("\n── Test 13: Remove-insert roundtrip ──")
    arr = QArray(num_qubits=3, num_clones=1)
    A, B, C = [make_state(l) for l in "ABC"]

    arr.set(0, A)
    arr.set(1, B)
    arr.set(2, C)
    save(arr, "13_roundtrip", "0_A_B_C")

    arr.remove(1)
    save(arr, "13_roundtrip", "1_A_C")

    arr.insert(1, B)
    save(arr, "13_roundtrip", "2_A_B_C_restored")


# ═══════════════════════════════════════════════════════════════════════════
#  TEST 14 — Reverse then set
#  Expected: [A, B, C] → reverse → [C, B, A] → set(0, X) → [X, B, A]
# ═══════════════════════════════════════════════════════════════════════════

def test_14_reverse_then_set():
    print("\n── Test 14: Reverse then set ──")
    arr = QArray(num_qubits=3, num_clones=1)
    A, B, C, X = [make_state(l) for l in "ABCX"]

    arr.set(0, A)
    arr.set(1, B)
    arr.set(2, C)
    save(arr, "14_reverse_set", "0_A_B_C")

    arr.reverse()
    save(arr, "14_reverse_set", "1_C_B_A")

    arr.set(0, X) # this should fail because index 0 alr holds a qubit
    save(arr, "14_reverse_set", "2_X_B_A")


# ═══════════════════════════════════════════════════════════════════════════
#  TEST 15 — Full lifecycle (mirrors your example)
#  set → set → set → reverse → set → remove → get → insert
# ═══════════════════════════════════════════════════════════════════════════

def test_15_full_lifecycle():
    print("\n── Test 15: Full lifecycle ──")
    arr = QArray(num_qubits=5, num_clones=1)
    A, B = make_state("A"), make_state("B")

    save(arr, "15_lifecycle", "0_empty")

    arr.set(0, A)
    arr.set(1, A)
    arr.set(4, A)
    save(arr, "15_lifecycle", "1_set_0_1_4")

    arr.reverse()
    save(arr, "15_lifecycle", "2_reversed")

    arr.set(1, B)
    save(arr, "15_lifecycle", "3_set1_B")

    arr.remove(0)
    save(arr, "15_lifecycle", "4_remove0")

    _ = arr.get(2)
    save(arr, "15_lifecycle", "5_after_get2")

    arr.insert(1, B)
    save(arr, "15_lifecycle", "6_insert1_B")


# ═══════════════════════════════════════════════════════════════════════════
#  TEST 16 — Clones: same state in multiple clone slots
# ═══════════════════════════════════════════════════════════════════════════

def test_16_with_clones():
    print("\n── Test 16: With clones ──")
    arr = QArray(num_qubits=3, num_clones=2)
    A, B = make_state("A"), make_state("B")

    arr.set(0, A)
    arr.set(1, B)
    arr.set(2, A)
    save(arr, "16_clones", "0_A_B_A")

    arr.reverse()
    save(arr, "16_clones", "1_reversed")


# ═══════════════════════════════════════════════════════════════════════════
#  RUN ALL
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    tests = [
        test_01_set_single,
        test_02_set_all,
        test_03_set_overwrite,
        test_04_reverse_even,
        test_05_reverse_odd,
        test_06_double_reverse,
        test_07_remove_first,
        test_08_remove_middle,
        test_09_remove_last,
        test_10_insert_beginning,
        test_11_insert_middle,
        test_12_get_no_mutate,
        test_13_remove_insert_roundtrip,
        test_14_reverse_then_set,
        test_15_full_lifecycle,
        test_16_with_clones,
    ]

    os.makedirs(OUT_DIR, exist_ok=True)
    passed, failed = 0, 0

    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  ✗ FAILED: {e}")

    print(f"\n{'='*50}")
    print(f"  {passed} passed, {failed} failed out of {len(tests)} tests")
    print(f"  Images saved to: {OUT_DIR}/")
    print(f"{'='*50}")