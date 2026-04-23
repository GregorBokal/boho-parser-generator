from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

LexerAction = str | List[str | int]
LexerDFA = Dict[str, List[str] | Dict[str, LexerAction]]
LexerInstructions = Dict[str, str | LexerDFA]

ParserAction = bool | str | Tuple[int, str]
ParserInstructions = Dict[str, ParserAction | List[str]]

TerminalList = List[Tuple[str, List[str | int]]]
TerminalDescription = Dict[str, TerminalList]
Grammar = Dict[str, List[Tuple[str, ...]]]

unnamed = '\'"/@'
auxiliary = unnamed + '_'


@dataclass
class Token:
    name: str
    value: str = ''
    line: int = 0
    col: int = 0

    def pretty(self, _level: int = 0) -> str:
        return _level * '  ' + f'{self.name!r} {self.value!r}'


@dataclass
class Tree:
    name: str
    children: List['Tree | Token']
    line: Optional[int] = None
    col: Optional[int] = None
    end_line: Optional[int] = None
    end_col: Optional[int] = None

    def __iter__(self):
        return iter(self.children)

    def __getitem__(self, index):
        return self.children[index]

    def __len__(self):
        return len(self.children)

    @property
    def value(self):
        return ''.join(c.value for c in self.children)

    def pretty(self, _level=0):
        i = '  ' * _level
        if self.children:
            p = ':\n' + '\n'.join(c.pretty(_level + 1) for c in self.children)
        else:
            p = ''
        return f'{i}{self.name}{p}'


@dataclass(frozen=True)
class LR1Item:
    head: str
    body: Tuple[str, ...]
    dot: int
    lookahead: str

    def __repr__(self):
        before = ' '.join(self.body[:self.dot])
        after = ' '.join(self.body[self.dot:])
        return f"[{self.head} -> {before} • {after}, {self.lookahead}]"

    @property
    def is_complete(self) -> bool:
        return self.dot >= len(self.body)

    @property
    def next_symbol(self) -> str | None:
        if self.dot < len(self.body):
            return self.body[self.dot]
        return None

    def next_item(self) -> 'LR1Item':
        return LR1Item(self.head, self.body, self.dot + 1, self.lookahead)
