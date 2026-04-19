import pytest

from boho.lexer import Lexer
from boho.objects import Token


# ── Fixtures ──────────────────────────────────────────────


@pytest.fixture
def simple_instructions():
    """Simple single-current_mode lexer: recognizes 'h' followed by vowels."""
    return {
        '': {
            '': [' '],
            '0': {
                'h': '1'
            },
            '1': {
                '[aeiou]': '1',
                '': ['ha']
            }
        }
    }


@pytest.fixture
def modal_instructions():
    """Modal lexer: text current_mode with nested expression current_mode via parentheses."""
    return {
        '': 'text',
        'text': {
            '0': {
                '[^(]': '1',
                r'\(': '2'
            },
            '1': {
                '[^(]': '1',
                '': ['text']
            },
            '2': {
                '': ['(', 'expression']
            }
        },
        'expression': {
            '': [' '],
            '0': {
                r'\d': '1',
                r'\(': '2',
                r'\)': '3'
            },
            '1': {
                r'\d': '1',
                '': ['number'],
            },
            '2': {
                '': ['(', 'expression']
            },
            '3': {
                '': [')', 1]
            }
        }
    }


# ── Basic examples from examples/lexer_example.py ────────────────


class TestSimpleLexer:

    def test_basic_tokenization(self, simple_instructions):
        lexer = Lexer(simple_instructions)
        tokens = lexer('haa haa hehia')
        assert tokens == [
            Token('ha', 'haa', 0, 0),
            Token('ha', 'haa', 0, 4),
            Token('ha', 'he', 0, 8),
            Token('ha', 'hia', 0, 10),
        ]

    def test_single_token(self, simple_instructions):
        lexer = Lexer(simple_instructions)
        tokens = lexer('ha')
        assert tokens == [Token('ha', 'ha', 0, 0)]

    def test_only_h(self, simple_instructions):
        """'h' alone should finish via the default action in state 1."""
        lexer = Lexer(simple_instructions)
        tokens = lexer('h')
        assert tokens == [Token('ha', 'h', 0, 0)]

    def test_empty_input(self, simple_instructions):
        lexer = Lexer(simple_instructions)
        tokens = lexer('')
        assert tokens == []

    def test_ignore_multiple_spaces(self, simple_instructions):
        lexer = Lexer(simple_instructions)
        tokens = lexer('ha  ha')
        assert tokens == [
            Token('ha', 'ha', 0, 0),
            Token('ha', 'ha', 0, 4),
        ]

    def test_many_vowels(self, simple_instructions):
        lexer = Lexer(simple_instructions)
        tokens = lexer('haeiou')
        assert tokens == [Token('ha', 'haeiou', 0, 0)]


class TestModalLexer:

    def test_nested_parentheses(self, modal_instructions):
        lexer = Lexer(modal_instructions)
        tokens = lexer('00(11 (2 2(33)22)11)00')
        assert tokens == [
            Token('text', '00', 0, 0),
            Token('(', '(', 0, 2),
            Token('number', '11', 0, 3),
            Token('(', '(', 0, 6),
            Token('number', '2', 0, 7),
            Token('number', '2', 0, 9),
            Token('(', '(', 0, 10),
            Token('number', '33', 0, 11),
            Token(')', ')', 0, 13),
            Token('number', '22', 0, 14),
            Token(')', ')', 0, 16),
            Token('number', '11', 0, 17),
            Token(')', ')', 0, 19),
            Token('text', '00', 0, 20),
        ]

    def test_text_only(self, modal_instructions):
        lexer = Lexer(modal_instructions)
        tokens = lexer('hello')
        assert tokens == [Token('text', 'hello', 0, 0)]

    def test_empty_parentheses(self, modal_instructions):
        lexer = Lexer(modal_instructions)
        tokens = lexer('a()b')
        assert tokens == [
            Token('text', 'a', 0, 0),
            Token('(', '(', 0, 1),
            Token(')', ')', 0, 2),
            Token('text', 'b', 0, 3),
        ]

    def test_parentheses_with_spaces(self, modal_instructions):
        lexer = Lexer(modal_instructions)
        tokens = lexer('(  1  )')
        assert tokens == [
            Token('(', '(', 0, 0),
            Token('number', '1', 0, 3),
            Token(')', ')', 0, 6),
        ]


# ── Start current_mode selection ─────────────────────────────────


