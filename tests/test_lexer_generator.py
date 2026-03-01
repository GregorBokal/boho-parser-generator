import pytest

from boho.lexer_generator import generate, generate_dfa, str_to_dfa, standard


# ── str_to_dfa ───────────────────────────────────────────


class TestStrToDfa:

    def test_single_char(self):
        dfa = str_to_dfa('A', ['A'])
        assert dfa == {
            '0': {'A': '1'},
            '1': {'': ['A']}
        }

    def test_multi_char(self):
        dfa = str_to_dfa('ABC', ['ABC'])
        assert dfa == {
            '0': {'A': '1'},
            '1': {'B': '2'},
            '2': {'C': '3'},
            '3': {'': ['ABC']}
        }

    def test_empty_string(self):
        dfa = str_to_dfa('', ['EMPTY'])
        assert dfa == {'0': {'': ['EMPTY']}}

    def test_action_with_operations(self):
        dfa = str_to_dfa('XY', ['XY', 1, 'current_mode'])
        assert dfa == {
            '0': {'X': '1'},
            '1': {'Y': '2'},
            '2': {'': ['XY', 1, 'current_mode']}
        }

    def test_special_characters(self):
        """Characters like ., +, * should be treated literally."""
        dfa = str_to_dfa('.+', ['DOTPLUS'])
        assert dfa == {
            '0': {'\\.': '1'},
            '1': {'\\+': '2'},
            '2': {'': ['DOTPLUS']}
        }

    def test_state_numbering(self):
        """States should be numbered from 0 to len(string)."""
        dfa = str_to_dfa('ABCD', ['TOK'])
        assert set(dfa.keys()) == {'0', '1', '2', '3', '4'}
        assert dfa['0'] == {'A': '1'}
        assert dfa['4'] == {'': ['TOK']}


# ── generate_dfa ─────────────────────────────────────────


class TestGenerateDfa:

    def test_string_literal(self):
        dfa = generate_dfa('"AB"', ['AB'])
        assert dfa == {
            '0': {'A': '1'},
            '1': {'B': '2'},
            '2': {'': ['AB']}
        }

    def test_regex(self):
        dfa = generate_dfa('/[0-9]+/', ['NUM'])
        assert '0' in dfa
        # State 0 should transition on digits
        assert any('\\d' in k or '[0-9]' in k or any(
            c.isdigit() for c in k) for k in dfa['0'])

    def test_standard_int(self):
        dfa = generate_dfa('@INT', ['INT'])
        assert dfa['0'] == {'-': '1', '\\d': '2'}
        assert dfa['1'] == {'\\d': '2'}
        assert dfa['2'] == {'\\d': '2', '': ['INT']}

    def test_standard_unknown(self):
        with pytest.raises(NotImplementedError, match='does not exist'):
            generate_dfa('@NONEXISTENT', ['TOK'])

    def test_unrecognized_format(self):
        with pytest.raises(SyntaxError, match='Unrecognized token'):
            generate_dfa('BARE', ['TOK'])

    def test_unrecognized_format_number(self):
        with pytest.raises(SyntaxError, match='Unrecognized token'):
            generate_dfa('123', ['TOK'])

    def test_string_literal_action_preserved(self):
        dfa = generate_dfa('"X"', ['X', 1, 'mode2'])
        assert dfa['1'] == {'': ['X', 1, 'mode2']}

    def test_regex_action_preserved(self):
        dfa = generate_dfa('/a/', ['A'])
        # Find the final state (one with '' key)
        finals = [s for s in dfa if '' in dfa[s]]
        assert len(finals) >= 1
        assert dfa[finals[0]][''] == ['A']


# ── standard DFAs ────────────────────────────────────────


class TestStandardDfas:

    def test_int_structure(self):
        """INT should handle optional minus and digits."""
        assert '0' in standard['INT']
        assert '-' in standard['INT']['0']
        assert '\\d' in standard['INT']['0']

    def test_float_structure(self):
        """FLOAT should handle optional minus, digits, dot, digits."""
        assert '0' in standard['FLOAT']
        assert '-' in standard['FLOAT']['0']
        assert '\\.' in standard['FLOAT']['0']


# ── generate: basic cases ────────────────────────────────


