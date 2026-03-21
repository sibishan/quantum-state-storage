from protocol import Protocol

class QArray:
    def __init__(self, num_qubits=0, num_clones=0):
        self.num_qubits = num_qubits
        self.num_clones = num_clones
        self.lookup = {}
        for i in range(self.num_qubits):
            self.lookup[i] = {
                'status': ''
            }
        self.size = 0
        self.protocol = Protocol(self.num_qubits, self.num_clones)
        self._get_qc = False

    def get(self, a_index=None, c_index=0):
        if self._get_qc:
            raise RuntimeError("Cannot get qubits after finalising the protocol circuit")
        if a_index is None:
            raise ValueError("Qubit A index and Clone index cannot be Null")
        if a_index >= self.num_qubits or a_index < 0:
            raise IndexError("a_index out of bounds")
        if c_index >= self.num_clones or c_index < 0:
            raise IndexError("c_index out of bounds")
        
        self.protocol.retrieve_qubit(a_index, c_index)
        self.lookup[a_index]['status'] = "get"

    def set(self, index=None, qc=None):
        if self._get_qc:
            raise RuntimeError("Cannot set qubits after finalising the protocol circuit")
        if index is None or qc is None:
            raise ValueError("index and qc cannot be Null")
        if qc.num_qubits != 1:
            raise ValueError("Input must be a single-qubit circuit")
        if index >= self.num_qubits or index < 0:
            raise IndexError("index out of bounds")
        
        self.protocol.store_qubit(qc, index)
        self.lookup[index]['status'] = "set"
        self.size += 1

    def draw(self):
        return self.protocol.qc.draw(output='mpl', fold=-1)
    
    def generate_circuit(self):
        self._get_qc = True
        return self.protocol.qc

    def insert(self, index, qc=None):
        if self._get_qc:
            raise RuntimeError("Cannot insert qubits after finalising the protocol circuit")
        if index is None or qc is None:
            raise ValueError("index and qc cannot be Null")
        if qc.num_qubits != 1:
            raise ValueError("Input must be a single-qubit circuit")
        if index >= self.num_qubits or index < 0:
            raise IndexError("index out of bounds")
        
        for i in range(index, self.size):
            if self.lookup[i]['status'] == "set":
                 self.protocol.retrieve_qubit(i, 0)
        for i in range(self.size-1, index-1, -1):
            self.protocol.swap_a(i, i+1)
            temp = self.lookup[i]['status']
            self.lookup[i]['status'] = self.lookup[i-1]['status']
            self.lookup[i-1]['status'] = temp
        for i in range(index+1, self.size+1):
            if self.lookup[i]['status'] == "set":
                self.protocol.store_qubit(qc=None, index=i)
        
        self.protocol.store_qubit(qc, index)
        self.size += 1
        

    # def append(self, value):
    #     if self.size < self.capacity:
    #         self.elements.append(value)
    #         self.size += 1

    # def remove(self, value):
    #     if value in self.elements:
    #         self.elements.remove(value)
    #         self.size -= 1
    #     else:
    #         raise ValueError("value not in array")

    # def reverse(self):
    #     self.elements.reverse()

    # def clear(self):
    #     self.elements = []
    #     self.size = 0

    # def is_empty(self):
    #     return self.size == 0
    
    # def is_full(self):
    #     return self.size >= self.capacity