class TestStartMode:

    def test_explicit_start_mode(self):
        instructions = {
            'a': {
                '0': {'x': '1'},
                '1': {'': ['X']}
            },
            'b': {
                '0': {'y': '1'},
                '1': {'': ['Y']}
            }
        }
        lexer = Lexer(instructions, start_mode='b')
        tokens = lexer('y')
        assert tokens == [Token('Y', 'y', 0, 0)]

    def test_default_key_start_mode(self):
        instructions = {
            '': 'b',
            'a': {
                '0': {'x': '1'},
                '1': {'': ['X']}
            },
            'b': {
                '0': {'y': '1'},
                '1': {'': ['Y']}
            }
        }
        lexer = Lexer(instructions)
        tokens = lexer('y')
        assert tokens == [Token('Y', 'y', 0, 0)]

    def test_first_mode_as_default(self):
        instructions = {
            'first': {
                '0': {'z': '1'},
                '1': {'': ['Z']}
            },
            'second': {
                '0': {'w': '1'},
                '1': {'': ['W']}
            }
        }
        lexer = Lexer(instructions)
        tokens = lexer('z')
        assert tokens == [Token('Z', 'z', 0, 0)]


# ── Line and column tracking ─────────────────────────────


class TestLineColumnTracking:

    def test_multiline_input(self):
        instructions = {
            '': {
                '': [' ', '\n'],
                '0': {'h': '1'},
                '1': {'[aeiou]': '1', '': ['ha']}
            }
        }
        lexer = Lexer(instructions)
        tokens = lexer('ha\nhe')
        assert tokens[0] == Token('ha', 'ha', 0, 0)
        assert tokens[1] == Token('ha', 'he', 1, 0)

    def test_multiline_columns(self):
        instructions = {
            '': {
                '': [' ', '\n'],
                '0': {'h': '1'},
                '1': {'[aeiou]': '1', '': ['ha']}
            }
        }
        lexer = Lexer(instructions)
        tokens = lexer('ha\n ha')
        assert tokens[1] == Token('ha', 'ha', 1, 1)

    def test_multiple_newlines(self):
        instructions = {
            '': {
                '': [' ', '\n'],
                '0': {'[a-z]': '1'},
                '1': {'[a-z]': '1', '': ['word']}
            }
        }
        lexer = Lexer(instructions)
        tokens = lexer('ab\n\ncd')
        assert tokens == [
            Token('word', 'ab', 0, 0),
            Token('word', 'cd', 2, 0),
        ]


# ── Error handling ────────────────────────────────────────


class TestErrors:

    def test_unexpected_character(self, simple_instructions):
        lexer = Lexer(simple_instructions)
        with pytest.raises(SyntaxError, match='Unexpected character'):
            lexer('x')

    def test_unexpected_char_in_middle(self, simple_instructions):
        lexer = Lexer(simple_instructions)
        with pytest.raises(SyntaxError, match='Unexpected character'):
            lexer('h1')  # '1' not expected in state 1

    def test_error_message_contains_line_info(self, simple_instructions):
        lexer = Lexer(simple_instructions)
        with pytest.raises(SyntaxError, match='line 1'):
            lexer('x')

    def test_error_message_contains_expected(self, simple_instructions):
        lexer = Lexer(simple_instructions)
        with pytest.raises(SyntaxError, match='Expected one of'):
            lexer('x')

    def test_unfinished_token_at_eof(self):
        """State without a default '' action should raise on EOF."""
        instructions = {
            '': {
                '0': {'a': '1'},
                '1': {'b': '2'},
                '2': {'': ['ab']}
            }
        }
        lexer = Lexer(instructions)
        with pytest.raises(SyntaxError, match='Unfinished token'):
            lexer('a')  # stuck in state 1, no '' fallback

    def test_unknown_mode_raises(self):
        instructions = {
            'main': {
                '0': {'a': '1'},
                '1': {'': ['tok', 'nonexistent']}
            }
        }
        lexer = Lexer(instructions)
        with pytest.raises(KeyError, match='Unknown mode'):
            lexer('aa')  # pushes 'nonexistent', then fails


# ── Stack operations ──────────────────────────────────────