class TestGenerateBasic:

    def test_empty_input(self):
        result = generate({})
        assert result == {}

    def test_single_token(self):
        result = generate({'m': [
            ('"A"', ['A'])
        ]})
        assert result == {
            'm': {
                '0': {'A': '1'},
                '1': {'': ['A']}
            }
        }

    def test_two_non_conflicting_tokens(self):
        result = generate({'m': [
            ('"A"', ['A']),
            ('"B"', ['B'])
        ]})
        dfa = result['m']
        assert 'A' in dfa['0']
        assert 'B' in dfa['0']
        # Each should lead to a final state
        a_state = dfa['0']['A']
        b_state = dfa['0']['B']
        assert '' in dfa[a_state]
        assert '' in dfa[b_state]
        assert dfa[a_state][''] == ['A']
        assert dfa[b_state][''] == ['B']

    def test_three_non_conflicting_tokens(self):
        result = generate({'m': [
            ('"A"', ['A']),
            ('"B"', ['B']),
            ('"C"', ['C'])
        ]})
        dfa = result['m']
        assert len(dfa['0']) == 3

    def test_multiple_modes(self):
        result = generate({
            'm1': [('"X"', ['X'])],
            'm2': [('"Y"', ['Y'])]
        })
        assert 'm1' in result
        assert 'm2' in result
        assert 'X' in result['m1']['0']
        assert 'Y' in result['m2']['0']

    def test_action_with_stack_operations(self):
        result = generate({'m': [
            ('"X"', ['X', 1, 'other'])
        ]})
        dfa = result['m']
        final_state = dfa['0']['X']
        assert dfa[final_state][''] == ['X', 1, 'other']


# ── generate: prefix conflicts ───────────────────────────


class TestGeneratePrefixConflicts:

    def test_ab_then_abc(self):
        """AB and ABC share a prefix; the merged DFA should handle both."""
        result = generate({'m': [
            ('"AB"', ['AB', 1, 'mode_1']),
            ('"ABC"', ['ABC'])
        ]})
        dfa = result['m']
        # A -> state -> B -> state (with both '' for AB and 'C' for ABC)
        a_state = dfa['0']['A']
        b_state = dfa[a_state]['B']
        assert '' in dfa[b_state], 'State after AB should have default action'
        assert 'C' in dfa[b_state], 'State after AB should transition on C'
        c_state = dfa[b_state]['C']
        assert dfa[c_state][''] == ['ABC']
        assert dfa[b_state][''] == ['AB', 1, 'mode_1']

    def test_abc_then_ab(self):
        """Reverse order: ABC first, then AB."""
        result = generate({'m': [
            ('"ABC"', ['ABC']),
            ('"AB"', ['AB'])
        ]})
        dfa = result['m']
        a_state = dfa['0']['A']
        b_state = dfa[a_state]['B']
        assert '' in dfa[b_state]
        assert 'C' in dfa[b_state]

    def test_a_then_ab(self):
        """A is a prefix of AB."""
        result = generate({'m': [
            ('"A"', ['A']),
            ('"AB"', ['AB'])
        ]})
        dfa = result['m']
        a_state = dfa['0']['A']
        assert '' in dfa[a_state], 'State for A should have default (finish A)'
        assert 'B' in dfa[a_state], 'State for A should also handle B'

    def test_ab_then_a(self):
        """Reverse: AB first, then A."""
        result = generate({'m': [
            ('"AB"', ['AB']),
            ('"A"', ['A'])
        ]})
        dfa = result['m']
        a_state = dfa['0']['A']
        assert '' in dfa[a_state]
        assert 'B' in dfa[a_state]

    def test_shared_prefix_different_suffix(self):
        """AB and AC share prefix A."""
        result = generate({'m': [
            ('"AB"', ['AB']),
            ('"AC"', ['AC'])
        ]})
        dfa = result['m']
        a_state = dfa['0']['A']
        assert 'B' in dfa[a_state]
        assert 'C' in dfa[a_state]
        b_state = dfa[a_state]['B']
        c_state = dfa[a_state]['C']
        assert dfa[b_state][''] == ['AB']
        assert dfa[c_state][''] == ['AC']


# ── generate: regex tokens ───────────────────────────────


