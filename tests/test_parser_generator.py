import pytest

from boho.parser_generator import generate, LR1ParserGenerator, START, END
from boho.objects import LR1Item


# ── Fixtures ──────────────────────────────────────────────


@pytest.fixture
def arithmetic_grammar():
    """Simple arithmetic: start -> start "+" product | product
                          product -> product "*" atom | atom
                          atom -> @INT"""
    return {
        'start': [
            ('start', '"+"', 'product'),
            ('product',)
        ],
        'product': [
            ('product', '"*"', 'atom'),
            ('atom',)
        ],
        'atom': [('@INT',)]
    }


@pytest.fixture
def single_production_grammar():
    """Minimal grammar: start -> A"""
    return {
        'start': [('A',)]
    }


@pytest.fixture
def epsilon_grammar():
    """Grammar with epsilon production: start -> A maybe
                                        maybe -> B | (empty)"""
    return {
        'start': [('A', 'maybe')],
        'maybe': [('B',), ()]
    }


@pytest.fixture
def generator():
    return LR1ParserGenerator()


# ── generate: basic usage ────────────────────────────────


class TestGenerateBasic:

    def test_returns_dict(self, arithmetic_grammar):
        result = generate(arithmetic_grammar)
        assert isinstance(result, dict)

    def test_example_grammar_produces_table(self, arithmetic_grammar):
        result = generate(arithmetic_grammar)
        assert len(result) > 0

    def test_single_production(self, single_production_grammar):
        result = generate(single_production_grammar)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_table_has_accept_action(self, arithmetic_grammar):
        """There should be at least one True (accept) action."""
        result = generate(arithmetic_grammar)
        has_accept = any(
            True in state.values()
            for state in result.values()
        )
        assert has_accept

    def test_table_has_shift_actions(self, arithmetic_grammar):
        """There should be string (shift/goto) actions."""
        result = generate(arithmetic_grammar)
        has_shift = any(
            any(isinstance(v, str) for v in state.values())
            for state in result.values()
        )
        assert has_shift

    def test_table_has_reduce_actions(self, arithmetic_grammar):
        """There should be tuple (reduce) actions."""
        result = generate(arithmetic_grammar)
        has_reduce = any(
            any(isinstance(v, tuple) for v in state.values())
            for state in result.values()
        )
        assert has_reduce

    def test_accept_action_is_on_end_symbol(self, arithmetic_grammar):
        """The accept action should be triggered by the END ($) symbol."""
        result = generate(arithmetic_grammar)
        for state in result.values():
            for symbol, action in state.items():
                if action is True:
                    assert symbol == END


# ── generate: start parameter ────────────────────────────


class TestGenerateStartParam:

    def test_default_start(self):
        grammar = {'start': [('A',)]}
        result = generate(grammar)
        assert isinstance(result, dict)

    def test_custom_start(self):
        grammar = {'expr': [('A',)]}
        result = generate(grammar, start='expr')
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_custom_start_produces_correct_table(self):
        grammar = {'my_start': [('X',)]}
        result = generate(grammar, start='my_start')
        has_accept = any(
            True in state.values()
            for state in result.values()
        )
        assert has_accept


# ── generate: kind parameter ─────────────────────────────


class TestGenerateKindParam:

    def test_lr1_kind(self, arithmetic_grammar):
        result = generate(arithmetic_grammar, kind='LR1')
        assert isinstance(result, dict)

    def test_unknown_kind_raises(self, arithmetic_grammar):
        with pytest.raises(NotImplementedError, match='is not implemented'):
            generate(arithmetic_grammar, kind='LALR')

    def test_unknown_kind_suggests_alternatives(self, arithmetic_grammar):
        with pytest.raises(NotImplementedError, match='LR1'):
            generate(arithmetic_grammar, kind='SLR')


# ── generate: log parameter ─────────────────────────────


