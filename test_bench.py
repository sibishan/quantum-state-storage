from protocol import Protocol
from array import Array
from stack import Stack

A = 2
S = 3

protocol = Protocol(A, S)
qc = protocol.build_circuit()
my_array = Array([1, 2, 3, 4], capacity=5, dtype=int)

qc.draw('mpl', filename='misc/circuit.png')
print(qc.depth())
print(dict(qc.count_ops()))
protocol.verify_fidelity()

print(my_array.isEmpty())
my_array.append(5)
print(my_array)

