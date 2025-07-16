#!/usr/bin/env python3

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.musicxml_parser import MusicXMLParser
from src.repeat_expander import RepeatExpander, LinearSequenceGenerator


class TestTieTiming:
    """Test cases for tie timing handling."""
    
    def test_tie_timing(self):
        """Test that tied notes are properly detected and marked."""
        
        # Parse the test file with ties
        parser = MusicXMLParser()
        score = parser.parse_file('tests/data/test_tie.xml')
        
        # Verify basic parsing
        assert score is not None
        assert len(score.parts) == 1
        assert len(score.parts[0].measures) == 2
        
        # Check first measure - should have 4 notes
        measure1 = score.parts[0].measures[0]
        assert len(measure1.notes) == 4
        
        # Check second measure - should have 4 notes  
        measure2 = score.parts[0].measures[1]
        assert len(measure2.notes) == 4
        
        # Find the tied notes (C4)
        tied_note_start = None
        tied_note_stop = None
        
        # First C4 should have tie_start
        for note in measure1.notes:
            if note.pitch == "C4":
                tied_note_start = note
                break
                
        # Second C4 should have tie_stop
        for note in measure2.notes:
            if note.pitch == "C4":
                tied_note_stop = note
                break
                
        assert tied_note_start is not None, "Should find C4 note with tie_start in measure 1"
        assert tied_note_stop is not None, "Should find C4 note with tie_stop in measure 2"
        
        # Test what parser detects for ties
        print(f"First C4: tie_start={getattr(tied_note_start, 'tie_start', None)}, tie_stop={getattr(tied_note_start, 'tie_stop', None)}")
        print(f"Second C4: tie_start={getattr(tied_note_stop, 'tie_start', None)}, tie_stop={getattr(tied_note_stop, 'tie_stop', None)}")
        
        # Expand repeats
        expander = RepeatExpander()
        expanded_score = expander.expand_repeats(score)
        
        # Create linear sequence
        generator = LinearSequenceGenerator()
        notes_with_timing = generator.get_expanded_notes_with_milliseconds(score, expanded_score)
        
        # Print all notes for debugging
        print("\nAll notes with timing:")
        for i, note in enumerate(notes_with_timing):
            print(note)
            pitch = note['pitch'] if not note['is_rest'] else 'REST'
            print(f"  Note {i}: {pitch}, measure={note['measure']}, start_time_ms={note['start_time_ms']}")
        
        # Test: Find both C4 notes
        c4_notes = [note for note in notes_with_timing if note['pitch'] == 'C4']
        assert len(c4_notes) == 2, f"Should find exactly 2 C4 notes, found {len(c4_notes)}"
        
        # The first C4 should be at time 0, second C4 should be at time 2000ms (after whole measure 1)
        c4_note1 = c4_notes[0]
        c4_note2 = c4_notes[1]
        
        # Check timing
        assert c4_note1['start_time_ms'] == 0.0, f"First C4 should start at 0ms, got {c4_note1['start_time_ms']}"
        assert c4_note2['start_time_ms'] == 2000.0, f"Second C4 should start at 2000ms, got {c4_note2['start_time_ms']}"
        
        # Check tie attributes
        assert c4_note1['tie_start'] == True, f"First C4 should have tie_start=True, got {c4_note1['tie_start']}"
        assert c4_note1['tie_stop'] == False, f"First C4 should have tie_stop=False, got {c4_note1['tie_stop']}"
        
        assert c4_note2['tie_start'] == False, f"Second C4 should have tie_start=False, got {c4_note2['tie_start']}"
        assert c4_note2['tie_stop'] == True, f"Second C4 should have tie_stop=True, got {c4_note2['tie_stop']}"
        
        print(f"\n✅ First C4: {c4_note1['start_time_ms']}ms, tie_start={c4_note1['tie_start']}, tie_stop={c4_note1['tie_stop']}")
        print(f"✅ Second C4: {c4_note2['start_time_ms']}ms, tie_start={c4_note2['tie_start']}, tie_stop={c4_note2['tie_stop']}")
        
        # Now we properly detect tied notes!


if __name__ == '__main__':
    test = TestTieTiming()
    test.test_tie_timing()
    print("✅ All tie timing tests passed!") 