import json

from .grammar_interpreter import interpret
from .lexer import Lexer
from .parser import Parser
from .lexer_generator import generate as prepare_lex
from .parser_generator import generate as prepare_pars


class Boho:

    def __init__(
            self,
            grammar: str,
            log: bool = False
    ):

        (
            self.tokens,
            self.grammar,
            self.ignore_dict
        ) = interpret(grammar)
        lex_table = prepare_lex(self.tokens, log=log)
        pars_table = prepare_pars(self.grammar, log=log)
        for mode in self.ignore_dict:
            for description in self.ignore_dict[mode]:
                if (
                        (len(description) > 4) or
                        (description[0] not in '\'"') or
                        (len(description) == 4 and description[1] != '\\')
                ):
                    if '' in pars_table:
                        pars_table[''].append(description)
                    else:
                        pars_table[''] = [description]
                        continue
                if '' in lex_table[mode]:
                    lex_table[mode][''].append(description[1:-1])
                else:
                    lex_table[mode][''] = [description[1:-1]]
        self._setup(lex_table, pars_table)

    @classmethod
    def from_tables(cls, lex_table, pars_table):
        """Build a Boho instance from pre-computed lexer and parser tables.

        Skips the (potentially slow) grammar-to-tables compilation. Ideal
        when tables come from ``save()``, ``tables`` or ``grammars.py``."""
        self = cls.__new__(cls)
        self._setup(lex_table, pars_table)
        return self

    @classmethod
    def load(cls, path):
        """Build a Boho instance from a JSON file previously written by
        ``save()``. The file must contain ``[lex_table, pars_table]``."""
        with open(path, encoding='utf-8') as f:
            lex_table, pars_table = json.load(f)
        return cls.from_tables(lex_table, pars_table)

    def save(self, path):
        """Serialize the current tables to a JSON file."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.tables, f)

    @property
    def tables(self):
        """``[lex_table, pars_table]`` — ready to feed back into
        ``from_tables`` or ``save``."""
        return [self.lex_table, self.pars_table]

    def _setup(self, lex_table, pars_table):
        self.lex_table = lex_table
        self.pars_table = pars_table
        self.lexer = Lexer(lex_table)
        # Parser mutates its input (pops ''), so pass a shallow copy
        # to keep self.pars_table intact for save() / tables.
        self.parser = Parser(dict(pars_table))

    def __call__(self, text: str, log: bool = False):
        return self.parser(self.lexer(text, log), log)
