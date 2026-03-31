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
        self._tail = 0
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
        if self.lookup[index]['status'] == "set" or self.lookup[index]['status'] == "get":
            raise IndexError(f"Qubit A_{index} already in use")
        
        self.protocol.store_qubit(qc, index)
        self.lookup[index]['status'] = "set"
        self.size += 1
        self._tail = max(self._tail, index + 1)

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
        if self.size >= self.num_qubits:
            raise IndexError("Array is full")
        
        for i in range(index, self._tail):
            if self.lookup[i]['status'] == "set":
                 self.protocol.retrieve_qubit(i, 0)
        for i in range(self._tail - 1, index - 1, -1):
            self.protocol.swap_a(i, i + 1)
            temp = self.lookup[i]['status']
            self.lookup[i]['status'] = self.lookup[i + 1]['status']
            self.lookup[i + 1]['status'] = temp
        for i in range(index + 1, self._tail + 1):
            if self.lookup[i]['status'] == "set":
                self.protocol.store_qubit(qc=None, index=i)
        
        self.protocol.store_qubit(qc, index)
        self.lookup[index]['status'] = "set"
        self.size += 1
        self._tail += 1
        
    def append(self, qc=None):
        if self._get_qc:
            raise RuntimeError("Cannot append qubits after finalising the protocol circuit")
        if qc is None:
            raise ValueError("qc cannot be Null")
        if qc.num_qubits != 1:
            raise ValueError("Input must be a single-qubit circuit")
        if self._tail >= self.num_qubits:
            raise IndexError("Array is full")
        
        self.protocol.store_qubit(qc, self._tail)
        self.lookup[self._tail]['status'] = "set"
        self.size += 1
        self._tail += 1

    def remove(self, index=None):
        if self._get_qc:
            raise RuntimeError("Cannot remove qubits after finalising the protocol circuit")
        if index is None:
            raise ValueError("index cannot be Null")
        if index >= self._tail or index < 0:
            raise IndexError("index out of bounds")
        
        self.protocol.uncompute_a(index)
        self.lookup[index]['status'] = ""
        for i in range(index + 1, self._tail):
            if self.lookup[i]['status'] == "set":
                self.protocol.retrieve_qubit(i, 0)
        for i in range(index, self._tail - 1):
            self.protocol.swap_a(i, i + 1)
            temp = self.lookup[i]['status']
            self.lookup[i]['status'] = self.lookup[i + 1]['status']
            self.lookup[i + 1]['status'] = temp
        for i in range(index, self._tail - 1):
            if self.lookup[i]['status'] == "set":
                self.protocol.store_qubit(qc=None, index=i)
        
        self.size -= 1
        self._tail -= 1
        
    def reverse(self):
        if self._get_qc:
            raise RuntimeError("Cannot reverse qubits after finalising the protocol circuit")
        
        for i in range(self._tail):
            if self.lookup[i]['status'] == "set":
                self.protocol.retrieve_qubit(i, 0)
        for i in range(self._tail // 2):
            j = self._tail - 1 - i
            self.protocol.swap_a(i, j)
            temp = self.lookup[i]['status']
            self.lookup[i]['status'] = self.lookup[j]['status']
            self.lookup[j]['status'] = temp
        for i in range(self._tail):
            if self.lookup[i]['status'] == "set":
                self.protocol.store_qubit(qc=None, index=i)

    def is_empty(self):
        return self.size == 0
    
    def is_full(self):
        return self._tail >= self.num_qubits

    def clear(self):
        self.size = 0
        self._tail = 0
        self.protocol = Protocol(self.num_qubits, self.num_clones)
        self._get_qc = False
        for i in range(self.num_qubits):
            self.lookup[i] = {
                'status': ''
            }
    
    def __repr__(self):
        header = f"QArray(size={self.size}, capacity={self.num_qubits})\n"
        if self.num_qubits == 0:
            return header + "┌──┐\n│  │\n└──┘  (empty)"

        top    = "┌"
        middle = "│"
        bottom = "└"
        labels = " "

        for i in range(self.num_qubits):
            width = max(len(f"A_{i}"), 4)
            if self.lookup[i]['status'] == "set":
                cell = f" A_{i} ".center(width + 2)
            elif self.lookup[i]['status'] == "get":
                label = f"A_{i}"
                cell = f"░{label}░".center(width + 2, '░')
            else:
                cell = " · ".center(width + 2)

            top    += "─" * (width + 2) + "┬"
            middle += cell + "│"
            bottom += "─" * (width + 2) + "┴"
            labels += str(i).center(width + 2) + " "

        top    = top[:-1]    + "┐"
        bottom = bottom[:-1] + "┘"

        return f"{header}{top}\n{middle}\n{bottom}\n{labels}"