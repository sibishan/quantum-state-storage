from qstack import QStack
from qarray import QArray

from qiskit import QuantumCircuit
from qiskit.quantum_info import random_statevector

A = 5
S = 2

# stack = QStack(num_qubits=A, num_clones=S)

# a = QuantumCircuit(1)
# psi = random_statevector(2)
# a.initialize(psi, 0)

# print(stack)
# stack.push(a)
# print(stack)
# stack.pop()
# print(stack)
# # qc = stack.generate_circuit()
# stack.push(a)
# stack.push(a)
# print(stack)
# stack.pop()
# print(stack)
# stack.pop()
# print(stack)


# img = stack.draw()
# img.savefig('misc/stack-circuit.png', bbox_inches='tight')

array = QArray(num_qubits=A, num_clones=S)

a = QuantumCircuit(1)
psi = random_statevector(2)
a.initialize(psi, 0)

print(array)
array.set(0, a)
array.set(1, a)
array.set(4, a)
print(array)
array.reverse()
print(array)
array.set(1, a)
print(array)
array.remove(0)
print(array)
array.get(2)
print(array)
array.insert(1, a)
print(array)


# qc = array.generate_circuit()
# array.set(1, a)

img = array.draw()
img.savefig('misc/array-circuit.png', bbox_inches='tight')