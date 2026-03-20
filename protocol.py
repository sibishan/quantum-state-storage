# Being built by Joshua the Architect, master of all creation

from qiskit import QuantumRegister, QuantumCircuit, transpile
from qiskit.quantum_info import (
    random_statevector, Statevector,
    partial_trace, state_fidelity
)
from qiskit_aer import AerSimulator
import numpy as np


class Protocol:
    def __init__(self, n_qubits_to_clone: int, n_clones: int):
        self.n_qubits_to_clone = n_qubits_to_clone
        self.n_clones = n_clones
        self.sigma = [
            np.eye(2, dtype=complex),                           # σ_0 = I
            np.array([[0, 1],  [1, 0]],  dtype=complex),        # σ_1 = X
            np.array([[0, -1j],[1j, 0]], dtype=complex),        # σ_2 = Y
            np.array([[1, 0],  [0, -1]], dtype=complex),        # σ_3 = Z
        ]
        self.A = QuantumRegister(n_qubits_to_clone, 'A')
        self.S = QuantumRegister(n_qubits_to_clone * n_clones, 'S')
        self.N = QuantumRegister(n_qubits_to_clone * n_clones, 'N')
        self.qc = None

    # ------------------------------------------------------------------ #
    #  Public                                                              #
    # ------------------------------------------------------------------ #

    def build_circuit(self, psi=None, seed=42) -> QuantumCircuit:
        """Full encode → decrypt pipeline."""
        if psi is None:
            self.psi = random_statevector(2, seed=seed)
        else:
            self.psi = psi

        self.qc = QuantumCircuit(self.A, self.S, self.N)

        # Initialise A with |ψ⟩
        for i in range(self.n_qubits_to_clone):
            self.qc.initialize(self.psi, self.A[i])

        # Bell pairs  |ϕ⟩_{S_j N_j}  for every (i, j) group
        for i in range(self.n_qubits_to_clone):
            for j in range(self.n_clones):
                idx = i * self.n_clones + j
                self.qc.h(self.S[idx])
                self.qc.cx(self.S[idx], self.N[idx])

        # ---- Encryption  U_enc = exp(-iπ/4 σ1^A⊗σ1^S…) · exp(-iπ/4 σ3^A⊗σ3^S…) ----
        self.qc.barrier(label='encrypt')
        self._apply_zz_factor()   # exp(-iπ/4 σ3⊗σ3⊗…)  — ZZ interaction
        self._apply_xx_factor()   # exp(-iπ/4 σ1⊗σ1⊗…)  — XX interaction (H-sandwiched)

        # ---- Decryption  U_dec  (unitary block per qubit group) ----
        self.qc.barrier(label='decrypt')
        self._apply_decryption()
        return self.qc

    def verify_fidelity(self) -> float:
        qc_sv = self.qc.copy()
        qc_sv.save_statevector()

        sim = AerSimulator(method='statevector')
        result = sim.run(transpile(qc_sv, sim)).result()
        sv = Statevector(result.get_statevector())

        n_total = self.qc.num_qubits
        s0_index = self.n_qubits_to_clone

        trace_out = [q for q in range(n_total) if q != s0_index]
        rho_s0 = partial_trace(sv, trace_out)
        fidelity = state_fidelity(rho_s0, Statevector(self.psi))
        print(f"Fidelity of S[0] with |ψ⟩: {fidelity:.6f}")
        return fidelity

    # ------------------------------------------------------------------ #
    #  Encryption helpers                                                #
    # ------------------------------------------------------------------ #

    def _zz_cascade(self, i: int):
        base = i * self.n_clones

        # Forward: fan parity of A into the S chain
        self.qc.cx(self.A[i], self.S[base])
        for j in range(self.n_clones - 1):
            self.qc.cx(self.S[base + j], self.S[base + j + 1])

        # Rz(2t) with t = π/4  →  Rz(π/2) on the last S qubit
        self.qc.rz(np.pi / 2, self.S[base + self.n_clones - 1])

        # Backward: uncompute the parity ladder
        for j in reversed(range(self.n_clones - 1)):
            self.qc.cx(self.S[base + j], self.S[base + j + 1])
        self.qc.cx(self.A[i], self.S[base])

    def _apply_zz_factor(self):
        for i in range(self.n_qubits_to_clone):
            self._zz_cascade(i)

    def _apply_xx_factor(self):
        for i in range(self.n_qubits_to_clone):
            base = i * self.n_clones

            # H on A and all S in this group
            self.qc.h(self.A[i])
            for j in range(self.n_clones):
                self.qc.h(self.S[base + j])

            self._zz_cascade(i)

            # H again to return to Z basis
            self.qc.h(self.A[i])
            for j in range(self.n_clones):
                self.qc.h(self.S[base + j])

    # ------------------------------------------------------------------ #
    #  Decryption  (Eq. 5 of paper)                                       #
    # ------------------------------------------------------------------ #

    def _build_decryption_unitary(self, n: int) -> np.ndarray:
        alpha = np.array([1, 1j, -(1j) ** (n + 1), 1j], dtype=complex)
        phi_vec = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)

        dim = 2 ** (n + 1)
        U_dec = np.zeros((dim, dim), dtype=complex)

        for mu in range(4):
            # |ϕ_μ⟩ = (σ_μ ⊗ I)|ϕ⟩
            phi_mu = np.kron(self.sigma[mu], np.eye(2)) @ phi_vec
            proj_mu = np.outer(phi_mu, phi_mu.conj())

            # ⊗_{j=2}^{n} σ_μ^T  (scalar identity if n=1)
            if n > 1:
                noise_op = self.sigma[mu].T.copy()
                for _ in range(n - 2):
                    noise_op = np.kron(noise_op, self.sigma[mu].T)
            else:
                noise_op = np.array([[1]], dtype=complex)

            U_dec += alpha[mu] * np.kron(proj_mu, noise_op)

        return U_dec

    def _apply_decryption(self):
        for i in range(self.n_qubits_to_clone):
            base = i * self.n_clones
            U_dec = self._build_decryption_unitary(self.n_clones)

            if self.n_clones > 1:
                dec_qubits = [self.N[base + k] for k in range(self.n_clones - 1, -1, -1)] + [self.S[base]]
            else:
                dec_qubits = [self.N[base], self.S[base]]

            self.qc.unitary(U_dec, dec_qubits, label=f'U_dec({self.n_clones})')