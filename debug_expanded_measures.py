#!/usr/bin/env python3
"""
Debug script to show expanded measures with simple timing table
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from musicxml_parser import MusicXMLParser
from repeat_expander import RepeatExpander, LinearSequenceGenerator

def debug_expanded_measures():
    """Show expanded measures with simple timing table"""
    
    # Parse files
    parser = MusicXMLParser()
    expander = RepeatExpander()
    sequence_gen = LinearSequenceGenerator()
    
    # Parse original and expanded scores
    original_score = parser.parse_file('data/fur_elize_multinotes.musicxml')
    # original_score = parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
    expanded_score = expander.expand_repeats(original_score)
    
    # Get expanded notes with display_ms
    expanded_notes_with_display = sequence_gen.get_expanded_notes_with_milliseconds(original_score, expanded_score)
    
    # Group notes by measure and show timing
    print("Original Takt | Original MS | Display MS")
    print("-" * 40)
    
    current_measure = None
    measure_notes = []
    
    for note in expanded_notes_with_display:
        print(note)
        # if note['measure'] != current_measure:
        #     # Print previous measure if exists
        #     if current_measure is not None:
        #         print_measure_timing(current_measure, measure_notes)
            
        #     # Start new measure
        #     current_measure = note['measure']
        #     measure_notes = []
        
        measure_notes.append(note)
    
    # Print last measure
    if current_measure is not None:
        print_measure_timing(current_measure, measure_notes)

def print_measure_timing(measure_num, notes):
    """Print timing for a measure"""
    if not notes:
        return
    
    # Get first note's timing (representative of measure start)
    first_note = notes[0]
    original_ms = first_note['start_time_ms']
    display_ms = first_note.get('start_time_display_ms', original_ms)
    
    print(f"     {measure_num:2d}      | {original_ms:8.1f}  | {display_ms:8.1f}")

if __name__ == "__main__":
    debug_expanded_measures() 