class A:
    def __init__(self, a):
        self.a = a


class B:
    def __init__(self, a: A):
        self.a = a
    def set_a(self, b):
        self.a.a = b


