#!/usr/bin/env python3
"""
Test for volta conflict resolution with new positional mapping algorithm
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from musicxml_parser import MusicXMLParser
from repeat_expander import RepeatExpander, LinearSequenceGenerator

def test_volta_conflict_resolution():
    """Test that volta conflicts are resolved with new algorithm"""
    
    # Parse files
    parser = MusicXMLParser()
    expander = RepeatExpander()
    sequence_gen = LinearSequenceGenerator()
    
    # Parse original and expanded scores
    original_score = parser.parse_file('data/Fur_Elise.mxl')
    expanded_score = expander.expand_repeats(original_score)
    
    print(f"Original measures: {len(original_score.parts[0].measures)}")
    print(f"Expanded measures: {len(expanded_score.parts[0].measures)}")
    
    # DEBUG: Check original score timing independently
    print("\n=== DEBUG: Original Score Timing Analysis ===")
    original_notes_direct = sequence_gen.get_notes_with_milliseconds(original_score)
    
    print("Direct original notes timing by measure:")
    for measure_num in range(11):  # Measures 0-10
        measure_notes = [n for n in original_notes_direct if n['measure'] == measure_num]
        if measure_notes:
            start_times = [n['start_time_ms'] for n in measure_notes]
            print(f"  Measure {measure_num}: {min(start_times):.1f} - {max(start_times):.1f}ms")
    
    # Calculate expected timing manually
    print("\nManual timing calculation:")
    # Takt 0 = 500ms (przedtakt)
    # Reszta = 1500ms każdy (4/4 takty przy 120 BPM = 60000/120*4 = 2000ms? nie, sprawdźmy)
    print(f"Score tempo: {original_score.tempo_bpm} BPM")
    
    # Sprawdź metrum czasowe
    if original_score.parts[0].measures:
        first_measure = original_score.parts[0].measures[0]
        print(f"Time signature: {first_measure._time_signature}")
    
    # Use new method to get notes with display_ms
    notes_with_display = sequence_gen.get_expanded_notes_with_milliseconds(original_score, expanded_score)
    
    print(f"\nTotal notes with display_ms: {len(notes_with_display)}")
    
    # Expected display times for each measure start
    expected_measure_times = {
        0: 0.0,      # measure 0: 0ms  
        1: 500.0,    # measure 1: 500ms
        2: 2000.0,   # measure 2 (volta 1): 2000ms
        3: 3500.0,   # measure 3 (volta 2): 3500ms  
        4: 5000.0,   # measure 4: 5000ms
        5: 6500.0,   # measure 5: 6500ms
        6: 8000.0,   # measure 6 (volta 1): 8000ms
        7: 9500.0,   # measure 7 (volta 2): 9500ms
        8: 11000.0,  # measure 8: 11000ms
        9: 12500.0,  # measure 9: 12500ms
        10: 14000.0  # measure 10: 14000ms
    }
    
    # Test 1: Check volta conflicts are resolved
    print("\n=== Test 1: Volta Conflict Resolution ===")
    measure_display_ranges = {}
    
    for note in notes_with_display:
        measure = note['measure']
        display_ms = note['start_time_display_ms']
        
        if measure not in measure_display_ranges:
            measure_display_ranges[measure] = {'min': display_ms, 'max': display_ms}
        else:
            measure_display_ranges[measure]['min'] = min(measure_display_ranges[measure]['min'], display_ms)
            measure_display_ranges[measure]['max'] = max(measure_display_ranges[measure]['max'], display_ms)
    
    print(f"Measure display ranges:")
    for measure in sorted(measure_display_ranges.keys()):
        range_info = measure_display_ranges[measure]
        print(f"  Measure {measure}: {range_info['min']:.1f} - {range_info['max']:.1f}ms")
    
    # Check for conflicts (overlapping ranges)
    conflicts = []
    measures = sorted(measure_display_ranges.keys())
    for i, measure1 in enumerate(measures):
        for measure2 in measures[i+1:]:
            range1 = measure_display_ranges[measure1]
            range2 = measure_display_ranges[measure2]
            
            # Check if ranges REALLY overlap (not just touch at boundaries)
            # Real overlap means: range1_start < range2_end AND range2_start < range1_end
            if range1['min'] < range2['max'] and range2['min'] < range1['max']:
                # Additional check: if they only touch at one point, it's not a real conflict
                if not (range1['max'] == range2['min'] or range2['max'] == range1['min']):
                    conflicts.append((measure1, measure2))
    
    if conflicts:
        print(f"❌ BŁĄD: Znaleziono konflikty między taktami: {conflicts}")
        for measure1, measure2 in conflicts:
            range1 = measure_display_ranges[measure1]
            range2 = measure_display_ranges[measure2]
            print(f"  Takt {measure1}: {range1['min']:.1f}-{range1['max']:.1f}ms")
            print(f"  Takt {measure2}: {range2['min']:.1f}-{range2['max']:.1f}ms")
        assert False, "Volta conflicts not resolved!"
    else:
        print("✅ OK: Brak konfliktów między taktami")
    
    # Test 2: Check expected measure start times
    print("\n=== Test 2: Expected Measure Times ===")
    errors = []
    
    for measure, expected_time in expected_measure_times.items():
        if measure in measure_display_ranges:
            actual_start = measure_display_ranges[measure]['min']
            if abs(actual_start - expected_time) > 1.0:  # 1ms tolerance
                errors.append(f"Takt {measure}: expected {expected_time}ms, actual {actual_start}ms")
                print(f"❌ Takt {measure}: expected {expected_time}ms, actual {actual_start}ms → błąd {actual_start - expected_time:+.1f}ms")
            else:
                print(f"✅ Takt {measure}: {actual_start}ms (expected {expected_time}ms)")
        else:
            errors.append(f"Takt {measure}: not found in results")
    
    if errors:
        print(f"\n❌ BŁĘDY w czasach taktów:")
        for error in errors:
            print(f"  {error}")
        assert False, "Measure times don't match expectations!"
    else:
        print("\n✅ OK: Wszystkie czasy taktów są poprawne")
    
    # Test 3: Check that repeated measures have same display_ms
    print("\n=== Test 3: Repeated Measures Same Display Times ===")
    
    # Group notes by measure and iteration (using the iteration field)
    measure_iterations = {}
    for note in notes_with_display:
        measure = note['measure']
        iteration = note.get('iteration', 0)  # Use the iteration field we added
        
        if measure not in measure_iterations:
            measure_iterations[measure] = {}
        
        if iteration not in measure_iterations[measure]:
            measure_iterations[measure][iteration] = []
        
        measure_iterations[measure][iteration].append(note)
    
    # Check repeated measures (0, 1, 4, 5 should appear multiple times)
    repeated_measures = [0, 1, 4, 5]
    for measure in repeated_measures:
        if measure in measure_iterations and len(measure_iterations[measure]) > 1:
            iterations = measure_iterations[measure]
            print(f"Takt {measure} ma {len(iterations)} iteracji:")
            
            # All iterations should have same display_ms
            first_iteration_key = min(iterations.keys())
            first_display_times = set(note['start_time_display_ms'] for note in iterations[first_iteration_key])
            
            for iteration_num in sorted(iterations.keys()):
                iteration_notes = iterations[iteration_num]
                display_times = set(note['start_time_display_ms'] for note in iteration_notes)
                print(f"  Iteracja {iteration_num}: display_ms = {sorted(display_times)}")
                
                if display_times != first_display_times:
                    print(f"❌ BŁĄD: Takt {measure} ma różne display_ms w różnych iteracjach!")
                    assert False, f"Measure {measure} has different display_ms in different iterations"
            
            print(f"✅ OK: Takt {measure} ma identyczne display_ms we wszystkich iteracjach")
        else:
            print(f"Takt {measure}: nie znaleziono powtórzeń lub tylko 1 iteracja")
    
    print("\n=== WSZYSTKIE TESTY PRZESZŁY ===")

if __name__ == "__main__":
    test_volta_conflict_resolution()