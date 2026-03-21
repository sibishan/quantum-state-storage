from qstack import QStack
from qarray import QArray

from qiskit import QuantumCircuit
from qiskit.quantum_info import (
    random_statevector, Statevector,
    partial_trace, state_fidelity
)

A = 3
S = 3

stack = QStack(num_qubits=A, num_clones=S)

a = QuantumCircuit(1)
psi = random_statevector(2)
a.initialize(psi, 0)

stack.push(a)
stack.pop()
# qc = stack.generate_circuit()
stack.push(a)
stack.push(a)
stack.pop()
stack.pop()



img = stack.draw()
img.savefig('misc/circuit.png', bbox_inches='tight')

# array = QArray(num_qubits=A, num_clones=S)

# a = QuantumCircuit(1)
# psi = random_statevector(2)
# a.initialize(psi, 0)

# array.set(0, a)
# array.set(0, a)
# array.get(0)
# array.get(1, 2)

# qc = array.generate_circuit()
# array.set(1, a)

# img = array.draw()
# img.savefig('misc/circuit.png', bbox_inches='tight')