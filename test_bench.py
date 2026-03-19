from protocol import Protocol

N = 3
S = 2

protocol = Protocol(N, S)
qc = protocol.build_encoder()
print(qc.draw())
print("\n\n")

