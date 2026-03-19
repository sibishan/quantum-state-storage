#Being built by Joshua the Architect, master of all creation

from qiskit import QuantumRegister, QuantumCircuit
from qiskit.quantum_info import (
    random_statevector, Statevector,
    partial_trace, state_fidelity
)
import numpy as np

class Protocol:
    def __init__(self, n_qubits_to_clone:int, n_clones:int):
        self.n_qubits_to_clone = n_qubits_to_clone
        self.n_clones = n_clones
        self.noise_qubits = n_clones
        self.sigma = [
            np.eye(2, dtype=complex),                          # σ_0 = I
            np.array([[0, 1], [1, 0]], dtype=complex),         # σ_1 = X
            np.array([[0, -1j], [1j, 0]], dtype=complex),      # σ_2 = Y
            np.array([[1, 0], [0, -1]], dtype=complex)          # σ_3 = Z
        ]
    
    def build_encoder(self, psi=None, seed=42) -> QuantumCircuit:
        if psi is None:
            psi = random_statevector(2, seed=seed)

        A = QuantumRegister(self.n_qubits_to_clone, 'A')    #Qubit to clone
        S = []  # Signal Qubit
        N = []  # Noise Qubit

        for i in range(self.n_qubits_to_clone):
            for j in range(self.n_clones):
                S.append(QuantumRegister(1, f'S{i}_{j}'))
                N.append(QuantumRegister(1, f'N{i}_{j}'))

        qc = QuantumCircuit(A, *S, *N)

        # === Initialize A with random state ===
        for i in range(self.n_qubits_to_clone):
            qc.initialize(psi, A[i])

        # === Create n Bell pairs (Si, Ni) ===
        for i in range(self.n_qubits_to_clone):
            for j in range(self.n_clones):
                idx = i * self.n_clones + j
                qc.h(S[idx])
                qc.cx(S[idx], N[idx])

        qc.barrier(label='encrypt')

        for i in range(self.n_qubits_to_clone):
            qc.cx(A[i], S[i])

        """for i in range(self.n_clones - 1):
            qc.cx(S[i], S[i + 1])"""

        """
        # ZZ part: exp(-i π/4  Z_A ⊗ Z_{S0} ⊗ ... ⊗ Z_{Sn-1})
        # CNOT ladder down to accumulate parity
        qc.cx(A[0], S[0])
        for i in range(n - 1):
            qc.cx(S[i], S[i + 1])
        # Phase rotation on last signal qubit
        qc.rz(np.pi / 2, S[n - 1])
        # CNOT ladder back up to uncompute
        for i in range(n - 2, -1, -1):
            qc.cx(S[i], S[i + 1])
        qc.cx(A[0], S[0])
        """
        return qc