class TestGenerateLog:

    def test_log_does_not_change_result(self):
        def make_grammar():
            return {
                'start': [('start', '"+"', 'product'), ('product',)],
                'product': [('product', '"*"', 'atom'), ('atom',)],
                'atom': [('@INT',)]
            }
        result_no_log = generate(make_grammar(), log=False)
        result_log = generate(make_grammar(), log=True)
        assert result_no_log == result_log

    def test_log_produces_output(self, arithmetic_grammar, capsys):
        generate(arithmetic_grammar, log=True)
        captured = capsys.readouterr()
        assert 'Generating instructions for the parser' in captured.out

    def test_log_shows_grammar(self, arithmetic_grammar, capsys):
        generate(arithmetic_grammar, log=True)
        captured = capsys.readouterr()
        assert 'the following grammar' in captured.out

    def test_log_shows_start_item(self, arithmetic_grammar, capsys):
        generate(arithmetic_grammar, log=True)
        captured = capsys.readouterr()
        assert 'start item' in captured.out

    def test_log_shows_finished(self, arithmetic_grammar, capsys):
        generate(arithmetic_grammar, log=True)
        captured = capsys.readouterr()
        assert 'finished' in captured.out

    def test_log_shows_state_scanning(self, arithmetic_grammar, capsys):
        generate(arithmetic_grammar, log=True)
        captured = capsys.readouterr()
        assert 'scan the state' in captured.out

    def test_log_shows_shifts(self, arithmetic_grammar, capsys):
        generate(arithmetic_grammar, log=True)
        captured = capsys.readouterr()
        assert 'moves us' in captured.out

    def test_log_shows_reduce(self, arithmetic_grammar, capsys):
        generate(arithmetic_grammar, log=True)
        captured = capsys.readouterr()
        assert 'reduce' in captured.out

    def test_log_shows_finish(self, arithmetic_grammar, capsys):
        generate(arithmetic_grammar, log=True)
        captured = capsys.readouterr()
        assert 'finish' in captured.out


# ── generate: augmented start ────────────────────────────


class TestAugmentedStart:

    def test_reserved_start_symbol_raises(self):
        """Using S' in the grammar should raise an AssertionError."""
        grammar = {START: [('A',)], 'other': [('B',)]}
        with pytest.raises(AssertionError):
            generate(grammar, start='other')


# ── generate: epsilon productions ────────────────────────


class TestEpsilonProductions:

    def test_epsilon_grammar_produces_table(self, epsilon_grammar):
        result = generate(epsilon_grammar)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_epsilon_produces_reduce_of_length_zero(self, epsilon_grammar):
        """Grammar with epsilon production () should produce a reduce of length 0."""
        result = generate(epsilon_grammar)
        has_zero_reduce = any(
            any(isinstance(v, tuple) and v[0] == 0
                for v in state.values())
            for state in result.values()
        )
        assert has_zero_reduce


# ── generate: recursive grammars ─────────────────────────


class TestRecursiveGrammars:

    def test_left_recursive(self):
        grammar = {
            'start': [
                ('start', '"+"', 'A'),
                ('A',)
            ]
        }
        result = generate(grammar)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_right_recursive(self):
        grammar = {
            'start': [
                ('A', '"+"', 'start'),
                ('A',)
            ]
        }
        result = generate(grammar)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_deeply_nested(self):
        grammar = {
            'start': [('a',)],
            'a': [('b',)],
            'b': [('c',)],
            'c': [('X',)]
        }
        result = generate(grammar)
        assert isinstance(result, dict)


# ── generate: multiple productions ───────────────────────


class TestMultipleProductions:

    def test_three_alternatives(self):
        grammar = {
            'start': [
                ('A',),
                ('B',),
                ('C',)
            ]
        }
        result = generate(grammar)
        assert isinstance(result, dict)

    def test_mixed_length_productions(self):
        grammar = {
            'start': [
                ('A', 'B', 'C'),
                ('D',)
            ]
        }
        result = generate(grammar)
        assert isinstance(result, dict)

    def test_single_vs_multiple_symbol_productions(self):
        grammar = {
            'start': [
                ('A', '"+"', 'B'),
                ('A',)
            ]
        }
        result = generate(grammar)
        has_reduce = any(
            any(isinstance(v, tuple) for v in state.values())
            for state in result.values()
        )
        assert has_reduce


# ── Table structure ──────────────────────────────────────


class TestTableStructure:

    def test_states_are_string_keyed(self, arithmetic_grammar):
        result = generate(arithmetic_grammar)
        for key in result:
            assert isinstance(key, str)

    def test_actions_are_correct_types(self, arithmetic_grammar):
        result = generate(arithmetic_grammar)
        for state in result.values():
            for action in state.values():
                assert isinstance(action, (str, tuple, bool))

    def test_reduce_actions_are_int_str_tuples(self, arithmetic_grammar):
        result = generate(arithmetic_grammar)
        for state in result.values():
            for action in state.values():
                if isinstance(action, tuple):
                    assert len(action) == 2
                    assert isinstance(action[0], int)
                    assert isinstance(action[1], str)

    def test_shift_targets_exist_as_states(self, arithmetic_grammar):
        """Every shift target should be a valid state in the table."""
        result = generate(arithmetic_grammar)
        for state in result.values():
            for action in state.values():
                if isinstance(action, str):
                    assert action in result

    def test_initial_state_is_zero(self, arithmetic_grammar):
        result = generate(arithmetic_grammar)
        assert '0' in result

    def test_exactly_one_accept(self, arithmetic_grammar):
        """There should be exactly one accept action (True)."""
        result = generate(arithmetic_grammar)
        accept_count = sum(
            1 for state in result.values()
            for action in state.values()
            if action is True
        )
        assert accept_count == 1


