#!/usr/bin/env python3
"""
Prosty test timingów - półnuta i dwie ćwierćnuty w takcie 4/4
"""

import pytest
from fractions import Fraction
import sys
import os

# Dodaj src do path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from musicxml_parser import MusicXMLParser
from repeat_expander import RepeatExpander, LinearSequenceGenerator


def test_simple_timing():
    """Test prostego timingu: półnuta C5 + ćwierćnuta D5 + ćwierćnuta E5"""
    
    # Załaduj prosty plik MusicXML
    parser = MusicXMLParser()
    test_file = os.path.join(os.path.dirname(__file__), 'data', 'simple_timing_test.musicxml')
    score = parser.parse_file(test_file)
    
    print(f"Załadowano: {score.title}")
    print(f"Tempo: {score.tempo_bpm} BPM")
    
    # Test 1: Sprawdź podstawowe właściwości
    print("\nTest 1: Podstawowe właściwości")
    assert len(score.parts) == 1, "Powinien być 1 part"
    assert len(score.parts[0].measures) == 1, "Powinien być 1 takt"
    
    measure = score.parts[0].measures[0]
    assert len(measure.notes) == 3, f"Powinny być 3 nuty, jest {len(measure.notes)}"
    assert score.tempo_bpm == 120, f"Tempo powinno być 120, jest {score.tempo_bpm}"
    print("✓ Podstawowe właściwości są OK")
    
    # Test 2: Sprawdź długości nut (w ćwierćnutach)
    print("\nTest 2: Długości nut")
    notes = measure.notes
    
    # Półnuta C5 - powinna mieć duration = 2 ćwierćnuty
    assert notes[0].pitch == 'C5', f"Pierwsza nuta powinna być C5, jest {notes[0].pitch}"
    assert notes[0].duration == Fraction(2), f"C5 powinno mieć duration=2, ma {notes[0].duration}"
    
    # Ćwierćnuta D5 - powinna mieć duration = 1 ćwierćnuta  
    assert notes[1].pitch == 'D5', f"Druga nuta powinna być D5, jest {notes[1].pitch}"
    assert notes[1].duration == Fraction(1), f"D5 powinno mieć duration=1, ma {notes[1].duration}"
    
    # Ćwierćnuta E5 - powinna mieć duration = 1 ćwierćnuta
    assert notes[2].pitch == 'E5', f"Trzecia nuta powinna być E5, jest {notes[2].pitch}"
    assert notes[2].duration == Fraction(1), f"E5 powinno mieć duration=1, ma {notes[2].duration}"
    
    # Suma powinna być 4 ćwierćnuty (pełny takt 4/4)
    total = sum(note.duration for note in notes)
    assert total == Fraction(4), f"Suma długości powinna być 4, jest {total}"
    print("✓ Długości nut są poprawne")
    
    # Test 3: Oblicz start_time używając RepeatExpander
    print("\nTest 3: Obliczanie start_time")
    expander = RepeatExpander()
    expanded_score = expander.expand_repeats(score)
    
    expanded_notes = expanded_score.parts[0].measures[0].notes
    
    # Sprawdź start_time (w ćwierćnutach)
    assert expanded_notes[0].start_time == Fraction(0), f"C5 powinno zaczynać się od 0, ma {expanded_notes[0].start_time}"
    assert expanded_notes[1].start_time == Fraction(2), f"D5 powinno zaczynać się od 2, ma {expanded_notes[1].start_time}"
    assert expanded_notes[2].start_time == Fraction(3), f"E5 powinno zaczynać się od 3, ma {expanded_notes[2].start_time}"
    print("✓ Start times są poprawne (w ćwierćnutach)")
    
    # Test 4: Konwersja na milisekundy
    print("\nTest 4: Konwersja na milisekundy (120 BPM)")
    sequence_gen = LinearSequenceGenerator()
    notes_with_ms = sequence_gen.get_notes_with_milliseconds(expanded_score)
    
    assert len(notes_with_ms) == 3, f"Powinno być 3 nut z timingami, jest {len(notes_with_ms)}"
    
    # Przy 120 BPM: 1 ćwierćnuta = 500ms
    
    # C5 (półnuta)
    c5_note = notes_with_ms[0]
    assert c5_note['pitch'] == 'C5'
    assert c5_note['start_time_ms'] == 0.0, f"C5 start_time_ms powinno być 0, jest {c5_note['start_time_ms']}"
    assert c5_note['duration_ms'] == 1000.0, f"C5 duration_ms powinno być 1000, jest {c5_note['duration_ms']}"
    assert c5_note['end_time_ms'] == 1000.0, f"C5 end_time_ms powinno być 1000, jest {c5_note['end_time_ms']}"
    
    # D5 (ćwierćnuta)
    d5_note = notes_with_ms[1] 
    assert d5_note['pitch'] == 'D5'
    assert d5_note['start_time_ms'] == 1000.0, f"D5 start_time_ms powinno być 1000, jest {d5_note['start_time_ms']}"
    assert d5_note['duration_ms'] == 500.0, f"D5 duration_ms powinno być 500, jest {d5_note['duration_ms']}"
    assert d5_note['end_time_ms'] == 1500.0, f"D5 end_time_ms powinno być 1500, jest {d5_note['end_time_ms']}"
    
    # E5 (ćwierćnuta)
    e5_note = notes_with_ms[2]
    assert e5_note['pitch'] == 'E5'
    assert e5_note['start_time_ms'] == 1500.0, f"E5 start_time_ms powinno być 1500, jest {e5_note['start_time_ms']}"
    assert e5_note['duration_ms'] == 500.0, f"E5 duration_ms powinno być 500, jest {e5_note['duration_ms']}"
    assert e5_note['end_time_ms'] == 2000.0, f"E5 end_time_ms powinno być 2000, jest {e5_note['end_time_ms']}"
    
    print("✓ Konwersja na milisekundy jest poprawna")
    
    # Test 5: Sprawdź też wartości w ćwierćnutach
    print("\nTest 5: Wartości w ćwierćnutach")
    assert c5_note['start_time_quarter_notes'] == Fraction(0)
    assert c5_note['duration_quarter_notes'] == Fraction(2)
    
    assert d5_note['start_time_quarter_notes'] == Fraction(2)
    assert d5_note['duration_quarter_notes'] == Fraction(1)
    
    assert e5_note['start_time_quarter_notes'] == Fraction(3)
    assert e5_note['duration_quarter_notes'] == Fraction(1)
    print("✓ Wartości w ćwierćnutach są poprawne")
    
    print("\n🎉 Wszystkie testy przeszły!")
    print(f"Timing: C5(0-1000ms) -> D5(1000-1500ms) -> E5(1500-2000ms)")
    print(f"W ćwierćnutach: C5(0-2) -> D5(2-3) -> E5(3-4)")


if __name__ == '__main__':
    test_simple_timing() 