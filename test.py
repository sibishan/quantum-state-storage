from stack import QStack

from qiskit import QuantumCircuit
from qiskit.quantum_info import (
    random_statevector, Statevector,
    partial_trace, state_fidelity
)

A = 2
S = 3

stack = QStack(num_qubits=A, num_clones=S)

a = QuantumCircuit(1)
psi = random_statevector(2)
a.initialize(psi, 0)

print(stack.size())
stack.push(a)
print(stack.size())
stack.pop()
print(stack.size())
# qc = stack.generate_circuit()
stack.push(a)
print(stack.size())

img = stack.draw()
img.savefig('misc/circuit.png', bbox_inches='tight')

