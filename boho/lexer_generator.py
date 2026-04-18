import copy

from .regex import regex_to_dfa, parse
from .objects import (
    LexerAction,
    LexerDFA,
    TerminalDescription as Input,
    LexerInstructions as Output,
)
from pprint import pprint

standard = {
    'INT': {
        '0': {'-': '1', r'\d': '2'},
        '1': {r'\d': '2'},
        '2': {r'\d': '2'}
    },
    'FLOAT': {
        '0': {'-': '1', r'\.': '2', r'\d': '1'},
        '1': {r'\.': '2', r'\d': '1'},
        '2': {r'\d': '3'},
        '3': {r'\d': '3'}
    },
    'STR': {
        '0': {'"': '1', "'": '2'},
        '1': {'[^"\\n]': '1', r'\\': '3', '"': '5'},
        '2': {"[^'\\n]": '2', r'\\': '4', "'": '5', },
        '3': {'.': '1'},
        '4': {'.': '2'},
        '5': {}
    }
}


def generate(modes: Input, log=False) -> Output:
    if log:
        print('##' * 20)
        print('Generating instructions for lexer')
        print('##' * 20)
    instructions = {}
    for mode in modes:
        dfa_list = [generate_dfa(*t) for t in modes[mode]]
        states = dfa_list.pop(0)
        usages = {}
        n = 0
        for s in states:
            for v in states[s].values():
                if isinstance(v, str) and v != s:
                    if v in usages:
                        usages[v] += 1
                    else:
                        usages[v] = 1
        if log:
            print('++' * 20)
            if modes:
                print(f'The next mode is \033[1;36m{mode}\033[0m.')
            print(f'Initial DFA is {states}.')
        for dfa in dfa_list:
            if log: print(f'Let\'s merge it with DFA {dfa}.')
            dictionary = {}
            queue = [('0', '0')]
            while queue:
                main, current = queue.pop(0)
                state = {}
                just_old = {}
                for chars, action in states[main].items():
                    if isinstance(action, list):
                        action = tuple(action)
                    if action in just_old:
                        just_old[action] |= parse(chars)
                    else:
                        just_old[action] = parse(chars)
                if log:
                    print('--' * 20)
                    print(f'Merging main state '
                          f'\033[1;33m*{main}*\033[0m '
                          f'with current state \033[0;'
                          f'33m{current}\033[0m.')
                    print('--' * 20)
                for rn, new in dfa[current].items():
                    just_new = parse(rn)
                    rn = parse(rn)
                    if log:
                        print(f'Let\'s check for conflicts '
                              f'at char \033[1;32m'
                              f'{rn}\033[0m.')
                    if old_actions := states[main].items():
                        for ro, old in old_actions:
                            ro = parse(ro)
                            if not (both := ro & rn).empty():
                                just_new -= both
                                just_old[old if isinstance(old, str) else tuple(old)] -= both
                                if log:
                                    print(f'    There is a conflict with {both}!')
                                if isinstance(new, str):
                                    if isinstance(old, str):
                                        if (name := dictionary.get((old, new))) is not None:
                                            state[str(both)] = name
                                            if log:
                                                print(f'    But it should have already been resolved '
                                                      f'in state \033[1;33m*{name}*\033[0m.')
                                        elif usages[old] == 1:
                                            queue.append((old, new))
                                            state[str(both)] = old
                                            dictionary[(old, new)] = old
                                            if log:
                                                print('    Fortunately, '
                                                      'neither action is final, '
                                                      'so let\'s use state '
                                                      f'\033[1;33m*{old}*\033[0m (which '
                                                      f'is not used in any other case) to '
                                                      f'resolve this conflict there.')
                                        else:
                                            while str(n) in states:
                                                n += 1
                                            name = str(n)
                                            states[name] = states[old]
                                            for v in states[name].values():
                                                if isinstance(v, str):
                                                    usages[v] += 1
                                            queue.append((name, new))
                                            usages[old] -= 1
                                            usages[name] = 1
                                            dictionary[(old, new)] = name
                                            state[str(both)] = name
                                            if log:
                                                print('    Fortunately, '
                                                      'neither action is final, '
                                                      'so let\'s create a new state '
                                                      f'\033[1;33m*{name}*\033[0m, where '
                                                      f'this conflict can be resolved.')
                                    elif isinstance(old, list):  # error
                                        for values in list(dfa[current].values())[::-1]:
                                            for value in values:
                                                if isinstance(value, list):
                                                    raise SyntaxError(
                                                        f'Tokens {old[0]} and {value[0]} are inseparable.')
                                        raise SyntaxError(f'Terminal {old[0]} is inseparable from some other token.')
                                elif isinstance(old, list):
                                    if log and old != new:
                                        print(f'    Tokens {old[0]} and '
                                              f'{new[0]} are inseparable, '
                                              f'but {old[0]} wins, because it'
                                              f'is declared first.')
                                    state[str(both)] = old
                                else:  # error
                                    seen = set()
                                    error_queue = [old]
                                    while error_queue:
                                        s = error_queue.pop(0)
                                        seen.add(s)
                                        for value in states[s].values():
                                            if isinstance(value, list):
                                                raise SyntaxError(
                                                    f'Tokens {old[0]} and {value[0]} are inseparable.')
                                            if value not in seen:
                                                error_queue.append(value)
                                    raise SyntaxError(f'Token {old[0]} is inseparable from some other token.')
                    else:
                        just_new = rn
                    if not just_new.empty():
                        chars = str(just_new)
                        if log:
                            print(f'    Characters '
                                  f'\033[1;32m{chars}'
                                  f'\033[0m only match '
                                  f'the new action '
                                  f'\033[1;33m{new}\033[0m.')
                        if isinstance(new, list):
                            state[chars] = new
                            if log:
                                print('    It\'s the '
                                      'final action, so it '
                                      'can stay unchanged.')
                        else:
                            if (translation := dictionary.get(new)) is None:
                                while str(n) in states:
                                    n += 1
                                translation = str(n)
                                dictionary[new] = translation
                                states[translation] = {}
                                queue.append((translation, new))
                                usages[translation] = 1
                                if log:
                                    print('    It\'s not the '
                                          'final action, so let\'s '
                                          'translate it to \033[1;33m'
                                          f'*{translation}*\033[0m.')
                            else:
                                usages[translation] = usages.get(translation, 0) + 1
                                if log:
                                    print('    It\'s not the '
                                          'final action, so it should '
                                          'be translated as \033[1;33m'
                                          f'*{translation}*\033[0m.')
                            state[chars] = translation
                for action, chars in just_old.items():
                    if not chars.empty():
                        if log:
                            print(f'Characters \033[1;32m{chars}'
                                  f'\033[0m can keep the action '
                                  f'\033[1;33m{action}\033[0m.')
                        state[str(chars)] = action if isinstance(
                            action, str) else list(action)
                old_targets = {v for v in states[main].values() if isinstance(v, str) and v != main}
                new_targets = {v for v in state.values() if isinstance(v, str) and v != main}
                for lost in old_targets - new_targets:
                    usages[lost] -= 1
                for gained in new_targets - old_targets:
                    usages[gained] = usages.get(gained, 0) + 1
                states[main] = state
                if log:
                    print('At the moment, the merged DFA looks like:')
                    pprint(states)
                    print(usages)
        if log:
            print('++' * 20)
            print(f'Merged DFA for mode \033[1;36m{mode}\033[0m is finished!')
            pprint(states)
        instructions[mode] = states
    if log:
        print('\nInstructions for lexer are finished now:\n')
        pprint(instructions)
    return instructions


def generate_dfa(description: str, action: LexerAction) -> LexerDFA:
    match description[0]:
        case '"':
            assert description.endswith('"')
            return str_to_dfa(description[1:-1], action)

        case '@':
            if prepared := standard.get(description[1:]):
                dfa = copy.deepcopy(prepared)
                dfa[str(len(dfa) - 1)][''] = action
                return dfa
            else:
                raise NotImplementedError(f'Terminal {description} does not exist.')

        case '/':
            assert description.endswith('/'), description
            return regex_to_dfa(desc_to_regex(description[1:-1]), action)

        case _:
            raise SyntaxError(f'Unrecognized token {description}.')


def str_to_dfa(string: str, action: LexerAction) -> LexerDFA:
    dfa = {str(len(string)): {'': action}}
    for i, char in enumerate(string):
        if char in '.^$*+?{}[]()|\\':
            char = '\\' + char
        dfa[str(i)] = {char: str(i + 1)}
    return dfa


def desc_to_regex(description: str) -> str:
    e = False
    r = ''
    for char in description:
        if e:
            if char != '/':
                r += '\\'
            r += char
            e = False
        elif char == '\\':
            e = True
        else:
            r += char
    return r
