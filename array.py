# callum will work on this array data structure class
class Array:
    def __init__(self, elements, capacity, dtype):
        self.elements = elements        # The actual stored values
        self.size = len(self.elements)                # Num of elements in the array
        self.capacity = max(capacity, self.size)        # Total allocated space
        self.dtype = dtype              # Element data type

        self.address = 0x1ffa5a
        self.stride = 4

    # Python will print this when we request to see our data in CLI
    def __repr__(self):
        return f"Array({self.elements}, size={self.size}, capacity={self.capacity}, data={self.dtype})"

    def get(self, index):
        if 0 <= index < self.size:
            return self.elements[index]
        raise IndexError("index out of range")

    def set(self, index, value):
        if 0 <= index < self.size:
            self.elements[index] = value
        raise IndexError("index out of range")

    def insert(self, index, value):
        self.elements.insert(index, value)
        self.size += 1

    def append(self, value):
        if self.size < self.capacity:
            self.elements.append(value)
            self.size += 1

    def remove(self, value):
        if value in self.elements:
            self.elements.remove(value)
            self.size -= 1
        else:
            raise ValueError("value not in array")

    def search(self, value):
        return self.elements.index(value)

    def sort(self):
        try:
            return self.elements.sort()
        except ValueError:
            return -1

    def reverse(self):
        self.elements.reverse()

    def slice(self, start, end):
        return self.elements.slice[start:end]

    def clear(self):
        self.elements = []
        self.size = 0

    def isEmpty(self):
        return self.size == 0

    def contains(self, value):
        return value in self.elements
