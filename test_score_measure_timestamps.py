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

def test_timestamps():
    """Test that volta conflicts are resolved with new algorithm"""
    
    # Parse files
    parser = MusicXMLParser()
    expander = RepeatExpander()
    sequence_gen = LinearSequenceGenerator()
    
    # Parse original and expanded scores
    original_score = parser.parse_file('data/Fur_Elise.mxl')
    expanded_score = expander.expand_repeats(original_score)
    
    print(f"Original measures: {len(original_score.parts[0].measures)}")

    print("\n=== DEBUG: Original Score Timing Analysis ===")
    notes_with_display = sequence_gen.get_expanded_notes_with_milliseconds(original_score, expanded_score)
    
    print("Direct original notes timing by measure:")
    for measure_num in range(11):  # Measures 0-10
        measure_notes = [n for n in notes_with_display if n['measure'] == measure_num]
        if measure_notes:
            start_times = [n['start_time_ms'] for n in measure_notes]
            end_times = [n['end_time_ms'] for n in measure_notes]
            print(f"  Measure {measure_num}: {min(start_times):.1f} - {max(end_times):.1f}ms")
  

if __name__ == "__main__":
    test_timestamps()