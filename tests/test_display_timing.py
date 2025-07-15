#!/usr/bin/env python3
"""
Test suite for display timing functionality
"""

import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from musicxml_parser import MusicXMLParser
from repeat_expander import RepeatExpander, LinearSequenceGenerator

class TestDisplayTiming(unittest.TestCase):
    """Test display timing functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = MusicXMLParser()
        self.expander = RepeatExpander()
        self.sequence_gen = LinearSequenceGenerator()
    
    # def test_simple_repeats_display_timing(self):
    #     """Test display timing for simple repeats (Für Elise simplified)"""
    #     # Parse simple file with known structure
    #     original_score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
    #     expanded_score = self.expander.expand_repeats(original_score)
        
    #     # Get notes with display timing
    #     notes_with_display = self.sequence_gen.get_expanded_notes_with_milliseconds(original_score, expanded_score)
        
    #     # Analyze measures in result
    #     measures_by_iteration = {}
    #     for note in notes_with_display:
    #         iteration = note.get('iteration', 0)
    #         measure = note['measure']
            
    #         if iteration not in measures_by_iteration:
    #             measures_by_iteration[iteration] = set()
    #         measures_by_iteration[iteration].add(measure)
        
    #     print(f"Simple file - iterations found: {len(measures_by_iteration)}")
    #     for iteration, measures in measures_by_iteration.items():
    #         sorted_measures = sorted(measures)
    #         print(f"  Iteration {iteration}: measures {sorted_measures}")
        
    #     # For simplified file, we should have reasonable number of iterations
    #     self.assertLessEqual(len(measures_by_iteration), 3, 
    #                        "Too many iterations detected for simple file")
        
    #     # Check that measure 0 in different iterations has correct display_ms
    #     measure_0_notes = [n for n in notes_with_display if n['measure'] == 0]
        
    #     if len(measure_0_notes) > 2:  # Multiple iterations of measure 0
    #         # First occurrence should be at 0ms
    #         first_occurrence = min(measure_0_notes, key=lambda n: n['start_time_ms'])
    #         self.assertEqual(first_occurrence['start_time_display_ms'], 0.0,
    #                        "First measure 0 should have display_ms = 0")
            
    #         # Second occurrence should also be at 0ms (reset for repeat)
    #         other_occurrences = [n for n in measure_0_notes if n != first_occurrence]
    #         for note in other_occurrences:
    #             self.assertEqual(note['start_time_display_ms'], 0.0,
    #                            "Repeated measure 0 should have display_ms = 0")
    
    def test_complex_file_iteration_detection(self):
        """Test that complex files don't generate too many false iterations"""
        try:
            # Try to parse full Für Elise file 
            original_score = self.parser.parse_file('data/Fur_Elise.mxl')
            expanded_score = self.expander.expand_repeats(original_score)
            
            # Get notes with display timing
            notes_with_display = self.sequence_gen.get_expanded_notes_with_milliseconds(original_score, expanded_score)
            
            # Analyze iterations
            iterations = set(note.get('iteration', 0) for note in notes_with_display)
            
            print(f"Full file - iterations detected: {len(iterations)}")
            print(f"Total notes: {len(notes_with_display)}")
            
            # Should not have excessive number of iterations (max reasonable is around 4-6 for complex piece)
            self.assertLessEqual(len(iterations), 6, 
                               f"Too many iterations detected: {len(iterations)}. "
                               f"This suggests the algorithm is overly aggressive.")
            
            # Print sample of measures by iteration
            measures_by_iteration = {}
            for note in notes_with_display:
                iteration = note.get('iteration', 0)
                measure = note['measure']
                
                if iteration not in measures_by_iteration:
                    measures_by_iteration[iteration] = set()
                measures_by_iteration[iteration].add(measure)
            
            for iteration in sorted(iterations)[:3]:  # Show first 3 iterations
                measures = sorted(measures_by_iteration[iteration])[:10]  # First 10 measures
                print(f"  Iteration {iteration}: measures {measures}...")
                
        except FileNotFoundError:
            self.skipTest("Full Für Elise file not found")
    
    def test_display_ms_mapping_logic(self):
        """Test the core logic of mapping display_ms"""
        # Create simple test data
        original_notes = [
            {'measure': 0, 'start_time_ms': 0.0, 'pitch': 'D5'},
            {'measure': 1, 'start_time_ms': 500.0, 'pitch': 'E5'},
            {'measure': 2, 'start_time_ms': 1000.0, 'pitch': 'F5'},
        ]
        
        # Simulate expanded notes with repeat
        expanded_notes = [
            # First iteration
            {'measure': 0, 'start_time_ms': 0.0, 'pitch': 'D5'},
            {'measure': 1, 'start_time_ms': 500.0, 'pitch': 'E5'},
            {'measure': 2, 'start_time_ms': 1000.0, 'pitch': 'F5'},
            # Second iteration (repeated section)
            {'measure': 0, 'start_time_ms': 1500.0, 'pitch': 'D5'},  # Should map to display_ms 0.0
            {'measure': 1, 'start_time_ms': 2000.0, 'pitch': 'E5'},  # Should map to display_ms 500.0
            {'measure': 3, 'start_time_ms': 2500.0, 'pitch': 'G5'},  # New measure, should get new display_ms
        ]
        
        # Test the mapping logic
        result = self.sequence_gen.join_display_with_expanded(expanded_notes, original_notes)
        
        # Check results
        self.assertEqual(len(result), 6, "Should have all 6 notes")
        
        # First iteration should match original timing
        self.assertEqual(result[0]['start_time_display_ms'], 0.0)
        self.assertEqual(result[1]['start_time_display_ms'], 500.0)
        self.assertEqual(result[2]['start_time_display_ms'], 1000.0)
        
        # Second iteration of repeated measures should map back to original timing
        repeated_measure_0 = [n for n in result if n['measure'] == 0 and n['start_time_ms'] == 1500.0][0]
        self.assertEqual(repeated_measure_0['start_time_display_ms'], 0.0,
                        "Repeated measure 0 should map to original display time")
        
        repeated_measure_1 = [n for n in result if n['measure'] == 1 and n['start_time_ms'] == 2000.0][0]
        self.assertEqual(repeated_measure_1['start_time_display_ms'], 500.0,
                        "Repeated measure 1 should map to original display time")

if __name__ == '__main__':
    unittest.main() 