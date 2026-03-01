from .grammar_interpreter import interpret
from .lexer import Lexer
from .parser import Parser
from .lexer_generator import generate as prepare_lex
from .parser_generator import generate as prepare_pars


class Boho:

    def __init__(self, grammar: str, log: bool = False):
        (
            self.tokens,
            self.grammar,
            self.ignore_dict
        ) = interpret(grammar)
        self.lex_table = prepare_lex(self.tokens, log=log)
        self.pars_table = prepare_pars(self.grammar, log=log)
        for mode in self.ignore_dict:
            for description in self.ignore_dict[mode]:
                if (
                        (len(description) > 4) or
                        (description[0] not in '\'"') or
                        (len(description) == 4 and description[1] != '\\')
                ):
                    if '' in self.pars_table:
                        self.pars_table[''].append(description)
                    else:
                        self.pars_table[''] = [description]
                        continue
                if '' in self.lex_table[mode]:
                    self.lex_table[mode][''].append(description[1:-1])
                else:
                    self.lex_table[mode][''] = [description[1:-1]]
        self.lexer = Lexer(self.lex_table)
        self.parser = Parser(self.pars_table)

    def __call__(self, text: str, log: bool = False):
        return self.parser(self.lexer(text, log), log)
