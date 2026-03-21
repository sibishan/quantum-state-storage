from protocol import Protocol

class QStack:
    def __init__(self, num_qubits=0, num_clones=0):
        self.num_qubits = num_qubits
        self.num_clones = num_clones
        self.capacity = 0
        self.protocol = Protocol(self.num_qubits, self.num_clones)
        self._get_qc = False
    
    def draw(self):
        return self.protocol.qc.draw(output='mpl', fold=-1)

    def push(self, qc=None):
        if self._get_qc:
            raise RuntimeError("Cannot push qubits after finalising the protocol circuit")
        if qc is None:
            raise ValueError("Input circuit cannot be None")
        if qc.num_qubits != 1:
            raise ValueError("Input must be a single-qubit circuit")
        if self.capacity >= (self.num_qubits):
            raise OverflowError("QStack Overflow")
        
        self.protocol.store_qubit(qc, self.capacity)
        self.capacity += 1

    def pop(self, c_index=0):
        if self._get_qc:
            raise RuntimeError("Cannot pop qubits after finalising the protocol circuit")
        if self.isEmpty():
            raise IndexError("QStack is empty")
        if c_index >= self.num_clones or c_index < 0:
            raise ValueError("Invalid clone index")
        
        temp = self.capacity - 1
        self.protocol.retrieve_qubit(temp)

    def isEmpty(self):
        return self.capacity == 0
    
    def generate_circuit(self):
        self._get_qc = True
        return self.protocol.get_qc()

    def size(self):
        return len(self.capacity)
