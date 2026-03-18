#Being built by Joshua the Architect, master of all creation

from qiskit import QuantumRegister, QuantumCircuit
import numpy as np

class Protocol:
    def __init__(self, n_qubits_to_clone, n_clones):
        self.n_qubits_to_clone = n_qubits_to_clone
        self.n_clones = n_clones
        self.noise_qubits = n_clones

    def create_circuit(self):
        A = QuantumRegister(self.n_qubits_to_clone, 'A')
        S = []
        N = []

        for i in range(self.n_qubits_to_clone):
            for j in range(self.n_clones):
                S.append(QuantumRegister(1, f'S{i}_{j}'))
                N.append(QuantumRegister(1, f'N{i}_{j}'))

        qc = QuantumCircuit(A, *S, *N)
        return qc
        