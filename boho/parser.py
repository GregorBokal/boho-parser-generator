from .objects import (
    Token,
    Tree,
    ParserInstructions as PI,
    auxiliary
)
from typing import List


class Parser:

    def __init__(
            self,
            states: PI,
            start: str = '0'
    ):
        self.ignore = [] if '' not in states else states.pop('')
        self.states = states

        self.start = start

        self.lines = 0
        self.line = ''

    def __call__(self, tokens: List[Token], log=False):

        tokens.append(Token('$'))
        stack: List[str | Token | Tree] = [self.start]

        if log:
            print('#' * 20)
            print('SYNTACTIC ANALYSIS')
            print('#' * 20)

        while tokens:
            state = stack[-1]
            terminal = tokens[0].name

            if log:
                print('--' * 20)
                print(f'I\'m in state \033[1;33m{state}\033[0m.')
                print(f'I see terminal \033[1;32m{terminal!r}\033[0m.')

            action = self.states[state].get(
                terminal,
                self.states[state].get('')
            )

            if action is None:  # Unexpected terminal
                if terminal in self.ignore:
                    if log:
                        print('     It is unexpected, '
                              'but can be ignored.')
                    self.count(tokens.pop(0))
                else:
                    if log:
                        print('     It is unexpected, '
                              'and can\'t be ignored!')
                    self.error(tokens.pop(0), state)

            elif isinstance(action, bool):  # Accept
                if log:
                    print('     The tree is completed:\n')
                    print(stack[1].pretty(3))
                break

            elif isinstance(action, str):  # Shift
                if log:
                    print(f'     It matches with action '
                          f'\033[1;33m{action}\033[0m.')
                    print('     So let\'s SHIFT it on the stack')
                    print(f'     and go to the state \033[1;33m'
                          f'{action}\033[0m.')
                self.count(token := tokens.pop(0))
                stack.append(token)
                stack.append(action)

            else:  # Reduce
                lenght, name = action
                children = []

                if lenght:
                    for symbol in stack[-lenght * 2::2]:
                        if isinstance(symbol, Token):
                            if symbol.name[0] in auxiliary:
                                continue
                        elif symbol.name.startswith('_'):
                            children += symbol.children
                            continue
                        children.append(symbol)
                    del stack[-lenght * 2:]

                t = Tree(name, children)

                if name.endswith('_') and name[-2].isupper():
                    v = t.value
                    stack.append(Token(
                        name=name,
                        value=v,
                    ))
                    if log:
                        print(f'     It matches with action '
                              f'\033[1;33m{action}\033[0m.')
                        print(f'     It is fake terminal, so we'
                              f'turn it into token with value '
                              f'\033[1;32m{v}\033[0m.')
                else:
                    stack.append(t)
                    if log:
                        print(f'     It matches with action '
                              f'\033[1;33m{action}\033[0m.')
                        print(f'     So let\'s REDUCE some '
                              f'({lenght}) symbols and '
                              f'push this tree on the stack:')
                        print(t.pretty(3))
                stack.append(self.states[stack[-2]][name])
                if log:
                    print(f'     The next state is {stack[-1]}.')
        return stack[1]

    def count(self, token: Token):
        if token.line > self.lines:
            self.lines = token.line
            self.line = token.value
        else:
            self.line += ' ' + token.value

    def error(self, token: Token, state: str):
        msg = (f'Unexpected {token.name} in '
               f'state {state} at line {self.lines + 1}:\n'
               f'{self.line}{token.value}\n'
               f'{" " * (len(self.line) - self.line.count("\n"))}^\n'
               'Expected one of:\n     ' +
               '\n     '.join(c for c in self.states[state]
                              if c and c not in self.ignore))

        raise SyntaxError(msg)