# ── LR1ParserGenerator class ────────────────────────────


class TestLR1ParserGeneratorClass:

    def test_init_defaults(self, generator):
        assert generator.grammar == {}
        assert generator.table == {}
        assert generator.conflicts == {}
        assert generator.log is False

    def test_callable(self, generator, single_production_grammar):
        result = generator(single_production_grammar)
        assert isinstance(result, dict)

    def test_reusable(self, generator):
        g1 = {'start': [('A',)]}
        g2 = {'start': [('B',)]}
        r1 = generator(g1)
        r2 = generator(g2)
        assert isinstance(r1, dict)
        assert isinstance(r2, dict)


# ── LR1Item ──────────────────────────────────────────────


class TestLR1Item:

    def test_repr(self):
        item = LR1Item('E', ('E', '+', 'T'), 1, '$')
        assert repr(item) == "[E -> E • + T, $]"

    def test_repr_at_start(self):
        item = LR1Item('E', ('E', '+', 'T'), 0, '$')
        assert repr(item) == "[E ->  • E + T, $]"

    def test_repr_at_end(self):
        item = LR1Item('E', ('E', '+', 'T'), 3, '$')
        assert repr(item) == "[E -> E + T • , $]"

    def test_is_complete_false(self):
        item = LR1Item('E', ('E', '+', 'T'), 1, '$')
        assert not item.is_complete

    def test_is_complete_true(self):
        item = LR1Item('E', ('E', '+', 'T'), 3, '$')
        assert item.is_complete

    def test_next_symbol(self):
        item = LR1Item('E', ('E', '+', 'T'), 1, '$')
        assert item.next_symbol == '+'

    def test_next_symbol_at_end(self):
        item = LR1Item('E', ('E', '+', 'T'), 3, '$')
        assert item.next_symbol is None

    def test_next_item(self):
        item = LR1Item('E', ('E', '+', 'T'), 1, '$')
        next_item = item.next_item()
        assert next_item.dot == 2
        assert next_item.head == 'E'
        assert next_item.body == ('E', '+', 'T')
        assert next_item.lookahead == '$'

    def test_frozen_hashable(self):
        item = LR1Item('E', ('E',), 0, '$')
        s = {item}
        assert item in s

    def test_equality(self):
        a = LR1Item('E', ('E',), 0, '$')
        b = LR1Item('E', ('E',), 0, '$')
        assert a == b

    def test_inequality_different_lookahead(self):
        a = LR1Item('E', ('E',), 0, '$')
        b = LR1Item('E', ('E',), 0, '+')
        assert a != b


# ── Closure ──────────────────────────────────────────────


class TestClosure:

    def test_closure_adds_items(self, generator, arithmetic_grammar):
        generator.grammar = dict(arithmetic_grammar)
        generator.grammar[START] = [('start',)]
        item = LR1Item(START, ('start',), 0, END)
        closure = generator.closure([item])
        assert len(closure) > 1

    def test_closure_no_duplicates(self, generator, arithmetic_grammar):
        generator.grammar = dict(arithmetic_grammar)
        generator.grammar[START] = [('start',)]
        item = LR1Item(START, ('start',), 0, END)
        closure = generator.closure([item])
        assert len(closure) == len(set(tuple(c.__dict__.items()) for c in closure))

    def test_closure_of_terminal(self, generator, single_production_grammar):
        """Closure of an item whose next symbol is a terminal should not expand."""
        generator.grammar = dict(single_production_grammar)
        generator.grammar[START] = [('start',)]
        item = LR1Item('start', ('A',), 0, END)
        closure = generator.closure([item])
        assert len(closure) == 1


# ── Goto ─────────────────────────────────────────────────


