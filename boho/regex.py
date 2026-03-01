import re
from greenery import parse
from .objects import LexerDFA, LexerAction


def match(pattern: str, text: str) -> bool:
    if re.match(pattern, text):
        return True
    return False


def regex_to_dfa(regex: str, action: LexerAction) -> LexerDFA:
    base = parse(regex).to_fsm()
    error_states = []
    for state in base.map:
        if state not in base.finals:
            values = list(base.map[state].values())
            first = values.pop(0)
            for value in values:
                if value == first:
                    continue
                else:
                    break
            else:
                error_states.append(state)

    dfa = {}
    for state in base.map:
        actions = {

        } if state not in base.finals else {
            '': action
        }
        for chars, next_state in base.map[state].items():
            if next_state in error_states:
                continue
            else:
                actions[str(chars)] = str(next_state)
        if actions:
            dfa[str(state)] = actions

    return dfa