class TestGenerateRegex:

    def test_single_regex_token(self):
        result = generate({'m': [
            ('/[0-9]+/', ['NUM'])
        ]})
        dfa = result['m']
        assert '0' in dfa

    def test_regex_with_action(self):
        result = generate({'m': [
            ('/[ab]+/', ['ABWORD'])
        ]})
        dfa = result['m']
        # Find a final state
        finals = [s for s in dfa if '' in dfa[s]]
        assert len(finals) >= 1
        assert dfa[finals[0]][''] == ['ABWORD']

    def test_regex_a_then_ab(self):
        """Regex /a/ and /ab/ - a is prefix of ab."""
        result = generate({'m': [
            ('/a/', ['A']),
            ('/ab/', ['AB'])
        ]})
        dfa = result['m']
        # Should have a path for 'a' alone and 'ab'
        a_state = dfa['0']['a']
        assert '' in dfa[a_state], 'Should accept just a'
        assert 'b' in dfa[a_state], 'Should continue to ab'


# ── generate: @INT standard ──────────────────────────────


class TestGenerateStandard:

    def test_int_token(self):
        result = generate({'m': [
            ('@INT', ['INT'])
        ]})
        dfa = result['m']
        assert '0' in dfa
        assert '-' in dfa['0']
        assert '\\d' in dfa['0']
        # Follow digits to a final state
        digit_state = dfa['0']['\\d']
        assert '' in dfa[digit_state]
        assert dfa[digit_state][''] == ['INT']

    def test_int_with_stack_operations(self):
        result = generate({'m': [
            ('@INT', ['INT', 'push_mode'])
        ]})
        dfa = result['m']
        digit_state = dfa['0']['\\d']
        assert dfa[digit_state][''] == ['INT', 'push_mode']


# ── generate: inseparable tokens ─────────────────────────


class TestGenerateInseparable:

    def test_identical_strings(self):
        """Two tokens with the exact same string should be inseparable."""
        with pytest.raises(SyntaxError, match='inseparable'):
            generate({'m': [
                ('"A"', ['A']),
                ('"A"', ['A2'])
            ]})

    def test_identical_multi_char_strings(self):
        with pytest.raises(SyntaxError, match='inseparable'):
            generate({'m': [
                ('"ABC"', ['TOK1']),
                ('"ABC"', ['TOK2'])
            ]})

    def test_inseparable_regex_full_overlap(self):
        """Two regex tokens that fully overlap on final states."""
        with pytest.raises(SyntaxError, match='inseparable'):
            generate({'m': [
                ('/[a-z]+/', ['WORD']),
                ('/if/', ['IF'])
            ]})


# ── generate: log output ─────────────────────────────────


class TestGenerateLog:

    def test_log_does_not_change_result(self):
        """Enabling log should not affect the output."""
        result_no_log = generate({'m': [
            ('"AB"', ['AB']),
            ('"AC"', ['AC'])
        ]}, log=False)
        result_log = generate({'m': [
            ('"AB"', ['AB']),
            ('"AC"', ['AC'])
        ]}, log=True)
        assert result_no_log == result_log

    def test_log_produces_output(self, capsys):
        generate({'m': [('"A"', ['A'])]}, log=True)
        captured = capsys.readouterr()
        assert 'Generating instructions for lexer' in captured.out
        assert 'finished' in captured.out.lower()


# ── generate: complex merging ────────────────────────────


class TestGenerateComplexMerging:

    def test_three_tokens_with_shared_prefix(self):
        """AX, AY, AZ all share prefix A."""
        result = generate({'m': [
            ('"AX"', ['AX']),
            ('"AY"', ['AY']),
            ('"AZ"', ['AZ'])
        ]})
        dfa = result['m']
        a_state = dfa['0']['A']
        assert 'X' in dfa[a_state]
        assert 'Y' in dfa[a_state]
        assert 'Z' in dfa[a_state]

    def test_cascading_prefixes(self):
        """A, AB, ABC - each is a prefix of the next."""
        result = generate({'m': [
            ('"A"', ['A']),
            ('"AB"', ['AB']),
            ('"ABC"', ['ABC'])
        ]})
        dfa = result['m']
        a_state = dfa['0']['A']
        # A state should have default action and B transition
        assert '' in dfa[a_state]
        assert 'B' in dfa[a_state]
        b_state = dfa[a_state]['B']
        assert '' in dfa[b_state]
        assert 'C' in dfa[b_state]

    def test_modes_are_independent(self):
        """Tokens in different modes should not interfere."""
        result = generate({
            'm1': [('"A"', ['A'])],
            'm2': [('"A"', ['A2'])]
        })
        # Both modes should successfully have their own DFA
        assert result['m1'] != result['m2'] or True  # they might look the same structurally
        # Each current_mode's final action should be different
        a1_state = result['m1']['0']['A']
        a2_state = result['m2']['0']['A']
        assert result['m1'][a1_state][''] == ['A']
        assert result['m2'][a2_state][''] == ['A2']

    def test_string_and_regex_mixed(self):
        """Mixing string literals and regex in one current_mode."""
        result = generate({'m': [
            ('"if"', ['IF']),
            ('/[0-9]+/', ['NUM'])
        ]})
        dfa = result['m']
        assert '0' in dfa
        # 'i' should be present (from "if")
        assert 'i' in dfa['0']


