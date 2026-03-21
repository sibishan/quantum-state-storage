from protocol import Protocol

class QStack:
    def __init__(self, num_qubits=0, num_clones=0):
        self.num_qubits = num_qubits
        self.num_clones = num_clones
        self.lookup = {}
        for i in range(self.num_qubits):
            self.lookup[i] = {
                'flag': False,
            }
        self.size = 0
        self.protocol = Protocol(self.num_qubits, self.num_clones)
        self._get_qc = False

    def push(self, qc=None):
        if self._get_qc:
            raise RuntimeError("Cannot push qubits after finalising the protocol circuit")
        if qc is None:
            raise ValueError("Input circuit cannot be None")
        if qc.num_qubits != 1:
            raise ValueError("Input must be a single-qubit circuit")
        if self.size >= (self.num_qubits):
            raise OverflowError("QStack Overflow")
        
        self.protocol.store_qubit(qc, self.size)
        self.lookup[self.size]['flag'] = True
        self.size += 1

    def pop(self, c_index=0):
        if self._get_qc:
            raise RuntimeError("Cannot pop qubits after finalising the protocol circuit")
        if self.is_empty():
            raise IndexError("QStack is empty")
        if c_index >= self.num_clones or c_index < 0:
            raise ValueError("c_index out of bounds")
        
        idx = 0
        for i in range(self.size-1, -1, -1):
            if self.lookup[i]['flag']:
                idx = i
                break
        
        self.protocol.retrieve_qubit(idx, c_index)
        self.lookup[idx]['flag'] = False
    
    def draw(self):
        return self.protocol.qc.draw(output='mpl', fold=-1)
    
    def generate_circuit(self):
        self._get_qc = True
        return self.protocol.get_qc()

    def is_empty(self):
        return self.size == 0
    
    def is_full(self):
        return self.size == self.num_qubits
    
    def get_size(self):
        return self.size
    
    def clear(self):
        self.size = 0
        self.protocol = Protocol(self.num_qubits, self.num_clones)
        self._get_qc = False
