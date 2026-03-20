# michael will work on this stack data structure class
class Stack:
    def __init__(self, items, capacity):
        self.items = items
        self.capacity = capacity
        self.top = -1

    def __repr__(self):
        return f"Stack({self.items}, capacity={self.capacity})"

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

    def peek(self):
        if self.isEmpty():
            return None
        return self.items[-1]

    def isEmpty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)

my_stack = Stack(items=[1,2,3,4,5,6,7,8,9], capacity=10)
my_stack.push(5)
my_stack.push(6)
my_stack.push(7)
print(my_stack.pop())
print(my_stack.peek())
my_stack.size()