class TestGoto:

    def test_goto_produces_items(self, generator, arithmetic_grammar):
        generator.grammar = dict(arithmetic_grammar)
        generator.grammar[START] = [('start',)]
        start_item = LR1Item(START, ('start',), 0, END)
        start_state = generator.closure([start_item])
        goto_state = generator.goto(start_state, 'start')
        assert len(goto_state) > 0

    def test_goto_advances_dot(self, generator, single_production_grammar):
        generator.grammar = dict(single_production_grammar)
        generator.grammar[START] = [('start',)]
        item = LR1Item('start', ('A',), 0, END)
        goto_state = generator.goto([item], 'A')
        assert any(i.dot == 1 for i in goto_state)


# ── First set ────────────────────────────────────────────


class TestFirst:

    def test_first_of_terminal(self, generator, arithmetic_grammar):
        generator.grammar = dict(arithmetic_grammar)
        generator.grammar[START] = [('start',)]
        result = generator.first(('@INT',))
        assert '@INT' in result

    def test_first_of_nonterminal(self, generator, arithmetic_grammar):
        generator.grammar = dict(arithmetic_grammar)
        generator.grammar[START] = [('start',)]
        generator.compute_first_sets()
        result = generator.first(('atom',))
        assert '@INT' in result

    def test_first_of_epsilon_nonterminal(self, generator, epsilon_grammar):
        generator.grammar = dict(epsilon_grammar)
        generator.grammar[START] = [('start',)]
        generator.compute_first_sets()
        result = generator.first(('maybe',))
        assert 'B' in result
        assert '' in result

    def test_first_skips_epsilon(self, generator):
        grammar = {
            'start': [('A', 'B')],
            'A': [()],
            'B': [('X',)],
            START: [('start',)]
        }
        generator.grammar = grammar
        generator.compute_first_sets()
        result = generator.first(('A', 'B'))
        assert 'X' in result


# ── Conflict detection ───────────────────────────────────


class TestConflicts:

    def test_ambiguous_grammar_detects_conflict(self):
        """An ambiguous grammar should produce conflicts."""
        grammar = {
            'start': [
                ('start', '"+"', 'start'),
                ('A',)
            ]
        }
        gen = LR1ParserGenerator()
        gen(grammar)
        assert len(gen.conflicts) > 0

    def test_conflict_message_mentions_type(self):
        grammar = {
            'start': [
                ('start', '"+"', 'start'),
                ('A',)
            ]
        }
        gen = LR1ParserGenerator()
        gen(grammar)
        messages = list(gen.conflicts.values())
        assert any('conflict' in m.lower() for m in messages)

    def test_shift_reduce_conflict_logged(self, capsys):
        grammar = {
            'start': [
                ('start', '"+"', 'start'),
                ('A',)
            ]
        }
        gen = LR1ParserGenerator()
        gen(grammar, log=True)
        captured = capsys.readouterr()
        assert 'conflict' in captured.out.lower()

    def test_shift_reduce_shift_wins(self):
        """In a shift-reduce conflict, shift should win."""
        grammar = {
            'start': [
                ('start', '"+"', 'start'),
                ('A',)
            ]
        }
        gen = LR1ParserGenerator()
        result = gen(grammar)
        # Find the conflicting state/symbol
        for (state, symbol), msg in gen.conflicts.items():
            action = result[state][symbol]
            # Shift action is a string (goto state)
            assert isinstance(action, str), \
                "Shift should win in shift-reduce conflict"

    def test_no_conflicts_for_unambiguous_grammar(self, arithmetic_grammar):
        gen = LR1ParserGenerator()
        gen(arithmetic_grammar)
        assert len(gen.conflicts) == 0


# ── Determinism ──────────────────────────────────────────


class TestDeterminism:

    def test_same_input_same_output(self):
        def make_grammar():
            return {
                'start': [('start', '"+"', 'product'), ('product',)],
                'product': [('product', '"*"', 'atom'), ('atom',)],
                'atom': [('@INT',)]
            }
        r1 = generate(make_grammar())
        r2 = generate(make_grammar())
        assert r1 == r2

    def test_different_grammars_different_output(self):
        g1 = {'start': [('A',)]}
        g2 = {'start': [('B',)]}
        r1 = generate(g1)
        r2 = generate(g2)
        assert r1 != r2


# ── Edge cases ───────────────────────────────────────────


