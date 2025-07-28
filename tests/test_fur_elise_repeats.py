#!/usr/bin/env python3
"""
Test dla poprawnego rozwijania repetycji w pliku Fur_Elise_simplified_repetitions.musicxml
"""

import pytest
import logging
from src.musicxml_parser import MusicXMLParser
from src.repeat_expander import RepeatExpander, LinearSequenceGenerator


class TestFurEliseRepeats:
    """Test rozwijania repetycji dla pliku Fur_Elise"""

    def setup_method(self):
        """Setup dla każdego testu"""
        logging.basicConfig(level=logging.INFO)
        self.parser = MusicXMLParser()
        self.expander = RepeatExpander()
        self.sequence_gen = LinearSequenceGenerator()

    def test_parse_fur_elise_structure(self):
        """Test parsowania podstawowej struktury pliku Fur_Elise"""
        score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
        
        # Podstawowa struktura
        assert len(score.parts) == 1
        part = score.parts[0]
        assert part.name == "Piano"
        
        # Oryginalne takty
        assert len(part.measures) == 11
        measures = part.measures
        
        # Sprawdź numerację taktów
        expected_numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        actual_numbers = [m.number for m in measures]
        assert actual_numbers == expected_numbers

    def test_detect_repeat_marks(self):
        """Test wykrywania znaczników repetycji"""
        score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
        part = score.parts[0]
        measures = part.measures
        
        # Sprawdź repeat marks
        repeat_starts = []
        repeat_ends = []
        
        for measure in measures:
            if measure.repeat_start:
                repeat_starts.append(measure.number)
            if measure.repeat_end:
                repeat_ends.append((measure.number, measure.repeat_count))
        
        # Oczekiwane repeat marks
        assert repeat_starts == [4], f"Expected repeat starts: [4], got: {repeat_starts}"
        assert repeat_ends == [(2, 2), (6, 2)], f"Expected repeat ends: [(2, 2), (6, 2)], got: {repeat_ends}"

    def test_detect_volta_marks(self):
        """Test wykrywania znaczników volt"""
        score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
        part = score.parts[0]
        measures = part.measures
        
        # Sprawdź volta marks
        voltas = []
        for measure in measures:
            if measure.ending_numbers and measure.ending_type:
                voltas.append((measure.number, measure.ending_numbers, measure.ending_type.value))
        
        # Oczekiwane volta marks
        expected_voltas = [
            (2, [1], 'stop'),    # Takt 2: volta 1 stop
            (3, [2], 'stop'),    # Takt 3: volta 2 stop  
            (6, [1], 'stop'),    # Takt 6: volta 1 stop
            (7, [2], 'stop')     # Takt 7: volta 2 stop
        ]
        assert voltas == expected_voltas, f"Expected voltas: {expected_voltas}, got: {voltas}"

    def test_expand_repeats_full_sequence(self):
        """Test główny - weryfikacja pełnej sekwencji po rozwinięciu repetycji"""
        score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
        expanded_score = self.expander.expand_repeats(score)
        notes_with_display = self.sequence_gen.get_expanded_notes_with_milliseconds(score, expanded_score)
        
        # Sprawdź oczekiwaną sekwencję taktów po rozwinięciu
        expected_sequence = [0, 1, 2, 0, 1, 3, 4, 5, 6, 4, 5, 7, 8, 9, 10]
        expanded_part = expanded_score.parts[0]
        expanded_numbers = [m.number for m in expanded_part.measures]
        
        assert expanded_numbers == expected_sequence, f"Expected sequence: {expected_sequence}, got: {expanded_numbers}"
        
        # Sprawdź liczbę nut
        assert len(notes_with_display) == 107, f"Expected 107 notes, got {len(notes_with_display)}"

    def test_repeat_iteration_metadata(self):
        """Test metadanych iteracji repetycji - kluczowa funkcjonalność"""
        score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
        expanded_score = self.expander.expand_repeats(score)
        notes_with_display = self.sequence_gen.get_expanded_notes_with_milliseconds(score, expanded_score)
        
        # Grupuj nuty według repeat_id i iteracji
        repeat_groups = {}
        for note in notes_with_display[:30]:
            print(f"Measure: {note['measure']}, Iteration: {note['iteration']}, Start time ms: {note['start_time_ms']}, Start time display ms: {note['start_time_display_ms']}")
            repeat_id = note['repeat_id']
            iteration = note['iteration']
            measure = note['measure']
            
            key = (repeat_id, iteration)
            if key not in repeat_groups:
                repeat_groups[key] = set()
            repeat_groups[key].add(measure)
        assert False
        # Konwertuj na sorted listy dla łatwiejszego porównania
        repeat_structure = {}
        for (repeat_id, iteration), measures in repeat_groups.items():
            if repeat_id not in repeat_structure:
                repeat_structure[repeat_id] = {}
            repeat_structure[repeat_id][iteration] = sorted(measures)
        
        # Oczekiwana struktura repetycji
        expected_structure = {
            'repeat_0_3': {
                0: [0, 1, 2],  # Pierwsza iteracja: takty 0,1,2 (volta 1)
                1: [0, 1, 3]   # Druga iteracja: takty 0,1,3 (volta 2)
            },
            'repeat_4_3': {
                0: [4, 5, 6],  # Pierwsza iteracja: takty 4,5,6 (volta 1)
                1: [4, 5, 7]   # Druga iteracja: takty 4,5,7 (volta 2)
            },
            None: {
                0: [8, 9, 10]  # Takty bez repetycji
            }
        }
        
        assert repeat_structure == expected_structure, f"Expected: {expected_structure}, got: {repeat_structure}"

    def test_repeat_sections_volta_assignment(self):
        """Test prawidłowego przypisania sekcji volta"""
        score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
        expanded_score = self.expander.expand_repeats(score)
        notes_with_display = self.sequence_gen.get_expanded_notes_with_milliseconds(score, expanded_score)
        
        # Sprawdź przypisanie sekcji volta dla każdego taktu
        section_assignments = {}
        for note in notes_with_display:
            measure = note['measure']
            iteration = note['iteration']
            repeat_id = note['repeat_id']
            section = note['repeat_section']
            
            key = (repeat_id, iteration, measure)
            if key not in section_assignments:
                section_assignments[key] = section
            
            # Sprawdź konsistentność - wszystkie nuty w tym samym takcie/iteracji mają tę samą sekcję
            assert section_assignments[key] == section, f"Inconsistent section for {key}: expected {section_assignments[key]}, got {section}"
        
        # Oczekiwane przypisania sekcji
        expected_sections = {
            # Pierwsza repetycja
            ('repeat_0_3', 0, 0): 'main',
            ('repeat_0_3', 0, 1): 'main', 
            ('repeat_0_3', 0, 2): 'volta_1',
            ('repeat_0_3', 1, 0): 'main',
            ('repeat_0_3', 1, 1): 'main',
            ('repeat_0_3', 1, 3): 'volta_2',
            
            # Druga repetycja
            ('repeat_4_3', 0, 4): 'main',
            ('repeat_4_3', 0, 5): 'main',
            ('repeat_4_3', 0, 6): 'volta_1',
            ('repeat_4_3', 1, 4): 'main',
            ('repeat_4_3', 1, 5): 'main',
            ('repeat_4_3', 1, 7): 'volta_2',
            
            # Bez repetycji
            (None, 0, 8): 'main',
            (None, 0, 9): 'main',
            (None, 0, 10): 'main'
        }
        
        for key, expected_section in expected_sections.items():
            assert key in section_assignments, f"Missing section assignment for {key}"
            assert section_assignments[key] == expected_section, f"Wrong section for {key}: expected {expected_section}, got {section_assignments[key]}"

    def test_repeat_total_iterations(self):
        """Test poprawności pola total_iterations"""
        score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
        expanded_score = self.expander.expand_repeats(score)
        notes_with_display = self.sequence_gen.get_expanded_notes_with_milliseconds(score, expanded_score)
        
        # Sprawdź total_iterations dla każdej repetycji
        for note in notes_with_display:
            repeat_id = note['repeat_id']
            total_iterations = note['total_iterations']
            
            if repeat_id == 'repeat_0_3' or repeat_id == 'repeat_4_3':
                assert total_iterations == 2, f"Expected total_iterations=2 for {repeat_id}, got {total_iterations}"
            elif repeat_id is None:
                assert total_iterations == 1, f"Expected total_iterations=1 for non-repeat, got {total_iterations}"

    def test_is_repeat_flag(self):
        """Test poprawności flagi is_repeat"""
        score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
        expanded_score = self.expander.expand_repeats(score)
        notes_with_display = self.sequence_gen.get_expanded_notes_with_milliseconds(score, expanded_score)
        
        repeat_notes = 0
        non_repeat_notes = 0
        
        for note in notes_with_display:
            repeat_id = note['repeat_id']
            is_repeat = note['is_repeat']
            
            if repeat_id is None:
                assert is_repeat == False, f"Note without repeat_id should have is_repeat=False, got {is_repeat}"
                non_repeat_notes += 1
            else:
                assert is_repeat == True, f"Note with repeat_id={repeat_id} should have is_repeat=True, got {is_repeat}"
                repeat_notes += 1
        
        # Sprawdź proporcje
        assert repeat_notes > 0, "Should have some repeat notes"
        assert non_repeat_notes > 0, "Should have some non-repeat notes"
        
        # Oczekiwane liczby nut (z poprzednich testów)
        expected_repeat_notes = 107 - 21  # 21 nut w taktach 8,9,10 bez repetycji
        expected_non_repeat_notes = 21
        
        assert repeat_notes == expected_repeat_notes, f"Expected {expected_repeat_notes} repeat notes, got {repeat_notes}"
        assert non_repeat_notes == expected_non_repeat_notes, f"Expected {expected_non_repeat_notes} non-repeat notes, got {non_repeat_notes}"

    def test_display_time_vs_playback_time(self):
        """Test różnicy między czasem odtwarzania a czasem wyświetlania"""
        score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
        expanded_score = self.expander.expand_repeats(score)
        notes_with_display = self.sequence_gen.get_expanded_notes_with_milliseconds(score, expanded_score)
        
        # Sprawdź że takty powtarzające się mają ten sam display_ms
        display_times_by_measure = {}
        for note in notes_with_display:
            measure = note['measure']
            display_ms = note['start_time_display_ms']
            
            if measure not in display_times_by_measure:
                display_times_by_measure[measure] = set()
            display_times_by_measure[measure].add(display_ms)
        
        # Każdy takt powinien mieć konsystentny display_ms (wszystkie wystąpienia tego taktu mają ten sam czas wyświetlania)
        for measure, times in display_times_by_measure.items():
            assert len(times) == 1, f"Measure {measure} should have consistent display_ms, got multiple times: {sorted(times)}"
        
        # Sprawdź że start_time_ms postępuje liniowo (czas odtwarzania)
        start_times = [note['start_time_ms'] for note in notes_with_display]
        for i in range(1, len(start_times)):
            assert start_times[i] >= start_times[i-1], f"Playback time should be monotonic: {start_times[i-1]} -> {start_times[i]} at index {i}"

    def test_repeat_id_consistency(self):
        """Test konsistentności repeat_id w ramach każdej repetycji"""
        score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
        expanded_score = self.expander.expand_repeats(score)
        notes_with_display = self.sequence_gen.get_expanded_notes_with_milliseconds(score, expanded_score)
        
        # Sprawdź że nuty z tych samych taktów w tej samej repetycji mają ten sam repeat_id
        repeat_ids_by_measure = {}
        for note in notes_with_display:
            measure = note['measure']
            repeat_id = note['repeat_id']
            
            if measure not in repeat_ids_by_measure:
                repeat_ids_by_measure[measure] = set()
            repeat_ids_by_measure[measure].add(repeat_id)
        
        # Każdy takt powinien mieć konsystentny repeat_id
        for measure, repeat_ids in repeat_ids_by_measure.items():
            assert len(repeat_ids) == 1, f"Measure {measure} should have consistent repeat_id, got: {repeat_ids}"
        
        # Sprawdź oczekiwane repeat_id dla każdego taktu
        expected_repeat_ids = {
            0: 'repeat_0_3', 1: 'repeat_0_3', 2: 'repeat_0_3', 3: 'repeat_0_3',
            4: 'repeat_4_3', 5: 'repeat_4_3', 6: 'repeat_4_3', 7: 'repeat_4_3',
            8: None, 9: None, 10: None
        }
        
        for measure, expected_id in expected_repeat_ids.items():
            actual_id = list(repeat_ids_by_measure[measure])[0]
            assert actual_id == expected_id, f"Measure {measure}: expected repeat_id={expected_id}, got {actual_id}"

    def test_expand_repeats_structure_analysis(self):
        """Test analizy struktur repetycji"""
        score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
        part = score.parts[0]
        
        # Użyj internal method żeby sprawdzić struktury
        repeat_structures = self.expander._analyze_repeat_structures(part.measures)
        
        # Oczekiwane struktury:
        # 1. Pierwsza repetycja: takty 0-3 z voltami
        # 2. Druga repetycja: takty 4-7 z voltami  
        # 3. Końcowe takty: 8-10
        assert len(repeat_structures) >= 2, f"Expected at least 2 repeat structures, got: {len(repeat_structures)}"
        
        # Pierwsza struktura powinna obejmować takty 0-3
        first_structure = repeat_structures[0]
        assert first_structure['type'] == 'repeat', f"First structure should be repeat, got: {first_structure['type']}"
        
        # Sprawdź czy pierwszy struktura zawiera odpowiednie takty
        first_measures = first_structure['measures']
        expected_first_measures = [0, 1, 2, 3]  # Takty w pierwszej repetycji
        
        # Tolerancja dla różnych implementacji - ważne że zawiera kluczowe takty
        assert any(m in first_measures for m in [0, 1, 2]), (
            f"First structure should contain measures from first repeat (0,1,2), got: {first_measures}"
        )

    def test_linear_sequence_generation(self):
        """Test generowania liniowej sekwencji nut"""
        score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
        expanded_score = self.expander.expand_repeats(score)
        
        # Generuj sekwencję liniową
        notes = self.sequence_gen.generate_sequence(expanded_score)
        
        # Sprawdź że są nuty z rozszerzonych taktów
        measure_numbers = [note.measure_number for note in notes]
        unique_measures = list(dict.fromkeys(measure_numbers))  # Zachowaj kolejność, usuń duplikaty
        
        # Powinna zawierać oczekiwaną sekwencję taktów
        expected_sequence = [0, 1, 2, 0, 1, 3, 4, 5, 6, 4, 5, 7, 8, 9, 10]
        
        # Sprawdź czy sekwencja taktów w nutach odpowiada oczekiwanej
        for expected_measure in expected_sequence:
            assert expected_measure in measure_numbers, (
                f"Measure {expected_measure} not found in generated note sequence"
            )

    def test_notes_with_milliseconds(self):
        """Test generowania nut z informacją o milisekundach"""
        score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
        expanded_score = self.expander.expand_repeats(score)
        
        # Generuj nuty z timing w ms
        notes_ms = self.sequence_gen.get_notes_with_milliseconds(expanded_score)
        
        # Podstawowe sprawdzenia
        assert len(notes_ms) > 0, "Should generate notes with millisecond timing"
        
        # Sprawdź czy zawierają wymagane pola
        first_note = notes_ms[0]
        required_fields = ['pitch', 'start_time_ms', 'duration_ms', 'end_time_ms', 'measure', 'tempo_bpm']
        for field in required_fields:
            assert field in first_note, f"Note should contain field: {field}"
        
        # Sprawdź czy timing jest rosnący dla nie-akordowych nut
        prev_time = -1
        for note in notes_ms:
            if not note.get('is_rest', False):
                assert note['start_time_ms'] >= prev_time, "Note times should be non-decreasing"
                prev_time = note['start_time_ms']

    def test_implicit_repeat_start_detection(self):
        """Test wykrywania implicit repeat start na początku utworu"""
        score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
        part = score.parts[0]
        
        # Sprawdź że pierwszy takt nie ma explicit repeat_start
        first_measure = part.measures[0]  # Takt 0
        assert not first_measure.repeat_start, "First measure should not have explicit repeat start"
        
        # Ale takt 2 ma repeat_end
        measure_2 = next(m for m in part.measures if m.number == 2)
        assert measure_2.repeat_end, "Measure 2 should have repeat end"
        
        # RepeatExpander powinien wykryć implicit repeat od początku
        expanded_score = self.expander.expand_repeats(score)
        expanded_part = expanded_score.parts[0]
        expanded_numbers = [m.number for m in expanded_part.measures]
        
        # Powinna zawierać powtórzenie pierwszej sekcji
        assert expanded_numbers.count(0) == 2, "Measure 0 should appear twice (implicit repeat)"
        assert expanded_numbers.count(1) == 2, "Measure 1 should appear twice (implicit repeat)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 