class TestStackOperations:

    def test_push_and_pop(self):
        """Push a current_mode, do work, pop back."""
        instructions = {
            '': 'outer',
            'outer': {
                '0': {
                    'a': '1',
                    r'\[': '2',
                },
                '1': {
                    'a': '1',
                    '': ['word']
                },
                '2': {
                    '': ['[', 'inner']
                }
            },
            'inner': {
                '0': {
                    r'\d': '1',
                    r'\]': '2',
                },
                '1': {
                    r'\d': '1',
                    '': ['num']
                },
                '2': {
                    '': [']', 1]
                }
            }
        }
        lexer = Lexer(instructions)
        tokens = lexer('aa[12]aa')
        assert tokens == [
            Token('word', 'aa', 0, 0),
            Token('[', '[', 0, 2),
            Token('num', '12', 0, 3),
            Token(']', ']', 0, 5),
            Token('word', 'aa', 0, 6),
        ]

    def test_double_nested_push_pop(self):
        """Two levels of nesting."""
        instructions = {
            '': 'L0',
            'L0': {
                '0': {'a': '1', r'\(': '2'},
                '1': {'a': '1', '': ['A']},
                '2': {'': ['(', 'L1']}
            },
            'L1': {
                '0': {'b': '1', r'\(': '2', r'\)': '3'},
                '1': {'b': '1', '': ['B']},
                '2': {'': ['(', 'L2']},
                '3': {'': [')', 1]}
            },
            'L2': {
                '0': {'c': '1', r'\)': '2'},
                '1': {'c': '1', '': ['C']},
                '2': {'': [')', 1]}
            }
        }
        lexer = Lexer(instructions)
        tokens = lexer('a((c)b)a')
        names = [t.name for t in tokens]
        assert names == ['A', '(', '(', 'C', ')', 'B', ')', 'A']


# ── Ignore characters ────────────────────────────────────


class TestIgnoreCharacters:

    def test_ignore_tabs_and_spaces(self):
        instructions = {
            '': {
                '': [' ', '\t'],
                '0': {'[a-z]': '1'},
                '1': {'[a-z]': '1', '': ['w']}
            }
        }
        lexer = Lexer(instructions)
        tokens = lexer('ab \t cd')
        assert tokens == [
            Token('w', 'ab', 0, 0),
            Token('w', 'cd', 0, 5),
        ]

    def test_ignore_only_between_tokens(self):
        """Ignored chars should only be skipped in state 0."""
        instructions = {
            '': {
                '': ['-'],
                '0': {'[a-z]': '1'},
                '1': {'[a-z]': '1', '': ['w']}
            }
        }
        lexer = Lexer(instructions)
        # '-' between tokens is ok
        tokens = lexer('ab-cd')
        assert tokens == [
            Token('w', 'ab', 0, 0),
            Token('w', 'cd', 0, 3),
        ]


# ── Regex patterns in state keys ─────────────────────────


class TestRegexPatterns:

    def test_digit_class(self):
        instructions = {
            '': {
                '0': {r'\d': '1'},
                '1': {r'\d': '1', '': ['num']}
            }
        }
        lexer = Lexer(instructions)
        tokens = lexer('42')
        assert tokens == [Token('num', '42', 0, 0)]

    def test_negated_class(self):
        instructions = {
            '': {
                '0': {'[^x]': '1'},
                '1': {'[^x]': '1', '': ['notx']}
            }
        }
        lexer = Lexer(instructions)
        tokens = lexer('ab')
        assert tokens == [Token('notx', 'ab', 0, 0)]

    def test_dot_matches_any(self):
        instructions = {
            '': {
                '0': {'.': '1'},
                '1': {'': ['any']}
            }
        }
        lexer = Lexer(instructions)
        tokens = lexer('xy')
        assert tokens == [
            Token('any', 'x', 0, 0),
            Token('any', 'y', 0, 1),
        ]


# ── Reusability ───────────────────────────────────────────


class TestReusability:

    def test_lexer_can_be_called_multiple_times(self, simple_instructions):
        lexer = Lexer(simple_instructions)
        t1 = lexer('ha')
        t2 = lexer('he')
        assert t1 == [Token('ha', 'ha', 0, 0)]
        assert t2 == [Token('ha', 'he', 0, 0)]

    def test_line_counter_resets(self):
        instructions = {
            '': {
                '': [' ', '\n'],
                '0': {'h': '1'},
                '1': {'[aeiou]': '1', '': ['ha']}
            }
        }
        lexer = Lexer(instructions)
        lexer('ha\nhe')
        tokens = lexer('ha')
        assert tokens[0].line == 0


# ── Coverage: logging, stack ops, EOF handling ───────────