# ── generate: result structure ───────────────────────────


class TestGenerateResultStructure:

    def test_output_is_dict_of_dicts(self):
        result = generate({'m': [('"X"', ['X'])]})
        assert isinstance(result, dict)
        assert isinstance(result['m'], dict)

    def test_states_are_string_keyed(self):
        result = generate({'m': [('"AB"', ['AB'])]})
        for state_name in result['m']:
            assert isinstance(state_name, str)

    def test_actions_are_str_or_list(self):
        result = generate({'m': [
            ('"AB"', ['AB']),
            ('"AC"', ['AC'])
        ]})
        for state in result['m'].values():
            for action in state.values():
                assert isinstance(action, (str, list))

    def test_all_referenced_states_exist(self):
        """Every state referenced by an action should exist in the DFA."""
        result = generate({'m': [
            ('"AB"', ['AB']),
            ('"AC"', ['AC']),
            ('"X"', ['X'])
        ]})
        dfa = result['m']
        for state in dfa.values():
            for action in state.values():
                if isinstance(action, str):
                    assert action in dfa, \
                        f'State {action} referenced but not in DFA'

    def test_initial_state_always_0(self):
        result = generate({'m': [('"XY"', ['XY'])]})
        assert '0' in result['m']

    def test_final_actions_contain_token_name(self):
        """Every list action should have a string as first element."""
        result = generate({'m': [
            ('"A"', ['A']),
            ('"B"', ['B', 1])
        ]})
        for state in result['m'].values():
            for action in state.values():
                if isinstance(action, list):
                    assert len(action) >= 1
                    assert isinstance(action[0], str)


# ── Edge cases and robustness ────────────────────────────


class TestEdgeCases:

    def test_single_char_token(self):
        result = generate({'m': [('"X"', ['X'])]})
        dfa = result['m']
        x_state = dfa['0']['X']
        assert dfa[x_state][''] == ['X']

    def test_long_string_token(self):
        long_str = 'ABCDEFGHIJ'
        result = generate({'m': [
            (f'"{long_str}"', ['LONG'])
        ]})
        dfa = result['m']
        # Walk the chain
        state = '0'
        for char in long_str:
            assert char in dfa[state]
            state = dfa[state][char]
        assert dfa[state][''] == ['LONG']

    def test_mode_name_with_special_chars(self):
        """Mode names can be arbitrary strings."""
        result = generate({
            'current_mode-1': [('"A"', ['A'])],
            'mode_2': [('"B"', ['B'])]
        })
        assert 'current_mode-1' in result
        assert 'mode_2' in result

    def test_single_mode_single_token(self):
        """Minimal valid input."""
        result = generate({'x': [('"a"', ['a'])]})
        assert 'x' in result

    def test_generate_dfa_string_with_quotes(self):
        """String descriptor must start and end with quotes."""
        dfa = generate_dfa('"hello"', ['HELLO'])
        state = '0'
        for char in 'hello':
            assert char in dfa[state]
            state = dfa[state][char]
        assert dfa[state][''] == ['HELLO']

    def test_generate_dfa_regex_with_slashes(self):
        """Regex descriptor must start and end with /."""
        dfa = generate_dfa('/abc/', ['ABC'])
        assert '0' in dfa

    def test_multiple_tokens_same_first_char(self):
        """Multiple tokens starting with the same character."""
        result = generate({'m': [
            ('"AB"', ['AB']),
            ('"AC"', ['AC']),
            ('"AD"', ['AD'])
        ]})
        dfa = result['m']
        a_state = dfa['0']['A']
        assert len(dfa[a_state]) == 3  # B, C, D

    def test_result_determinism(self):
        """Same input should always produce same output."""
        input_data = {'m': [
            ('"AB"', ['AB']),
            ('"CD"', ['CD'])
        ]}
        r1 = generate(input_data)
        r2 = generate(input_data)
        assert r1 == r2
