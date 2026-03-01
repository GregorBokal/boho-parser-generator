from .objects import (
    Token,
    LexerAction as Action,
    LexerInstructions as Instructions
)
from .regex import match
from typing import List


class Lexer:

    def __init__(
            self,
            instructions: Instructions,
            start_mode: str = None,
    ):

        self.instructions = instructions

        if start_mode is not None:
            self.start_mode: str = start_mode
        elif isinstance(
                name := self.instructions.get(''),
                str
        ):
            self.start_mode: str = name
        else:
            self.start_mode: str = list(
                self.instructions.keys()
            )[0]

        self.lines: int = 0
        self.line: str = ''

    def __call__(self, text: str, log=False) -> List[Token]:
        self.lines = 0
        self.line = ''

        tokens: List[Token] = []
        token = ''

        stack = [mode := self.start_mode]
        state = '0'
        i = 0

        if log:
            print('##' * 20)
            print('LEXICAL ANALYSIS')
            print('##' * 20)

        while i < len(text):
            mode = stack[-1]
            char = text[i]

            if log:
                print('--' * 20)
                print(f'I\'m in state \033[1;33m{state}\033[0m '
                      f'of mode \033[1;36m{mode}\033[0m.')
                print(f'I see char \033[1;32m{char!r}\033[0m.')

            action = self.get_action(
                mode, state, char
            )

            if action is None:  # Unexpected char
                ignore = self.instructions[
                    mode
                ].get('', [])
                if state == '0' and (
                        char in ignore
                ):
                    if log:
                        print('     It is unexpected, '
                              'but can be ignored.')
                    self.count(char)
                    i += 1
                else:
                    if log:
                        print('     It is unexpected, '
                              'and can\'t be ignored!')
                    if token:
                        for c in token:
                            if c not in ignore:
                                self.error(mode, state, char)
                        if log:
                            print(f'     But fortunately all '
                                  f'recently read chars can '
                                  f'be ignored: \033[1;32m{token!r}\033[0m')
                        token = ''
                        state = '0'
                    else:
                        self.error(mode, state, char)

            elif isinstance(action, str):  # Continuing
                if log:
                    print(f'     It matches with action '
                          f'\033[1;33m{action}\033[0m.')
                    print(f'     So let\'s expand the token '
                          f'\033[0;32m{token}\033[1;32m{char}'
                          f'\033[0m')
                    print(f'     And go to the state \033[1;33m'
                          f'{action}\033[0m.')
                self.count(char)
                token += char
                state = action
                i += 1

            elif isinstance(action, list):  # Finishing
                if log:
                    print(f'     It matches with action '
                          f'\033[1;31m{action}\033[0m.')
                    print(f'     Now the token \033[0;32m'
                          f'{(t := f"{action[0]} : {token}")}'
                          f'\033[0m is finished.', end='')
                    print(f'{' ' * max(5, 20 - len(t))}-->'
                          f'   \033[0;30;47m[{action[0]!r} :'
                          f' {token!r}]\033[0m')
                tokens.append(
                    Token(
                        action[0], token,
                        self.lines,
                        len(self.line) - len(token)
                    )
                )

                if log and len(action) - 1:
                    print(f'     Some changes on the stack '
                          f'of modes should be done ({action}):')
                c = 1
                while c < len(action):
                    change = action[c]
                    if isinstance(change, str):
                        if log:
                            print(f'        - Adding \033'
                                  f'[1;36m{change}\033[0m '
                                  f'on the top of the stack.')
                        stack.append(change)
                    elif isinstance(change, int):
                        if len(stack) >= change > 0:
                            if log:
                                print(f'        - Deleting '
                                      f'{change} elements from '
                                      f'the top of the stack.')
                            del stack[-change:]
                        else:
                            print(f'        - Emptying the stack.')
                            stack = []
                    c += 1

                token = ''
                state = '0'

        if token:
            try:
                name = self.instructions[stack[-1]][state][''][0]
                assert isinstance(name, str)
                if log:
                    print('I see the end of file.')
                    print(f'     And here is the final token '
                          f'\033[0;32m{(t := f"{name} : {token}")}'
                          f'\033[0m.', end='')
                    print(f'{' ' * max(3, 18 - len(t))}-->   '
                          f'\033[0;30;47m[{name} : {token}]\033[0m')
                tokens.append(
                    Token(
                        name, token,
                        self.lines,
                        len(self.line) - len(token)
                    )
                )
            except KeyError:
                raise SyntaxError(
                    f'Unfinished token at the end of '
                    f'file in state {state} of mode '
                    f'{mode}\n(\'\' option must'
                    f'be expected here)'
                )
            except TypeError:
                raise SyntaxError(
                    f'Unfinished token at the end of '
                    f'file in state {state} of mode '
                    f'{mode}\n(option \'\' must'
                    f'trigger finishing action here)'
                )

        return tokens

    def get_action(
            self, mode: str, state: str, char: str
    ) -> Action | None:
        try:
            for expected, action in self.instructions[
                mode
            ][state].items():
                if expected and match(expected, char):
                    return action
            return self.instructions[mode][state].get('')
        except KeyError:
            raise KeyError(f'Unknown mode {mode}')
        except IndexError:
            if mode:
                raise IndexError(
                    f'Unknown state {state} in mode {mode}'
                )
            else:
                raise IndexError(f'Unknown state {state}')

    def count(self, char: str) -> None:
        if char == '\n':
            self.lines += 1
            self.line = ''
        else:
            self.line += char

    def error(
            self, mode: str, state: str, char: str
    ) -> None:

        msg = (f'Unexpected character {char!r} '
               f'in state {state} of mode {mode} at '
               f'line {self.lines + 1}:\n{self.line}'
               f'{char}\n{" " * (len(self.line))}^\n'
               'Expected one of:\n     ' +
               '\n     '.join(
                   f'{c!r}' for c in self.instructions[
                       mode
                   ][state] if c
               ))

        raise SyntaxError(msg)
