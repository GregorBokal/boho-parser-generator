import re
from greenery import parse
from .objects import LexerDFA, LexerAction


def match(pattern: str, text: str) -> bool:
    if re.match(pattern, text):
        return True
    return False


def regex_to_dfa(regex: str, action: LexerAction) -> LexerDFA:
    base = parse(regex).to_fsm()
    # A "dead" state is a non-final sink: every outgoing transition
    # loops back to itself, so no final state is reachable from it.
    # Pass-through states (all transitions to the SAME other state)
    # used to be pruned here too, which incorrectly dropped legitimate
    # intermediate states like the "\X" branch in '\\.' escapes.
    error_states = [
        state for state, transitions in base.map.items()
        if state not in base.finals
        and transitions
        and all(target == state for target in transitions.values())
    ]

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
