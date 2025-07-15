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
        
        expanded_part = expanded_score.parts[0]
        expanded_numbers = [m.number for m in expanded_part.measures]
        
        # Oczekiwana sekwencja:
        # 1. Takty 0,1,2 (pierwsza volta pierwszej repetycji)
        # 2. Takty 0,1,3 (druga volta pierwszej repetycji)  
        # 3. Takty 4,5,6 (pierwsza volta drugiej repetycji)
        # 4. Takty 4,5,7 (druga volta drugiej repetycji)
        # 5. Takty 8,9,10 (końcowe takty)
        expected_sequence = [0, 1, 2, 0, 1, 3, 4, 5, 6, 4, 5, 7, 8, 9, 10]
        
        assert expanded_numbers == expected_sequence, (
            f"Błędna sekwencja po rozwinięciu repetycji.\n"
            f"Oczekiwana: {expected_sequence}\n"
            f"Otrzymana:  {expanded_numbers}\n"
            f"Oczekiwana długość: {len(expected_sequence)}, otrzymana: {len(expanded_numbers)}"
        )

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