class TestEdgeCases:

    def test_single_terminal_grammar(self):
        grammar = {'start': [('X',)]}
        result = generate(grammar)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_many_alternatives(self):
        grammar = {
            'start': [(chr(ord('A') + i),) for i in range(10)]
        }
        result = generate(grammar)
        assert isinstance(result, dict)

    def test_long_production(self):
        grammar = {
            'start': [('A', 'B', 'C', 'D', 'E')]
        }
        result = generate(grammar)
        has_reduce_5 = any(
            any(isinstance(v, tuple) and v[0] == 5
                for v in state.values())
            for state in result.values()
        )
        assert has_reduce_5

    def test_single_symbol_reduce_length(self):
        grammar = {'start': [('A',)]}
        result = generate(grammar)
        has_reduce_1 = any(
            any(isinstance(v, tuple) and v[0] == 1
                for v in state.values())
            for state in result.values()
        )
        assert has_reduce_1

    def test_multiple_nonterminals(self):
        grammar = {
            'start': [('a', 'b')],
            'a': [('X',)],
            'b': [('Y',)]
        }
        result = generate(grammar)
        assert isinstance(result, dict)

    def test_nonterminal_names_with_underscores(self):
        grammar = {
            'start': [('_my_rule',)],
            '_my_rule': [('A',)]
        }
        result = generate(grammar)
        assert isinstance(result, dict)

    def test_terminal_names_with_quotes(self):
        """Terminals like '"+"' should be handled normally."""
        grammar = {
            'start': [('A', '"+"', 'A')]
        }
        result = generate(grammar)
        assert isinstance(result, dict)

    def test_terminal_names_with_at(self):
        """Standard terminals like '@INT' treated as terminals."""
        grammar = {
            'start': [('@INT',)]
        }
        result = generate(grammar)
        assert isinstance(result, dict)


# ── Integration with example ─────────────────────────────


class TestExampleIntegration:

    def test_example_grammar(self):
        """The grammar from examples/parser_generator.py should work."""
        grammar = {
            'start': [
                ('start', '"+"', 'product'),
                ('product',)
            ],
            'product': [
                ('product', '"*"', 'atom'),
                ('atom',)
            ],
            'atom': [('@INT',)]
        }
        result = generate(grammar)
        assert isinstance(result, dict)
        assert '0' in result
        has_accept = any(
            True in state.values()
            for state in result.values()
        )
        assert has_accept

    def test_example_grammar_with_log(self, capsys):
        grammar = {
            'start': [
                ('start', '"+"', 'product'),
                ('product',)
            ],
            'product': [
                ('product', '"*"', 'atom'),
                ('atom',)
            ],
            'atom': [('@INT',)]
        }
        result = generate(grammar, log=True)
        captured = capsys.readouterr()
        assert len(captured.out) > 0
        assert isinstance(result, dict)


# ── Coverage: first/action edge cases ────────────────────


class TestCoverageGaps:

    def test_first_all_epsilon_production(self, generator):
        """A production whose every symbol is nullable should add ''
        to the first set of its nonterminal."""
        grammar = {
            'start': [('A', 'B')],
            'A': [()],
            'B': [()],
        }
        generator.grammar = dict(grammar)
        generator.grammar[START] = [('start',)]
        generator.compute_first_sets()
        assert '' in generator.first_cache['start']

    def test_shift_reduce_existing_shift(self):
        """Shift installed first, then a reduce tries to overwrite —
        hits the branch where existing is a goto (str) and action is reduce."""
        gen = LR1ParserGenerator()
        gen.action('0', 'X', '1')
        gen.action('0', 'X', (1, 'a'))
        assert ('0', 'X') in gen.conflicts
        assert 'Shift-reduce' in gen.conflicts[('0', 'X')]
        assert gen.table['0']['X'] == '1'

    def test_unknown_conflict_with_bool_existing(self):
        """If an accept action (bool) already exists at a (state, symbol)
        and a different action tries to overwrite, conflict is 'Unknown'."""
        gen = LR1ParserGenerator()
        gen.action('0', '$', True)
        gen.action('0', '$', '1')
        assert ('0', '$') in gen.conflicts
        assert 'Unknown' in gen.conflicts[('0', '$')]

    def test_reduce_reduce_conflict_logged(self, capsys):
        """A reduce-reduce conflict should be detected and logged
        with the 'first action wins' message."""
        grammar = {
            'start': [('a',), ('b',)],
            'a': [('X',)],
            'b': [('X',)],
        }
        gen = LR1ParserGenerator()
        gen(grammar, log=True)
        captured = capsys.readouterr()
        assert any('Reduce-reduce' in msg for msg in gen.conflicts.values())
        assert 'first action wins' in captured.out
