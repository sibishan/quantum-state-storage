class Stack:
    def __init__(self, items, capacity):
        self.items = items
        self.capacity = capacity
        self.top = -1

    def push(self, item):
        if len(self.items) >= self.capacity:
            raise OverflowError("Stack Overflow")
        self.items.append(item)
        self.top += 1

    def pop(self):
        if self.isEmpty():
            raise IndexError("Stack Underflow")
        self.top -= 1
        return self.items.pop()

    def isEmpty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)
