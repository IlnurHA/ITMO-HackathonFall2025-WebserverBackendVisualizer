import file_example_imported

def local_function():
    pass

class MyClass:
    def __init__(self):
        file_example_imported.create_class()
    
    def outer_method(self):
        def inner_function():
            local_function()
        return inner_function

def global_function():
    class InnerClass:
        def inner_method(self):
            pass
    return InnerClass