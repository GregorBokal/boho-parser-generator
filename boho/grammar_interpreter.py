from .grammars import boho_grammar
from .lexer import Lexer
from .parser import Parser
from .interpreter import Interpreter
from .objects import (
    TerminalList,
    TerminalDescription as Terminals,
    Grammar,
    Tree, unnamed
)
from typing import Dict, List

alphabet = 'abcdefghijklmnopqrstuvwxyz'


class GrammarInterpreter(Interpreter):

    def __init__(self):
        self.terminal_list: TerminalList = []
        self.terminals: Terminals = {}
        self.grammar: Grammar = {}
        self.ignore_dict: Dict[str, List[str]] = {}
        self.current_mode: str = ''
        self.i: int = 0

    def start(self, tree):
        self.terminal_list = []
        self.terminals = {}
        self.grammar = {}
        self.ignore_dict = {'': []}
        self.current_mode = ''
        self.i = 0

        for statement in tree:
            self(statement)

        if self.terminals:
            for mode in self.terminals:
                for terminal in self.terminal_list:
                    self.terminals[mode].append(terminal)
        else:
            self.terminals[''] = self.terminal_list

        return self.terminals, self.grammar, self.ignore_dict

    def terminal(self, tree):
        desc = self(tree[1])
        action = [self(tree[0])]
        if len(tree) > 2:
            b = self(tree[2])
            action += b
        self.add_terminal(desc, action)

    def add_terminal(self, *new):
        if self.current_mode:
            if new not in self.terminals[self.current_mode]:
                self.terminals[self.current_mode].append(new)
        elif new not in self.terminal_list:
            self.terminal_list.append(new)

    def description(self, token):
        return token.value

    def operations(self, tree):
        list = []
        for token in tree:
            list += self(token)
        return list

    @staticmethod
    def push_mode(token):
        return [token.value[1:]]

    @staticmethod
    def pop_mode(token):
        if token.children:
            return [int(token.value)]
        else:
            return [1]

    @staticmethod
    def reset_mode(*args):
        return [0]

    @staticmethod
    def change_mode(token):
        return [1, token.value]

    def nonterminal(self, tree):
        name = self(tree[0])
        options = self(tree[1])
        self.grammar[name] = options

    def option(self, tree):
        units = self(tree[0])
        if len(tree) > 1:
            alias = self(tree[1])
            self.grammar[alias] = [tuple(units)]
            return (alias,)
        return tuple(units)

    def unit(self, tree):
        atom = self(tree[0])
        if atom[0] in unnamed:
            self.add_terminal(atom, [atom])
        if len(tree) > 1:
            quantifier = tree[1][0].value
            name = self.random_name()
            match quantifier:
                case '?':
                    self.grammar[name] = [(atom,), ()]
                case '*':
                    self.grammar[name] = [(name, atom), ()]
                case '+':
                    self.grammar[name] = [(name, atom), (atom,)]
            return name
        return atom

    def atom(self, tree):
        desc = self(tree[0])
        if isinstance(desc, str):
            return desc
        name = self.random_name()
        self.grammar[name] = desc
        return name

    def random_name(self):
        while (name := self.next_name()) in self.grammar:
            self.i += 1
        return name

    def next_name(self):
        result = []
        n = self.i
        while n > 0:
            remainder = n % len(alphabet)
            result.append(alphabet[remainder])
            n = n // len(alphabet)
        return '_' + ''.join(result or 'a')

    def mode(self, token):
        self.current_mode = token.value
        self.terminals[self.current_mode] = []
        self.ignore_dict[self.current_mode] = []

    def ignore(self, node):
        terminal = self(node[0])
        if isinstance(node, Tree):
            if (
                    (len(terminal) > 4) or
                    (terminal[0] not in '\'"') or
                    (len(terminal) == 4 and terminal[1] != '\\')
            ):
                self.add_terminal(terminal, [terminal])
        self.ignore_dict[self.current_mode].append(terminal)


l, p = boho_grammar
lexer = Lexer(l)
parser = Parser(p)
interpreter = GrammarInterpreter()


def interpret(grammar: str):
    tokens = lexer(grammar)
    tree = parser(tokens)
    return interpreter(tree)
