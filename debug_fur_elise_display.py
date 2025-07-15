#!/usr/bin/env python3

import sys
from pathlib import Path

# Dodaj src do ścieżki Pythona
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from musicxml_parser import MusicXMLParser
from repeat_expander import RepeatExpander, LinearSequenceGenerator

def debug_fur_elise_display():
    """Debug wszystkich nut z Fur_Elise z display_time"""
    
    # Parsowanie
    parser = MusicXMLParser()
    score = parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
    print(f"Parsed score: {score.title}")
    
    # Rozwinięcie repetycji  
    expander = RepeatExpander()
    expanded_score = expander.expand_repeats(score)
    print(f"Expanded to {len(expanded_score.parts[0].measures)} measures")
    
    # Generowanie sekwencji z millisekund
    sequence_gen = LinearSequenceGenerator()
    notes_with_ms = sequence_gen.get_notes_with_milliseconds(expanded_score)
    
    print(f"\n=== WSZYSTKIE NUTY ({len(notes_with_ms)}) ===")
    print(f"{'#':<3} {'Measure':<7} {'Pitch':<6} {'Staff':<5} {'Voice':<5} {'Start_MS':<10} {'Display_MS':<10} {'Diff':<8}")
    print("-" * 70)
    
    for i, note in enumerate(notes_with_ms):
        start_ms = note['start_time_ms']
        display_ms = note['start_time_display_ms']
        diff = start_ms - display_ms
        
        # Obsługa None dla pitch (przerwy)
        pitch = note['pitch'] if note['pitch'] is not None else 'REST'
        
        print(f"{i:<3} {note['measure']:<7} {pitch:<6} {note['staff']:<5} {note['voice']:<5} "
              f"{start_ms:<10.1f} {display_ms:<10.1f} {diff:<8.1f}")
    
    # Analiza iteracji repetycji
    print(f"\n=== ANALIZA ITERACJI ===")
    
    # Grupuj według taktu 0
    takt_0_notes = [n for n in notes_with_ms if n['measure'] == 0]
    print(f"Nuty z taktu 0: {len(takt_0_notes)}")
    
    # Znajdź unikalne start_time dla taktu 0
    unique_starts = {}
    for note in takt_0_notes:
        start_time = note['start_time_ms']
        if start_time not in unique_starts:
            unique_starts[start_time] = []
        unique_starts[start_time].append(note)
    
    print(f"Unikalne czasy start dla taktu 0: {sorted(unique_starts.keys())}")
    
    for start_time in sorted(unique_starts.keys()):
        notes = unique_starts[start_time]
        print(f"  Start_MS={start_time}: {len(notes)} nut")
        for note in notes:
            pitch = note['pitch'] if note['pitch'] is not None else 'REST'
            print(f"    {pitch} (staff={note['staff']}, voice={note['voice']}, display_ms={note['start_time_display_ms']})")
    
    # Sprawdź boundaries z algorytmu
    print(f"\n=== DEBUG ALGORYTMU ===")
    print("(Zobacz logi DEBUG powyżej)")

if __name__ == "__main__":
    debug_fur_elise_display() 