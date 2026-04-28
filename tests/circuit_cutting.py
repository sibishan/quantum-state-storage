from utils import cut_circuit
from qarray import QArray

from qiskit import QuantumCircuit
from qiskit.quantum_info import random_statevector

import os
import matplotlib.pyplot as plt

OUT_DIR = "tests/out"


def save(circuit, test_name, step):
    path = os.path.join(OUT_DIR, test_name)
    os.makedirs(path, exist_ok=True)

    fig = circuit.draw(output="mpl", fold=-1)
    fig.savefig(os.path.join(path, f"{step}.png"), bbox_inches="tight")
    plt.close(fig)
    print(f"  saved: {path}/{step}.png")

a = QuantumCircuit(1)
psi = random_statevector(2)
a.initialize(psi, 0)

array = QArray(1, 2)
array.set(0, a)
array.get(0)
array_qc = array.generate_circuit()

save(array_qc, "circuit_cutting", "array")

store, retrieve = cut_circuit(array_qc, idx=1)

save(store, "circuit_cutting", "store")
save(retrieve, "circuit_cutting", "retrieve")
