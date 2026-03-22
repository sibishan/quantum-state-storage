from qiskit import QuantumRegister, QuantumCircuit

import numpy as np


class Protocol:
    def __init__(self, num_qubits=0, num_clones=0):
        self.num_qubits = num_qubits
        self.num_clones = num_clones
        
        self.A = {}
        for i in range(self.num_qubits):
            self.A[i] = {
                'reg': QuantumRegister(1, name=f'A{i}'),
                'in_use': False
            }

        self.S = {}
        self.N = {}
        for i in range(self.num_qubits):
            for j in range(self.num_clones):
                self.S[i, j] = {
                    'reg': QuantumRegister(1, name=f'S_{i}_{j}'),
                    'in_use': False
                }
                self.N[i, j] = {
                    'reg': QuantumRegister(1, name=f'N_{i}_{j}'),
                    'in_use': False
                }

        self.qc = self._init_circuit()

    def _init_circuit(self):
        qc = QuantumCircuit(
            *[self.A[i]['reg'] for i in self.A],
            *[self.S[k]['reg'] for k in self.S],
            *[self.N[k]['reg'] for k in self.N]
        )
        for i in range(self.num_qubits):
            for j in range(self.num_clones):
                qc.h(self._s(i, j))
                qc.cx(self._s(i, j), self._n(i, j))
        qc.barrier()
        return qc

    def store_qubit(self, qc, index):
        if index >= self.num_qubits or index < 0:
            raise IndexError(f"{index} of Qubit A is out of bounds")

        flag = False
        for i in range(self.num_clones):
            if self._s_in_use(index, i) or self._n_in_use(index, i):
                flag = True
                break
        if flag and self._a_in_use(index):
                raise IndexError(f"Qubit A_{index} already in use with clones")

        if qc is not None:
            self.qc = self.qc.compose(qc, qubits=[self._a(index)])
        self._a_in_use(index, True)

        # Encrypted Cloning  U_enc = exp(-iπ/4 σ1^A⊗σ1^S…) · exp(-iπ/4 σ3^A⊗σ3^S…)
        self._apply_zz_factor(index)    # exp(-iπ/4 σ3⊗σ3⊗…)  — ZZ interaction
        self._apply_xx_factor(index)    # exp(-iπ/4 σ1⊗σ1⊗…)  — XX interaction (H-sandwiched)
        self.qc.barrier()

        for i in range(self.num_clones):
            self._s_in_use(index, i, True)
            self._n_in_use(index, i, True)

    def retrieve_qubit(self, a_index, c_index):
        n = self.num_clones

        if not self._a_in_use(a_index):
            raise ValueError(f"Qubit A_{a_index} has nothing stored")
        if c_index < 0 or c_index >= n:
            raise IndexError(f"Clone index {c_index} out of bounds")
        if not self._s_in_use(a_index, c_index) or not self._n_in_use(a_index, c_index):
            raise ValueError(f"Clone already decrypted or never stored")
        
        sigma = [
            np.eye(2, dtype=complex),                           # σ_0 = I
            np.array([[0, 1],  [1, 0]],  dtype=complex),        # σ_1 = X
            np.array([[0, -1j],[1j, 0]], dtype=complex),        # σ_2 = Y
            np.array([[1, 0],  [0, -1]], dtype=complex),        # σ_3 = Z
        ]

        # α_0 = 1, α_1 = α_3 = i, α_2 = -i^{n+1}
        alpha = [1, 1j, -(1j) ** (n + 1), 1j]

        # Bell states |ϕ_μ⟩ = (σ_μ ⊗ I)|ϕ_0⟩  as 4-vectors
        phi_0 = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
        bell = [np.kron(sigma[mu], np.eye(2)) @ phi_0 for mu in range(4)]

        # U_dec = Σ_μ α_μ |ϕ_μ⟩⟨ϕ_μ|_{Sc,Nc} ⊗ (⊗_{j≠c} σ_μ^T_{Nj})
        total_dim = 2 ** (n + 1)          # Sc + n noise qubits
        U_dec = np.zeros((total_dim, total_dim), dtype=complex)

        for mu in range(4):
            proj = np.outer(bell[mu], bell[mu].conj())       # 4×4

            noise_op = np.array([[1.0 + 0j]])                # scalar seed
            for _ in range(n - 1):                           # (n-1) other Nj
                noise_op = np.kron(noise_op, sigma[mu].T)

            U_dec += alpha[mu] * np.kron(proj, noise_op)

        # Qubit ordering: matrix built as Sc ⊗ Nc ⊗ N_other_0 ⊗ ... (MSB first)
        # Qiskit unitary() expects [LSB, ..., MSB], so reverse the list
        other_n = [self._n(a_index, j) for j in range(n) if j != c_index]
        qubits_msb_first = [self._s(a_index, c_index),
                            self._n(a_index, c_index)] + other_n
        
        self.qc.unitary(U_dec, qubits_msb_first[::-1],
                        label=f'U_dec({a_index},{c_index})')
        self.qc.swap(self._a(a_index), self._s(a_index, c_index))

        for i in range(n):
            self.qc.reset(self._n(a_index, i))
            self.qc.reset(self._s(a_index, i))
            self._s_in_use(a_index, i, False)
            self._n_in_use(a_index, i, False)
        for i in range(self.num_clones):
                self.qc.h(self._s(a_index, i))
                self.qc.cx(self._s(a_index, i), self._n(a_index, i))
        
        self.qc.barrier()
    
    def swap_a(self, p, q):
        if p >= self.num_qubits or p < 0 or q >= self.num_qubits or q < 0:
            raise IndexError("index out of bounds")

        self.qc.swap(self._a(p), self._a(q))
        temp = self._a_in_use(p)
        self._a_in_use(p, self._a_in_use(q))
        self._a_in_use(q, temp)
    
    def uncompute_a(self, index):
        if not self._a_in_use(index):
            raise ValueError(f"Qubit A_{index} has nothing stored")

        self.qc.reset(self._a(index))
        self._a_in_use(index, False)
        for i in range(self.num_clones):
            if self._s_in_use(index, i) or self._n_in_use(index, i):
                self.qc.reset(self._s(index, i))
                self.qc.reset(self._n(index, i))
                self._s_in_use(index, i, False)
                self._n_in_use(index, i, False)
        for i in range(self.num_clones):
                self.qc.h(self._s(index, i))
                self.qc.cx(self._s(index, i), self._n(index, i))

    def get_qc(self):
        return self.qc

    def _apply_zz_factor(self, index):
        # Forward: fan parity of A into the S chain
        self.qc.cx(self._a(index), self._s(index, 0))
        for i in range(self.num_clones - 1):
            self.qc.cx(self._s(index, i), self._s(index, i + 1))

        # Rz(2t) with t = π/4  →  Rz(π/2) on the last S qubit
        self.qc.rz(np.pi / 2, self._s(index, self.num_clones - 1))

        # Backward: uncompute the parity chain
        for i in range(self.num_clones - 1, 0, -1):
            self.qc.cx(self._s(index, i - 1), self._s(index, i))
        self.qc.cx(self._a(index), self._s(index, 0))

    def _apply_xx_factor(self, index):
        # H on A and all S in this group
        self.qc.h(self._a(index))
        for i in range(self.num_clones):
            self.qc.h(self._s(index, i))

        self._apply_zz_factor(index)

        # H again to return to Z basis
        self.qc.h(self._a(index))
        for i in range(self.num_clones):
            self.qc.h(self._s(index, i))

    def _a(self, i):
        return self.A[i]['reg'][0]

    def _s(self, i, j):
        return self.S[i, j]['reg'][0]

    def _n(self, i, j):
        return self.N[i, j]['reg'][0]
    
    def _a_in_use(self, i, val=None):
        if val is not None:
            self.A[i]['in_use'] = val
        return self.A[i]['in_use']

    def _s_in_use(self, i, j, val=None):
        if val is not None:
            self.S[i, j]['in_use'] = val
        return self.S[i, j]['in_use']

    def _n_in_use(self, i, j, val=None):
        if val is not None:
            self.N[i, j]['in_use'] = val
        return self.N[i, j]['in_use']
    