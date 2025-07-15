import unittest
import os
import sys
from fractions import Fraction

# Dodaj ścieżkę do katalogu src, aby móc importować moduły z projektu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.musicxml_parser import MusicXMLParser
from src.repeat_expander import RepeatExpander, LinearSequenceGenerator

class TestChordTiming(unittest.TestCase):
    def test_chord_timing(self):
        parser = MusicXMLParser()
        score = parser.parse_file('tests/data/test_chord.xml')  # Upewnij się, że ścieżka jest poprawna
        notes = score.parts[0].measures[0].notes
        expander = RepeatExpander()
        expanded_score = expander.expand_repeats(score)
        sequence_gen = LinearSequenceGenerator()
        expanded_notes_with_display = sequence_gen.get_expanded_notes_with_milliseconds(score, expanded_score)
        
        ds_notes = expanded_notes_with_display
        
        print(notes)
        self.assertEqual(len(notes), 3, "Powinny być 3 nuty w akordzie")
        print("--------------------------------\n")


        for note in ds_notes:
            print(note)
            self.assertEqual(note['start_time_ms'], 0, f"Nuta {note['pitch']} ma nieprawidłowy czas rozpoczęcia: {note['start_time_ms']}")
            self.assertEqual(note['start_time_display_ms'], 0, f"Nuta {note['pitch']} ma nieprawidłowy czas rozpoczęcia: {note['start_time_display_ms']}")
        print("--------------------------------\n")
        
        # Sprawdź, czy wszystkie nuty mają ten sam czas rozpoczęcia (0)
        expected_start_time = Fraction(0)
        for note in notes:
            self.assertEqual(note.start_time, expected_start_time, f"Nuta {note.pitch} ma nieprawidłowy czas rozpoczęcia: {note.start_time}")
    

    def test_chord_timing_2(self):
        parser = MusicXMLParser()
        score = parser.parse_file('tests/data/fur_elize_multinotes.musicxml')
        notes = score.parts[0].measures[0].notes
        expander = RepeatExpander()
        expanded_score = expander.expand_repeats(score)
        sequence_gen = LinearSequenceGenerator()
        notes_ms = sequence_gen.get_expanded_notes_with_milliseconds(score, expanded_score)

        for note in notes_ms[:10]:
            print(note)

        self.assertEqual(notes_ms[0]['start_time_ms'], 0)
        self.assertEqual(notes_ms[0]['start_time_display_ms'], 0)
        self.assertEqual(notes_ms[1]['start_time_ms'], 0)
        self.assertEqual(notes_ms[1]['start_time_display_ms'], 0)
        self.assertEqual(notes_ms[2]['start_time_ms'], 0)
        self.assertEqual(notes_ms[2]['start_time_display_ms'], 0)
        self.assertEqual(notes_ms[3]['start_time_ms'], 0)
        self.assertEqual(notes_ms[3]['start_time_display_ms'], 0)
        self.assertEqual(notes_ms[4]['start_time_ms'], 250)
        self.assertEqual(notes_ms[4]['start_time_display_ms'], 250)



if __name__ == '__main__':
    unittest.main()
