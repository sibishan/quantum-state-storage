from protocol import Protocol

N = 1
S = 3

protocol = Protocol(N, S)
qc = protocol.build_circuit()
qc.draw('mpl', filename='misc/circuit.png')
print(qc.draw(fold=-1))
print("\n\n")

