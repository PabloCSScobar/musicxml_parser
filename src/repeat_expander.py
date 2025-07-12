#!/usr/bin/env python3
"""
Repeat Expander - Handles MusicXML repeats and voltas

This module expands repeats and voltas into a linear sequence of measures,
similar to how MuseScore handles repeat expansion.
"""

import logging
from typing import List, Dict, Optional, Tuple
from fractions import Fraction
from copy import deepcopy

try:
    from .musicxml_parser import MusicXMLScore, MusicXMLPart, MusicXMLMeasure, MusicXMLNote, EndingType
except ImportError:
    from musicxml_parser import MusicXMLScore, MusicXMLPart, MusicXMLMeasure, MusicXMLNote, EndingType

logger = logging.getLogger(__name__)


class RepeatExpander:
    """Expands repeats and voltas in MusicXML scores"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def expand_repeats(self, score: MusicXMLScore) -> MusicXMLScore:
        """Expand all repeats and voltas in the score"""
        expanded_score = deepcopy(score)
        
        for part in expanded_score.parts:
            self._expand_part_repeats(part)
        
        return expanded_score
    
    def _expand_part_repeats(self, part: MusicXMLPart):
        """Expand repeats in a single part"""
        if not part.measures:
            return
        
        # Store original measures for reference
        original_measures = part.measures[:]
        
        # Find repeat structures
        repeat_structures = self._analyze_repeat_structures(original_measures)
        
        if not repeat_structures:
            # No repeats, just update start times
            self._update_start_times(part.measures)
            return
        
        # Expand repeats
        expanded_measures = []
        current_time = Fraction(0)
        
        for structure in repeat_structures:
            expanded_section = self._expand_repeat_structure(structure, current_time, original_measures)
            expanded_measures.extend(expanded_section)
            if expanded_section:
                # Calculate current time based on last measure
                last_measure = expanded_section[-1]
                if last_measure.notes:
                    current_time = last_measure.notes[-1].start_time + last_measure.notes[-1].duration
                else:
                    current_time += self._calculate_measure_duration(last_measure)
        
        part.measures = expanded_measures
    
    def _analyze_repeat_structures(self, measures: List[MusicXMLMeasure]) -> List[Dict]:
        """Analyze repeat structures in measures"""
        structures = []
        current_structure = None
        i = 0
        
        self.logger.debug(f"Analyzing {len(measures)} measures for repeat structures")
        
        while i < len(measures):
            measure = measures[i]
            measure_processed = False
            self.logger.debug(f"Processing measure {i}: repeat_start={measure.repeat_start}, repeat_end={measure.repeat_end}, ending_type={measure.ending_type}")
            
            # Check for repeat start
            if measure.repeat_start:
                if current_structure is not None:
                    # End previous structure
                    structures.append(current_structure)
                
                # Start new repeat structure
                current_structure = {
                    'type': 'repeat',
                    'start_measure': i,
                    'measures': [],
                    'voltas': {},
                    'repeat_count': 2
                }
            
            # Check for volta
            if measure.ending_numbers and measure.ending_type:
                if current_structure is None:
                    # Look for the most recent repeat structure that hasn't been closed
                    # Voltas can extend beyond the repeat_end measure
                    if structures:
                        last_structure = structures[-1]
                        if last_structure['type'] == 'repeat':
                            # Extend the last repeat structure to include this volta
                            current_structure = last_structure
                            # Remove it from structures since we're still working on it
                            structures.pop()
                        else:
                            # No recent repeat, treat as simple section
                            current_structure = {
                                'type': 'simple',
                                'start_measure': i,
                                'measures': [],
                                'voltas': {},
                                'repeat_count': 1
                            }
                    else:
                        # No repeat start found, treat as simple section
                        current_structure = {
                            'type': 'simple',
                            'start_measure': i,
                            'measures': [],
                            'voltas': {},
                            'repeat_count': 1
                        }
                
                # Handle volta
                for ending_num in measure.ending_numbers:
                    if ending_num not in current_structure['voltas']:
                        current_structure['voltas'][ending_num] = []
                    
                    if measure.ending_type == EndingType.START:
                        current_structure['voltas'][ending_num] = [i]
                    elif measure.ending_type == EndingType.STOP or measure.ending_type == EndingType.DISCONTINUE:
                        if ending_num in current_structure['voltas']:
                            current_structure['voltas'][ending_num].append(i)
            
            # Add measure to current structure FIRST (before processing repeat_end)
            if current_structure is not None:
                current_structure['measures'].append(i)
                self.logger.debug(f"Added measure {i} to current structure")
                measure_processed = True
            
            # Check for repeat end or discontinue AFTER adding measure to structure
            if measure.repeat_end:
                if current_structure is not None:
                    current_structure['repeat_count'] = measure.repeat_count
                    structures.append(current_structure)
                    current_structure = None
                    # measure_processed is already True from above
                else:
                    # Implicit forward repeat - backward repeat without explicit forward repeat
                    # Need to restructure: convert all previous simple structures into one repeat structure
                    
                    # Collect all measures from previous simple structures
                    all_measures = []
                    for struct in structures:
                        if struct['type'] == 'simple':
                            all_measures.extend(struct['measures'])
                    
                    # Add current measure (but don't duplicate if already added)
                    if i not in all_measures:
                        all_measures.append(i)
                    
                    # Clear structures and create one repeat structure
                    structures.clear()
                    implicit_structure = {
                        'type': 'repeat',
                        'start_measure': 0,  # Start from beginning
                        'measures': sorted(list(set(all_measures))),  # All measures in order, no duplicates
                        'voltas': {},
                        'repeat_count': measure.repeat_count
                    }
                    structures.append(implicit_structure)
                    self.logger.debug(f"Created implicit repeat structure with measures {implicit_structure['measures']}, repeat_count={measure.repeat_count}")
                    measure_processed = True  # Measure was included in the implicit repeat
            elif measure.ending_type == EndingType.DISCONTINUE:
                # DISCONTINUE ends the repeat structure
                if current_structure is not None and current_structure['type'] == 'repeat':
                    structures.append(current_structure)
                    current_structure = None
            
            # Create simple structure for measures not part of any repeat structure
            if not measure_processed:
                # Simple measure, create single-measure structure
                simple_structure = {
                    'type': 'simple',
                    'start_measure': i,
                    'measures': [i],
                    'voltas': {},
                    'repeat_count': 1
                }
                structures.append(simple_structure)
                self.logger.debug(f"Created simple structure for measure {i}")
            
            i += 1
        
        # Add any remaining structure
        if current_structure is not None:
            structures.append(current_structure)
            self.logger.debug(f"Added remaining structure with measures {current_structure['measures']}")
        
        self.logger.debug(f"Final structures: {[(s['type'], s['measures'], s['repeat_count']) for s in structures]}")
        return structures
    
    def _expand_repeat_structure(self, structure: Dict, start_time: Fraction, original_measures: List[MusicXMLMeasure]) -> List[MusicXMLMeasure]:
        """Expand a single repeat structure"""
        self.logger.debug(f"Expanding structure: type={structure['type']}, measures={structure['measures']}, repeat_count={structure['repeat_count']}")
        
        if structure['type'] == 'simple':
            # No repeats, just return measures with updated times
            if structure['measures']:
                measure_idx = structure['measures'][0]
                if measure_idx < len(original_measures):
                    measure = deepcopy(original_measures[measure_idx])
                    self._update_measure_times([measure], start_time)
                    self.logger.debug(f"Expanded simple structure to 1 measure")
                    return [measure]
            return []
        
        # Handle repeat with voltas
        expanded_measures = []
        current_time = start_time
        
        repeat_count = structure['repeat_count']
        base_measures = structure['measures']
        voltas = structure['voltas']
        
        for repeat_num in range(1, repeat_count + 1):
            # Add base measures (before any volta)
            volta_start = None
            if voltas:
                volta_start = min(min(volta_measures) for volta_measures in voltas.values())
            
            if volta_start is not None:
                # Add measures before volta
                for measure_idx in base_measures:
                    if measure_idx < volta_start and measure_idx < len(original_measures):
                        measure = deepcopy(original_measures[measure_idx])
                        expanded_measures.append(measure)
                
                # Add appropriate volta measures
                volta_measures = self._get_volta_measures_for_repeat(voltas, repeat_num)
                for measure_idx in volta_measures:
                    if measure_idx < len(original_measures):
                        measure = deepcopy(original_measures[measure_idx])
                        expanded_measures.append(measure)
            else:
                # No voltas, just add all measures
                for measure_idx in base_measures:
                    if measure_idx < len(original_measures):
                        measure = deepcopy(original_measures[measure_idx])
                        expanded_measures.append(measure)
        
        # Update times
        self._update_measure_times(expanded_measures, current_time)
        
        self.logger.debug(f"Expanded repeat structure to {len(expanded_measures)} measures")
        return expanded_measures
    
    def _get_volta_measures_for_repeat(self, voltas: Dict, repeat_num: int) -> List[int]:
        """Get the measures for a specific repeat number"""
        if repeat_num in voltas:
            return list(range(voltas[repeat_num][0], voltas[repeat_num][-1] + 1))
        else:
            # Find the highest volta number <= repeat_num
            applicable_volta = None
            for volta_num in sorted(voltas.keys(), reverse=True):
                if volta_num <= repeat_num:
                    applicable_volta = volta_num
                    break
            
            if applicable_volta is not None:
                return list(range(voltas[applicable_volta][0], voltas[applicable_volta][-1] + 1))
        
        return []
    

    
    def _update_measure_times(self, measures: List[MusicXMLMeasure], start_time: Fraction):
        """Update start times for all notes in measures"""
        current_time = start_time
        
        for measure in measures:
            # Reset to measure start for each voice/staff
            measure_start = current_time
            voice_times = {}
            
            for note in measure.notes:
                # Track time per voice to handle multiple voices
                voice_key = (note.staff, note.voice)
                if voice_key not in voice_times:
                    voice_times[voice_key] = measure_start
                
                note.start_time = voice_times[voice_key]
                voice_times[voice_key] += note.duration
            
            # Move to next measure - use the longest voice duration
            if voice_times:
                current_time = max(voice_times.values())
            else:
                current_time += self._calculate_measure_duration(measure)
    
    def _update_start_times(self, measures: List[MusicXMLMeasure]):
        """Update start times for measures without repeats"""
        current_time = Fraction(0)
        
        for measure in measures:
            # Reset to measure start for each voice/staff
            measure_start = current_time
            voice_times = {}
            
            for note in measure.notes:
                # Track time per voice to handle multiple voices
                voice_key = (note.staff, note.voice)
                if voice_key not in voice_times:
                    voice_times[voice_key] = measure_start
                
                note.start_time = voice_times[voice_key]
                voice_times[voice_key] += note.duration
            
            # Move to next measure - use the longest voice duration
            if voice_times:
                current_time = max(voice_times.values())
            else:
                current_time += self._calculate_measure_duration(measure)
    
    def _calculate_measure_duration(self, measure: MusicXMLMeasure) -> Fraction:
        """Calculate the duration of a measure"""
        beats, beat_type = measure._time_signature
        return Fraction(beats, beat_type) * 4  # Convert to quarter notes


class LinearSequenceGenerator:
    """Generates a linear sequence of notes from expanded measures"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def generate_sequence(self, score: MusicXMLScore) -> List[MusicXMLNote]:
        """Generate a linear sequence of all notes in the score"""
        all_notes = []
        
        for part in score.parts:
            part_notes = self._get_part_notes(part)
            all_notes.extend(part_notes)
        
        # Sort by start time
        all_notes.sort(key=lambda note: note.start_time)
        
        return all_notes
    
    def _get_part_notes(self, part: MusicXMLPart) -> List[MusicXMLNote]:
        """Get all notes from a part"""
        notes = []
        
        for measure in part.measures:
            for note in measure.notes:
                # Add part information to note
                note_copy = deepcopy(note)
                notes.append(note_copy)
        
        return notes
    
    def get_notes_by_hand(self, score: MusicXMLScore) -> Tuple[List[MusicXMLNote], List[MusicXMLNote]]:
        """Get notes separated by hand (staff 1 = right, staff 2 = left)"""
        all_notes = self.generate_sequence(score)
        
        right_hand = [note for note in all_notes if note.staff == 1]
        left_hand = [note for note in all_notes if note.staff == 2]
        
        return right_hand, left_hand
    
    def get_playback_events(self, score: MusicXMLScore) -> List[Dict]:
        """Generate playback events with timing information"""
        events = []
        all_notes = self.generate_sequence(score)
        
        # Add initial tempo if available
        if score.tempo_bpm:
            events.append({
                'type': 'tempo_change',
                'time': Fraction(0),
                'tempo': score.tempo_bpm
            })
        
        # Add tempo changes
        current_tempo = score.tempo_bpm or 120
        for part in score.parts:
            for measure in part.measures:
                if measure.tempo_bpm and measure.tempo_bpm != current_tempo:
                    events.append({
                        'type': 'tempo_change',
                        'time': measure.notes[0].start_time if measure.notes else Fraction(0),
                        'tempo': measure.tempo_bpm
                    })
                    current_tempo = measure.tempo_bpm
        
        # Add note events
        for note in all_notes:
            if not note.is_rest:
                # Note on event
                events.append({
                    'type': 'note_on',
                    'time': note.start_time,
                    'pitch': note.pitch,
                    'staff': note.staff,
                    'measure': note.measure_number
                })
                
                # Note off event
                events.append({
                    'type': 'note_off',
                    'time': note.start_time + note.duration,
                    'pitch': note.pitch,
                    'staff': note.staff,
                    'measure': note.measure_number
                })
        
        # Sort events by time
        events.sort(key=lambda event: event['time'])
        
        return events


def main():
    """Example usage"""
    from .musicxml_parser import MusicXMLParser
    
    parser = MusicXMLParser()
    expander = RepeatExpander()
    sequence_gen = LinearSequenceGenerator()
    
    try:
        # Parse a file with repeats
        score = parser.parse_file('tests/data/simple_score.xml')
        print(f"Original score: {len(score.parts[0].measures)} measures")
        
        # Expand repeats
        expanded_score = expander.expand_repeats(score)
        print(f"Expanded score: {len(expanded_score.parts[0].measures)} measures")
        
        # Generate linear sequence
        notes = sequence_gen.generate_sequence(expanded_score)
        print(f"Total notes: {len(notes)}")
        
        # Get notes by hand
        right_hand, left_hand = sequence_gen.get_notes_by_hand(expanded_score)
        print(f"Right hand: {len(right_hand)} notes")
        print(f"Left hand: {len(left_hand)} notes")
        
        # Get playback events
        events = sequence_gen.get_playback_events(expanded_score)
        print(f"Playback events: {len(events)}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 