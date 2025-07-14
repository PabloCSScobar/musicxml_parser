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



def quarter_notes_to_ms(quarter_notes: Fraction, bpm: int) -> float:
    """Convert quarter notes to milliseconds at given BPM"""
    # 1 quarter note = 60000ms / BPM
    ms_per_quarter = 60000.0 / bpm
    return float(quarter_notes) * ms_per_quarter


def ms_to_quarter_notes(milliseconds: float, bpm: int) -> Fraction:
    """Convert milliseconds to quarter notes at given BPM"""
    ms_per_quarter = 60000.0 / bpm
    return Fraction(milliseconds / ms_per_quarter).limit_denominator()



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
        
        # First pass: identify all repeat ends to detect implicit repeat starts
        repeat_ends = []
        for idx, measure in enumerate(measures):
            if measure.repeat_end:
                repeat_ends.append((idx, measure.repeat_count))
        
        # Check if we need implicit repeat start from beginning
        needs_implicit_start = False
        if repeat_ends:
            first_repeat_end_idx = repeat_ends[0][0]
            # Check if there's no explicit repeat start before first repeat end
            has_explicit_start = any(measures[j].repeat_start for j in range(first_repeat_end_idx + 1))
            if not has_explicit_start:
                needs_implicit_start = True
                self.logger.debug(f"Detected implicit repeat start needed - first repeat_end at measure {first_repeat_end_idx} with no prior repeat_start")
        
        while i < len(measures):
            measure = measures[i]
            measure_processed = False
            self.logger.debug(f"Processing measure {i}: repeat_start={measure.repeat_start}, repeat_end={measure.repeat_end}, ending_type={measure.ending_type}")
            
            # Handle implicit repeat start from beginning
            if i == 0 and needs_implicit_start and current_structure is None:
                current_structure = {
                    'type': 'repeat',
                    'start_measure': 0,
                    'measures': [],
                    'voltas': {},
                    'repeat_count': 2  # Will be updated when we hit repeat_end
                }
                self.logger.debug("Created implicit repeat structure starting from measure 0")
            
            # Check for explicit repeat start
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
                self.logger.debug(f"Created explicit repeat structure starting at measure {i}")
            
            # Check for volta
            if measure.ending_numbers and measure.ending_type:
                if current_structure is None:
                    # Look for the most recent repeat structure that hasn't been closed
                    # Voltas can extend beyond the repeat_end measure
                    if structures:
                        last_structure = structures[-1]
                        if last_structure['type'] == 'repeat':
                            # Volta found after repeat structure was closed
                            # Add volta info to the last repeat structure (retroactively)
                            self.logger.debug(f"Adding volta {measure.ending_numbers} to previous repeat structure")
                            for ending_num in measure.ending_numbers:
                                if ending_num not in last_structure['voltas']:
                                    last_structure['voltas'][ending_num] = []
                                
                                if measure.ending_type == EndingType.START:
                                    last_structure['voltas'][ending_num] = [i]
                                elif measure.ending_type == EndingType.STOP or measure.ending_type == EndingType.DISCONTINUE:
                                    if ending_num in last_structure['voltas']:
                                        last_structure['voltas'][ending_num].append(i)
                                    else:
                                        # Volta stop without start, just add this measure
                                        last_structure['voltas'][ending_num] = [i]
                            
                            # Don't continue with current_structure logic - volta is handled
                            measure_processed = True
                        else:
                            # No recent repeat, create implicit repeat structure
                            current_structure = {
                                'type': 'repeat',
                                'start_measure': 0,  # Implicit start from beginning
                                'measures': list(range(i + 1)),  # All measures up to this point
                                'voltas': {},
                                'repeat_count': 2
                            }
                            self.logger.debug(f"Created implicit repeat for volta at measure {i}")
                    else:
                        # No repeat start found, create implicit repeat structure
                        current_structure = {
                            'type': 'repeat',
                            'start_measure': 0,  # Implicit start from beginning  
                            'measures': list(range(i + 1)),  # All measures up to this point
                            'voltas': {},
                            'repeat_count': 2
                        }
                        self.logger.debug(f"Created implicit repeat for volta at measure {i} (no previous structures)")
                
                # Handle volta for current structure (if not already processed)
                if current_structure is not None:
                    for ending_num in measure.ending_numbers:
                        if ending_num not in current_structure['voltas']:
                            current_structure['voltas'][ending_num] = []
                        
                        if measure.ending_type == EndingType.START:
                            current_structure['voltas'][ending_num] = [i]
                        elif measure.ending_type == EndingType.STOP or measure.ending_type == EndingType.DISCONTINUE:
                            if ending_num in current_structure['voltas']:
                                current_structure['voltas'][ending_num].append(i)
                            else:
                                # Volta stop without start, just add this measure
                                current_structure['voltas'][ending_num] = [i]
            
            # Add measure to current structure FIRST (before processing repeat_end)
            if current_structure is not None:
                if i not in current_structure['measures']:
                    current_structure['measures'].append(i)
                self.logger.debug(f"Added measure {i} to current structure")
                measure_processed = True
            
            # Check for repeat end or discontinue AFTER adding measure to structure
            if measure.repeat_end:
                if current_structure is not None:
                    current_structure['repeat_count'] = measure.repeat_count
                    structures.append(current_structure)
                    current_structure = None
                    self.logger.debug(f"Closed repeat structure at measure {i} with repeat_count={measure.repeat_count}")
                else:
                    # Implicit forward repeat - backward repeat without explicit forward repeat
                    # This shouldn't happen now that we handle implicit starts above, but keep as fallback
                    all_measures = list(range(i + 1))  # All measures from 0 to current
                    
                    implicit_structure = {
                        'type': 'repeat',
                        'start_measure': 0,  # Start from beginning
                        'measures': all_measures,
                        'voltas': {},
                        'repeat_count': measure.repeat_count
                    }
                    structures.append(implicit_structure)
                    self.logger.debug(f"Created fallback implicit repeat structure with measures {implicit_structure['measures']}, repeat_count={measure.repeat_count}")
                    measure_processed = True
            elif measure.ending_type == EndingType.DISCONTINUE:
                # DISCONTINUE ends the repeat structure
                if current_structure is not None and current_structure['type'] == 'repeat':
                    structures.append(current_structure)
                    current_structure = None
                    self.logger.debug(f"Discontinued repeat structure at measure {i}")
            
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
        self.logger.debug(f"Expanding structure: type={structure['type']}, measures={structure['measures']}, repeat_count={structure['repeat_count']}, voltas={structure['voltas']}")
        
        if structure['type'] == 'simple':
            # No repeats, just return measures with updated times
            expanded_measures = []
            for measure_idx in structure['measures']:
                if measure_idx < len(original_measures):
                    measure = deepcopy(original_measures[measure_idx])
                    expanded_measures.append(measure)
            self._update_measure_times(expanded_measures, start_time)
            self.logger.debug(f"Expanded simple structure to {len(expanded_measures)} measures")
            return expanded_measures
        
        # Handle repeat with voltas
        expanded_measures = []
        repeat_count = structure['repeat_count']
        base_measures = structure['measures']
        voltas = structure['voltas']
        
        self.logger.debug(f"Base measures: {base_measures}")
        self.logger.debug(f"Voltas: {voltas}")
        
        # Find volta boundaries
        volta_measures = set()
        for volta_nums, measure_range in voltas.items():
            if measure_range:
                # volta_range is [start, end] but we need all measures in range
                start_measure = measure_range[0]
                end_measure = measure_range[-1] if len(measure_range) > 1 else measure_range[0]
                for m in range(start_measure, end_measure + 1):
                    volta_measures.add(m)
        
        # Split base measures into: before volta, volta measures, after volta
        pre_volta_measures = []
        post_volta_measures = []
        
        if volta_measures:
            min_volta = min(volta_measures)
            max_volta = max(volta_measures)
            
            for measure_idx in base_measures:
                if measure_idx < min_volta:
                    pre_volta_measures.append(measure_idx)
                elif measure_idx > max_volta:
                    post_volta_measures.append(measure_idx)
            
            self.logger.debug(f"Pre-volta: {pre_volta_measures}, volta: {sorted(volta_measures)}, post-volta: {post_volta_measures}")
        else:
            # No voltas, all measures are pre-volta
            pre_volta_measures = base_measures[:]
        
        # Generate repeated sections
        for repeat_num in range(1, repeat_count + 1):
            self.logger.debug(f"Generating repeat iteration {repeat_num}")
            
            # Add pre-volta measures (always included)
            for measure_idx in pre_volta_measures:
                if measure_idx < len(original_measures):
                    measure = deepcopy(original_measures[measure_idx])
                    expanded_measures.append(measure)
                    self.logger.debug(f"Added pre-volta measure {measure_idx}")
            
            # Add appropriate volta measures for this iteration
            if volta_measures:
                volta_to_play = self._get_volta_for_iteration(voltas, repeat_num)
                if volta_to_play:
                    volta_range = voltas[volta_to_play]
                    if volta_range:
                        start_measure = volta_range[0]
                        end_measure = volta_range[-1] if len(volta_range) > 1 else volta_range[0]
                        for measure_idx in range(start_measure, end_measure + 1):
                            if measure_idx < len(original_measures):
                                measure = deepcopy(original_measures[measure_idx])
                                expanded_measures.append(measure)
                                self.logger.debug(f"Added volta {volta_to_play} measure {measure_idx}")
            
            # Add post-volta measures (always included)  
            for measure_idx in post_volta_measures:
                if measure_idx < len(original_measures):
                    measure = deepcopy(original_measures[measure_idx])
                    expanded_measures.append(measure)
                    self.logger.debug(f"Added post-volta measure {measure_idx}")
        
        # Update times
        self._update_measure_times(expanded_measures, start_time)
        
        self.logger.debug(f"Expanded repeat structure to {len(expanded_measures)} measures: {[m.number for m in expanded_measures]}")
        return expanded_measures
    
    def _get_volta_for_iteration(self, voltas: Dict, repeat_num: int) -> Optional[int]:
        """Get the volta number to play for a specific repeat iteration"""
        if not voltas:
            return None
        
        # Direct match: volta number matches repeat iteration
        if repeat_num in voltas:
            self.logger.debug(f"Direct volta match: iteration {repeat_num} -> volta {repeat_num}")
            return repeat_num
        
        # Find the highest volta number that should apply to this iteration
        # Standard music logic: volta 1 plays on iteration 1, volta 2 on iteration 2, etc.
        applicable_volta = None
        for volta_num in sorted(voltas.keys(), reverse=True):
            if volta_num <= repeat_num:
                applicable_volta = volta_num
                break
        
        if applicable_volta is not None:
            self.logger.debug(f"Applicable volta for iteration {repeat_num}: volta {applicable_volta}")
            return applicable_volta
        
        # Fallback: use the first available volta
        first_volta = min(voltas.keys()) if voltas else None
        if first_volta:
            self.logger.debug(f"Fallback volta for iteration {repeat_num}: volta {first_volta}")
        return first_volta
    

    
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

    def get_notes_with_milliseconds(self, score: MusicXMLScore) -> List[Dict]:
        """Get all notes with millisecond timing information"""
        all_notes = self.generate_sequence(score)
        events = self.get_playback_events(score)
        
        # Build tempo map
        tempo_map = []
        current_tempo = score.tempo_bpm or 120
        
        for event in events:
            if event['type'] == 'tempo_change':
                tempo_map.append({
                    'time': event['time'],
                    'tempo': event['tempo']
                })
                current_tempo = event['tempo']
        
        # Convert notes to milliseconds
        notes_with_ms = []
        
        for note in all_notes:
            # Find applicable tempo
            applicable_tempo = score.tempo_bpm or 120
            for tempo_change in tempo_map:
                if tempo_change['time'] <= note.start_time:
                    applicable_tempo = tempo_change['tempo']
                else:
                    break
            
            # Convert times
            start_ms = quarter_notes_to_ms(note.start_time, applicable_tempo)
            duration_ms = quarter_notes_to_ms(note.duration, applicable_tempo)
            end_ms = start_ms + duration_ms
            
            note_info = {
                'pitch': note.pitch,
                'is_rest': note.is_rest,
                'staff': note.staff,
                'voice': note.voice,
                'measure': note.measure_number,
                'start_time_quarter_notes': note.start_time,
                'duration_quarter_notes': note.duration,
                'start_time_ms': start_ms,
                'duration_ms': duration_ms,
                'end_time_ms': end_ms,
                'tempo_bpm': applicable_tempo
            }
            
            notes_with_ms.append(note_info)
        
        return notes_with_ms
    
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