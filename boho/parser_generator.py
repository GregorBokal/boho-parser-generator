from typing import Dict, Set, FrozenSet, List, Tuple
from pprint import pprint

from .objects import (
    Grammar,
    LR1Item,
    ParserAction,
    ParserInstructions
)

START = "S'"
END = '$'


class LR1ParserGenerator:

    def __init__(self):
        self.grammar: Grammar = {}
        self.first_cache: Dict[str, FrozenSet[str]] = {}

        self.table: ParserInstructions = {}
        self.conflicts: Dict[Tuple[str, str], str] = {}

        self.log: bool = False

    def __call__(
            self,
            grammar: Grammar,
            start: str = 'start',
            log: bool = False,
    ) -> ParserInstructions:

        self.log = log
        if self.log:
            print('##' * 20)
            print('Generating instructions for the parser')
            print('##' * 20)

        assert START not in grammar, \
            f'{START} is reserved for augmentation.'
        self.grammar = grammar
        self.grammar[START] = [(start,)]
        self.compute_first_sets()

        return self.states(start)

    def states(self, start):
        start_item = LR1Item(START, (start,), 0, END)
        start_state = self.closure([start_item])

        states = [start_state]
        self.table = {}
        queue = [0]

        if self.log:
            print('We have the following grammar:')
            pprint(self.grammar)
            print(f'The start item is \033[1;36m{start_item}\033[0m.')

        while queue:
            i = queue.pop(0)
            state = states[i]
            seen = {None}
            if self.log:
                print('--' * 20)
                print(f'Let\'s scan the state \033[1;33m{i}\033[0m.')
                print('--' * 20)

            for item in state:

                if item.is_complete:
                    lookahead = item.lookahead
                    new = item.head
                    if new == START:
                        if self.log:
                            print(f'\033[1;36m{item}\033[0m')
                            print(f' └── At symbol \033[1;32m'
                                  f'{lookahead}\033[0m we can '
                                  f'\033[1;33mfinish\033[0m!')
                        self.action(str(i), lookahead, True)
                    else:
                        length = len(item.body)
                        if self.log:
                            print(f'\033[1;36m{item}\033[0m')
                            print(f' └── At symbol \033[1;32m'
                                  f'{lookahead}\033[0m we can '
                                  f'reduce some symbols ({length}) to '
                                  f'\033[1;33m{new}\033[0m.')
                        self.action(str(i), lookahead, (length, new))
                if (symbol := item.next_symbol) not in seen:
                    seen.add(symbol)
                    next_state = self.goto(state, symbol)
                    if next_state in states:
                        new = states.index(next_state)
                        if self.log:
                            print(f'\033[1;36m{item}\033[0m')
                            print(f' └── Symbol \033[1;32m'
                                  f'{symbol}\033[0m moves us '
                                  f'to an already existing state '
                                  f'\033[1;33m{new}\033[0m.')
                    else:
                        new = len(states)
                        states.append(next_state)
                        queue.append(new)
                        if self.log:
                            print(f'\033[1;36m{item}\033[0m')
                            print(f' └── Symbol \033[1;32m'
                                  f'{symbol}\033[0m moves us '
                                  f'to a new state ('
                                  f'\033[1;33m{new}\033[0m).')
                    self.action(str(i), symbol, str(new))
                elif self.log:
                    print(f'\033[1;36m{item}\033[0m')
        if self.log:
            print('\nThe parser instructions are now finished:\n')
            pprint(self.table)
        return self.table

    def closure(self, items: List[LR1Item]) -> List[LR1Item]:
        queue = list(items)
        while queue:
            item = queue.pop(0)
            symbol = item.next_symbol
            if symbol in self.grammar.keys():
                following = item.body[item.dot + 1:]
                ahead = self.first(following + (item.lookahead,))
                for body in self.grammar[symbol]:
                    for terminal in sorted(ahead):
                        new_item = LR1Item(symbol, body, 0, terminal)
                        if new_item not in items:
                            items.append(new_item)
                            queue.append(new_item)
        return items

    def goto(self, items: List[LR1Item], symbol: str) -> List[LR1Item]:
        result: List[LR1Item] = []
        for item in items:
            if item.next_symbol == symbol:
                next_item = item.next_item()
                if next_item not in result:
                    result.append(next_item)
        return self.closure(result)

    def compute_first_sets(self):
        for nonterminal in self.grammar:
            self.first_cache[nonterminal] = frozenset()
        changed = True
        while changed:
            changed = False
            for nonterminal, productions in self.grammar.items():
                old = self.first_cache[nonterminal]
                new = set(old)
                for production in productions:
                    if production == ():
                        new.add('')
                        continue
                    for symbol in production:
                        if symbol in self.grammar:
                            new |= (self.first_cache[symbol] - {''})
                            if '' not in self.first_cache[symbol]:
                                break
                        else:
                            new.add(symbol)
                            break
                    else:
                        new.add('')
                result = frozenset(new)
                if result != old:
                    self.first_cache[nonterminal] = result
                    changed = True

    def first(self, symbols: Tuple[str, ...]) -> Set[str]:
        result = set()
        for symbol in symbols:
            if symbol in self.grammar:
                terminals = self.first_cache[symbol]
                result |= (terminals - {''})
                if '' not in terminals:
                    break
            else:
                result.add(symbol)
                break
        else:
            result.add('')
        return result

    def action(
            self,
            state: str,
            symbol: str,
            action: ParserAction
    ):
        if state in self.table:
            existing = self.table[state].get(symbol)
            if existing and existing != action:
                if isinstance(existing, str) and isinstance(action, tuple):
                    conflict = 'Shift-reduce'
                elif isinstance(existing, tuple):
                    if isinstance(action, str):
                        conflict = 'Shift-reduce'
                        self.table[state][symbol] = action
                    else:
                        conflict = 'Reduce-reduce'
                else:
                    conflict = 'Unknown'
                message = (
                    f'{conflict} conflict in state '
                    f'\033[1;33m{state}\033[0m at symbol '
                    f'\033[1;32m{symbol}\033[0m ('
                    f'\033[1;33m{existing}\033[0m vs. '
                    f'\033[1;33m{action}\033[0m).'
                )
                self.conflicts[(state, symbol)] = message
                if self.log:
                    print('     But there is a conflict:')
                    print('     ' + message)
                    if conflict == 'Shift-reduce':
                        print('     In those cases, the shift action wins.')
                    elif conflict == 'Reduce-reduce':
                        print('     In those cases, the first action wins.')
            else:
                self.table[state][symbol] = action
        else:
            self.table[state] = {symbol: action}


options = {
    'LR1': LR1ParserGenerator
}


def generate(
        grammar: Grammar,
        start: str = 'start',
        kind: str = 'LR1',
        log: bool = False
):
    if generator := options.get(kind):
        return generator()(grammar, start, log)
    else:
        raise NotImplementedError(f'{kind} is not implemented. '
                                  f'Use one of {", ".join(
                                      list(options.keys())
                                  )} instead.')