class TestLexerCoverageGaps:

    def test_log_simple(self, capsys, simple_instructions):
        lexer = Lexer(simple_instructions)
        lexer('hi', log=True)
        out = capsys.readouterr().out
        assert 'LEXICAL ANALYSIS' in out
        assert "I'm in state" in out

    def test_log_ignore_char(self, capsys, simple_instructions):
        lexer = Lexer(simple_instructions)
        lexer(' hi', log=True)
        out = capsys.readouterr().out
        assert 'unexpected, but can be ignored' in out

    def test_log_unexpected_error(self, capsys, simple_instructions):
        lexer = Lexer(simple_instructions)
        with pytest.raises(SyntaxError):
            lexer('x', log=True)
        out = capsys.readouterr().out
        assert "can't be ignored" in out

    def test_token_chars_all_ignorable(self):
        """If we're stuck mid-token but the accumulated chars are all
        ignorable, we should reset to state 0 instead of raising."""
        instructions = {
            '': {
                '': [' '],
                '0': {'[ a]': '1'},
                '1': {'b': '2'},
                '2': {'': ['AB']},
            }
        }
        lexer = Lexer(instructions)
        tokens = lexer(' ab')
        assert [t.name for t in tokens] == ['AB']

    def test_token_chars_all_ignorable_log(self, capsys):
        instructions = {
            '': {
                '': [' '],
                '0': {'[ a]': '1'},
                '1': {'b': '2'},
                '2': {'': ['AB']},
            }
        }
        lexer = Lexer(instructions)
        lexer(' ab', log=True)
        out = capsys.readouterr().out
        assert 'all recently read chars can be ignored' in out

    def test_log_list_action_finish(self, capsys, simple_instructions):
        """Triggering a list (finishing) action mid-stream."""
        lexer = Lexer(simple_instructions)
        lexer('hah', log=True)
        out = capsys.readouterr().out
        assert 'is finished' in out

    def test_log_stack_push_and_pop(self, capsys):
        """Mid-stream push and mid-stream pop of a mode should both log."""
        instructions = {
            'main': {
                '0': {'a': '1', 'z': '4'},
                '1': {'': ['A', 'sub']},
                '4': {'': ['Z']},
            },
            'sub': {
                '0': {'b': '1'},
                '1': {'': ['B', 1]},
            }
        }
        lexer = Lexer(instructions)
        tokens = lexer('abz', log=True)
        out = capsys.readouterr().out
        assert [t.name for t in tokens] == ['A', 'B', 'Z']
        assert 'on the top of the stack' in out
        assert 'Deleting' in out

    def test_stack_empty_via_large_pop(self, capsys):
        """A pop count larger than the stack size empties the stack
        and prints 'Emptying the stack'."""
        instructions = {
            'main': {
                '0': {'a': '1'},
                '1': {'': ['A', 'sub']},
            },
            'sub': {
                '0': {'b': '1'},
                '1': {'': ['B', 99]},
            }
        }
        lexer = Lexer(instructions)
        with pytest.raises(IndexError):
            lexer('abbx')
        out = capsys.readouterr().out
        assert 'Emptying the stack' in out

    def test_log_eof_final_token(self, capsys):
        instructions = {
            '': {
                '0': {'a': '1'},
                '1': {'a': '1', '': ['A']},
            }
        }
        lexer = Lexer(instructions)
        lexer('aaa', log=True)
        out = capsys.readouterr().out
        assert 'end of file' in out
        assert 'final token' in out

    def test_eof_non_list_tail_raises_type_error(self):
        """If the state's '' entry is a string (continuation, not a list),
        finishing at EOF should raise SyntaxError via the TypeError path."""
        instructions = {
            'm': {
                '0': {'a': '1'},
                '1': 'something',
            }
        }
        lexer = Lexer(instructions)
        with pytest.raises(SyntaxError, match='Unfinished token'):
            lexer('a')

    def test_unknown_state_raises(self):
        """A transition to a state that doesn't exist should raise
        IndexError with a helpful message."""
        instructions = {
            'm': {
                '0': {'a': 'nope'},
            }
        }
        lexer = Lexer(instructions)
        with pytest.raises((IndexError, KeyError)):
            lexer('aa')

    def test_partial_token_has_non_ignorable_chars(self):
        """If unexpected char is hit mid-token and the accumulated chars
        contain something non-ignorable, should raise."""
        instructions = {
            '': {
                '': [' '],
                '0': {'[ x]': '1'},
                '1': {'y': '2'},
                '2': {'': ['XY']},
            }
        }
        lexer = Lexer(instructions)
        with pytest.raises(SyntaxError, match='Unexpected character'):
            lexer('xz')

    def test_get_action_index_error_with_mode(self):
        """get_action should wrap IndexError with a useful message
        when a mode is set."""
        lexer = Lexer({'m': {'0': {}}})
        lexer.instructions = {'m': []}
        with pytest.raises(IndexError, match='Unknown state 0 in mode m'):
            lexer.get_action('m', 0, 'a')

    def test_get_action_index_error_without_mode(self):
        """get_action should wrap IndexError with a useful message
        even when mode is an empty string."""
        lexer = Lexer({'m': {'0': {}}})
        lexer.instructions = {'': []}
        with pytest.raises(IndexError, match='Unknown state 0'):
            lexer.get_action('', 0, 'a')
