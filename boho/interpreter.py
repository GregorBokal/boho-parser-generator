from .objects import Tree, Token


class Interpreter:

    def __call__(self, node: Tree | Token):
        if hasattr(self, node.name):
            return getattr(self, node.name)(node)
        elif isinstance(node, Token):
            return node.value
        else:
            return [self(p) for p in node.children]
