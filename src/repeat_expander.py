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
                # self.logger.debug(f"Detected implicit repeat start needed - first repeat_end at measure {first_repeat_end_idx} with no prior repeat_start")
        
        while i < len(measures):
            measure = measures[i]
            measure_processed = False
            # self.logger.debug(f"Processing measure {i}: repeat_start={measure.repeat_start}, repeat_end={measure.repeat_end}, ending_type={measure.ending_type}")
            
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
                # self.logger.debug(f"Created explicit repeat structure starting at measure {i}")
            
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
                        # self.logger.debug(f"Created implicit repeat for volta at measure {i} (no previous structures)")
                
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
                # self.logger.debug(f"Added measure {i} to current structure")
                measure_processed = True
            
            # Check for repeat end or discontinue AFTER adding measure to structure
            if measure.repeat_end:
                if current_structure is not None:
                    current_structure['repeat_count'] = measure.repeat_count
                    structures.append(current_structure)
                    current_structure = None
                    # self.logger.debug(f"Closed repeat structure at measure {i} with repeat_count={measure.repeat_count}")
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
                    # self.logger.debug(f"Created fallback implicit repeat structure with measures {implicit_structure['measures']}, repeat_count={measure.repeat_count}")
                    measure_processed = True
            elif measure.ending_type == EndingType.DISCONTINUE:
                # DISCONTINUE ends the repeat structure
                if current_structure is not None and current_structure['type'] == 'repeat':
                    structures.append(current_structure)
                    current_structure = None
                    # self.logger.debug(f"Discontinued repeat structure at measure {i}")
            
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
                    # self.logger.debug(f"Added pre-volta measure {measure_idx}")
            
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
                                # self.logger.debug(f"Added volta {volta_to_play} measure {measure_idx}")
            
            # Add post-volta measures (always included)  
            for measure_idx in post_volta_measures:
                if measure_idx < len(original_measures):
                    measure = deepcopy(original_measures[measure_idx])
                    expanded_measures.append(measure)
                    # self.logger.debug(f"Added post-volta measure {measure_idx}")
        
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
            # self.logger.debug(f"Direct volta match: iteration {repeat_num} -> volta {repeat_num}")
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
        
        print(f"DEBUG: _update_start_times called with {len(measures)} measures")
        
        for i, measure in enumerate(measures):
            # Reset to measure start for each voice/staff
            measure_start = current_time
            voice_times = {}
            
            print(f"DEBUG: Measure {measure.number} starts at {float(current_time):.1f} quarter notes")
            
            for note in measure.notes:
                # Track time per voice to handle multiple voices
                voice_key = (note.staff, note.voice)
                if voice_key not in voice_times:
                    voice_times[voice_key] = measure_start
                
                note.start_time = voice_times[voice_key]
                voice_times[voice_key] += note.duration
            
            # Move to next measure - use the longest voice duration
            if voice_times:
                old_current_time = current_time
                current_time = max(voice_times.values())
                print(f"DEBUG: Measure {measure.number} voice_times end at {float(current_time):.1f} quarter notes (was {float(old_current_time):.1f})")
            else:
                old_current_time = current_time
                measure_duration = self._calculate_measure_duration(measure)
                current_time += measure_duration
                print(f"DEBUG: Measure {measure.number} (empty) duration {float(measure_duration):.1f} quarter notes, current_time {float(old_current_time):.1f} -> {float(current_time):.1f}")
            
            print(f"DEBUG: Measure {measure.number} time signature: {measure._time_signature}")
    
    def _calculate_measure_duration(self, measure: MusicXMLMeasure) -> Fraction:
        """Calculate the duration of a measure based on its actual content"""
        # Use actual duration calculated during parsing if available
        if hasattr(measure, '_actual_duration') and measure._actual_duration > Fraction(0):
            return measure._actual_duration
        
        # Fallback: calculate from notes if available
        if measure.notes:
            # Calculate the actual duration based on the notes in the measure
            # Track the maximum time reached in the measure
            max_time = Fraction(0)
            current_time = Fraction(0)
            
            for note in measure.notes:
                current_time += note.duration
                if current_time > max_time:
                    max_time = current_time
            
            return max_time
        
        # If no notes, fall back to time signature
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
        
        print(f"DEBUG: score.tempo_bpm = {score.tempo_bpm}, current_tempo = {current_tempo}")
        
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
    
    def _calculate_display_times(self, notes_with_ms: List[Dict]):
        """Calculate display times for frontend visualization (resets for repeats)"""
        print(f"DEBUG: _calculate_display_times called with {len(notes_with_ms)} notes")
        
        if not notes_with_ms:
            print("DEBUG: No notes, returning early")
            return
        
        print(f"DEBUG: Calculating display times for {len(notes_with_ms)} notes")
        self.logger.debug(f"Calculating display times for {len(notes_with_ms)} notes")
        
        # Analyze repeat structure by grouping notes by measure patterns
        repeat_iterations = self._detect_repeat_iterations(notes_with_ms)
        
        print(f"DEBUG: Detected {len(repeat_iterations)} repeat iterations")
        self.logger.debug(f"Detected {len(repeat_iterations)} repeat iterations")
        
        # ALWAYS add display_ms field, even if no repeats detected
        if not repeat_iterations:
            # No repeats detected - display_ms = start_ms
            print("DEBUG: No repeat iterations detected, setting display_ms = start_ms for all notes")
            for i, note in enumerate(notes_with_ms):
                note['start_time_display_ms'] = note['start_time_ms']
                note['iteration'] = 0  # Single iteration
                # print(f"DEBUG: Note {i}: added start_time_display_ms = {note['start_time_display_ms']}")
            self.logger.debug("No repeat iterations - using start_time_ms as display_ms")
            print("DEBUG: Finished setting display times for all notes")
            return
        
        # Calculate display times - SHARED measures get same display_ms, UNIQUE measures get sequential time
        # Build global timeline that reuses positions for repeated measures
        
        # First, find which measures appear in which iterations
        measure_to_iterations = {}
        for iteration_idx, iteration_notes in enumerate(repeat_iterations):
            for note in iteration_notes:
                measure_num = note['measure']
                if measure_num not in measure_to_iterations:
                    measure_to_iterations[measure_num] = []
                if iteration_idx not in measure_to_iterations[measure_num]:
                    measure_to_iterations[measure_num].append(iteration_idx)
        
        print(f"DEBUG: Measure to iterations mapping: {measure_to_iterations}")
        
        # Build global display timeline
        global_measure_display_start = {}
        current_display_time = 0.0
        
        # Process measures in order they appear in first iteration (base timeline)
        first_iteration_notes = repeat_iterations[0] if repeat_iterations else []
        first_iteration_measures = []
        seen_measures = set()
        
        for note in first_iteration_notes:
            measure_num = note['measure']
            if measure_num not in seen_measures:
                first_iteration_measures.append(measure_num)
                seen_measures.add(measure_num)
        
        print(f"DEBUG: Base timeline measures: {first_iteration_measures}")
        
        # Assign display times to base measures
        for measure_num in first_iteration_measures:
            global_measure_display_start[measure_num] = current_display_time
            print(f"  Measure {measure_num}: display_start = {current_display_time}")
            
            # Calculate measure duration from first occurrence
            measure_notes = [n for n in first_iteration_notes if n['measure'] == measure_num]
            if measure_notes:
                measure_start = min(n['start_time_ms'] for n in measure_notes)
                measure_end = max(n['start_time_ms'] + n['duration_ms'] for n in measure_notes)
                measure_duration = measure_end - measure_start
                current_display_time += measure_duration
        
        # Now handle unique measures from other iterations (voltas)
        for iteration_idx, iteration_notes in enumerate(repeat_iterations):
            if iteration_idx == 0:
                continue  # Already processed base iteration
                
            measures_in_iteration = []
            seen_measures = set()
            
            for note in iteration_notes:
                measure_num = note['measure']
                if measure_num not in seen_measures:
                    measures_in_iteration.append(measure_num)
                    seen_measures.add(measure_num)
            
            # print(f"DEBUG: Iteration {iteration_idx} measures: {measures_in_iteration}")
            
            # Process measures unique to this iteration (not in base timeline)
            for measure_num in measures_in_iteration:
                if measure_num not in global_measure_display_start:
                    # This is a unique measure (e.g. volta 2)
                    global_measure_display_start[measure_num] = current_display_time
                    print(f"  Measure {measure_num} (unique): display_start = {current_display_time}")
                    
                    # Calculate duration and advance timeline
                    measure_notes = [n for n in iteration_notes if n['measure'] == measure_num]
                    if measure_notes:
                        measure_start = min(n['start_time_ms'] for n in measure_notes)
                        measure_end = max(n['start_time_ms'] + n['duration_ms'] for n in measure_notes)
                        measure_duration = measure_end - measure_start
                        current_display_time += measure_duration
        
        # Apply display times to all notes
        for iteration_idx, iteration_notes in enumerate(repeat_iterations):
            print(f"DEBUG: Applying display times for iteration {iteration_idx}")
            
            for note in iteration_notes:
                measure_num = note['measure']
                measure_start_display = global_measure_display_start[measure_num]
                
                # Find original measure start time for this measure in this iteration
                measure_notes = [n for n in iteration_notes if n['measure'] == measure_num]
                measure_start_original = min(n['start_time_ms'] for n in measure_notes)
                
                # Calculate note offset within measure
                note_offset_in_measure = note['start_time_ms'] - measure_start_original
                
                # Set display time and iteration info
                note['start_time_display_ms'] = measure_start_display + note_offset_in_measure
                note['iteration'] = iteration_idx
            
            self.logger.debug(f"Iteration {iteration_idx}: {len(iteration_notes)} notes, "
                            f"measures={sorted(set(n['measure'] for n in iteration_notes))}")
    

    def _detect_repeat_iterations(self, notes_with_ms: List[Dict]) -> List[List[Dict]]:
        """Detect repeat iterations by analyzing measure number patterns"""
        if not notes_with_ms:
            return []
        
        # Group notes by measure number to analyze patterns
        measures_timeline = []
        current_measure = None
        measure_start_time = None
        
        for note in notes_with_ms:
            if note['measure'] != current_measure:
                if current_measure is not None:
                    measures_timeline.append({
                        'measure': current_measure,
                        'start_time_ms': measure_start_time
                    })
                current_measure = note['measure']
                measure_start_time = note['start_time_ms']
        
        # Add last measure
        if current_measure is not None:
            measures_timeline.append({
                'measure': current_measure,
                'start_time_ms': measure_start_time
            })
        
        print(f"DEBUG: Measures timeline: {[(m['measure'], m['start_time_ms']) for m in measures_timeline]}")
        self.logger.debug(f"Measures timeline: {[(m['measure'], m['start_time_ms']) for m in measures_timeline]}")
        
        # Look for patterns where same measure numbers appear multiple times
        measure_occurrences = {}
        for i, entry in enumerate(measures_timeline):
            measure_num = entry['measure']
            if measure_num not in measure_occurrences:
                measure_occurrences[measure_num] = []
            measure_occurrences[measure_num].append(i)
        
        print(f"DEBUG: Measure occurrences: {measure_occurrences}")
        
        # Find measures that appear multiple times (indicating repeats)
        repeated_measures = {m: times for m, times in measure_occurrences.items() if len(times) > 1}
        
        print(f"DEBUG: Repeated measures: {repeated_measures}")
        
        # NOWE: Sprawdź czy to wygląda na rozwiniętą repetycję (nie na prawdziwe wielokrotne iteracje)
        # Jeśli takty nie są w kolejnych blokach, to prawdopodobnie to rozwinięta repetycja
        if repeated_measures:
            # Sprawdź czy powtarzające się takty tworzą sensowne bloki
            total_measures = len(measures_timeline)
            max_repeats = max(len(times) for times in repeated_measures.values())
            
            # Jeśli mamy tylko 2 wystąpienia każdego taktu i nie ma wyraźnego wzorca 
            # wielokrotnego powtarzania, traktuj jako rozwiniętą repetycję
            if max_repeats <= 2 and total_measures <= 10:
                print("DEBUG: Detected expanded repeat (not multiple iterations) - treating as no repeats")
                self.logger.debug("Detected expanded repeat (not multiple iterations) - treating as no repeats")
                return []
        
        if not repeated_measures:
            # No repeats detected, return empty list so display_ms = start_ms
            print("DEBUG: No repeated measures detected - returning empty iterations")
            self.logger.debug("No repeated measures detected - returning empty iterations")
            return []
        
        # Find the boundaries of repeat iterations
        # Strategy: use the first repeated measure to detect iteration boundaries
        first_repeated_measure = min(repeated_measures.keys())
        repeat_boundaries = [measures_timeline[i]['start_time_ms'] 
                           for i in measure_occurrences[first_repeated_measure]]
        
        print(f"DEBUG: First repeated measure: {first_repeated_measure}")
        print(f"DEBUG: Repeat boundaries: {repeat_boundaries}")
        self.logger.debug(f"Repeat boundaries based on measure {first_repeated_measure}: {repeat_boundaries}")
        
        # Group notes by iteration
        iterations = []
        for i, boundary_start in enumerate(repeat_boundaries):
            boundary_end = repeat_boundaries[i + 1] if i + 1 < len(repeat_boundaries) else float('inf')
            
            iteration_notes = [
                note for note in notes_with_ms 
                if boundary_start <= note['start_time_ms'] < boundary_end
            ]
            
            # print(f"DEBUG: Iteration {i}: boundary_start={boundary_start}, boundary_end={boundary_end}, notes={len(iteration_notes)}")
            
            if iteration_notes:
                iterations.append(iteration_notes)
        
        print(f"DEBUG: Final iterations: {len(iterations)} iterations with {[len(it) for it in iterations]} notes each")
        return iterations
    
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

    def get_expanded_notes_with_milliseconds(self, score: MusicXMLScore, expanded_score: MusicXMLScore) -> List[Dict]:
        """Get all notes with millisecond timing for expanded score, with display_ms from original score"""
        print(f"DEBUG: get_expanded_notes_with_milliseconds called")
        
        # Get notes from original score (without repeats) - this gives us correct display_ms
        original_notes = self.get_notes_with_milliseconds(score)
        print(f"DEBUG: Got {len(original_notes)} original notes")
        
        # DEBUG: Print original notes timing
        print("DEBUG: Original notes timing by measure:")
        original_by_measure = {}
        for note in original_notes:
            measure = note['measure']
            if measure not in original_by_measure:
                original_by_measure[measure] = []
            original_by_measure[measure].append(note)
        
        for measure in sorted(original_by_measure.keys()):
            measure_notes = original_by_measure[measure]
            start_times = [n['start_time_ms'] for n in measure_notes]
            print(f"  Measure {measure}: {len(measure_notes)} notes, times: {min(start_times):.1f} - {max(start_times):.1f}ms")
        
        # Get notes from expanded score (with repeats) - this gives us correct start_ms for playback
        expanded_notes = self.get_notes_with_milliseconds(expanded_score)
        print(f"DEBUG: Got {len(expanded_notes)} expanded notes")
        
        # Join them - copy display_ms from original to expanded
        notes_with_display = self.join_display_with_expanded(expanded_notes, original_notes)
        print(f"DEBUG: Joined into {len(notes_with_display)} notes with display_ms")
        
        return notes_with_display

    def join_display_with_expanded(self, expanded_notes: List[Dict], original_notes: List[Dict]) -> List[Dict]:
        """Join expanded notes with display_ms from original notes by sequential position"""
        print(f"DEBUG: Joining {len(expanded_notes)} expanded notes with {len(original_notes)} original notes")
        
        # Group original notes by measure, preserving order
        original_by_measure = {}
        for note in original_notes:
            measure = note['measure']
            if measure not in original_by_measure:
                original_by_measure[measure] = []
            original_by_measure[measure].append(note)
        
        print(f"DEBUG: Original notes grouped by measures: {list(original_by_measure.keys())}")
        
        # Detect repeat iterations in expanded notes
        repeat_iterations = self._detect_repeat_iterations_for_display(expanded_notes)
        print(f"DEBUG: Detected {len(repeat_iterations)} repeat iterations")
        
        result = []
        
        # Process each iteration separately
        for iteration_idx, iteration_notes in enumerate(repeat_iterations):
            print(f"DEBUG: Processing iteration {iteration_idx} with {len(iteration_notes)} notes")
            
            # Reset pointers for each iteration - this is the key fix!
            original_pointers = {}
            
            for i, expanded_note in enumerate(iteration_notes):
                measure = expanded_note['measure']
                
                # Initialize pointer for this measure if not exists
                if measure not in original_pointers:
                    original_pointers[measure] = 0
                
                # Get original notes for this measure
                if measure in original_by_measure:
                    original_measure_notes = original_by_measure[measure]
                    
                    if original_measure_notes:  # Make sure list is not empty
                        # Use modulo to cycle through original notes when measure repeats
                        note_index = original_pointers[measure] % len(original_measure_notes)
                        original_note = original_measure_notes[note_index]
                        display_ms = original_note['start_time_ms']
                        original_pointers[measure] += 1
                        
                        # print(f"DEBUG: Iteration {iteration_idx}, note {i} (measure {measure}, pos {note_index}): "
                        #       f"mapped to display_ms = {display_ms}")
                    else:
                        # Empty measure - fallback
                        display_ms = expanded_note['start_time_ms']
                        print(f"DEBUG: FALLBACK for iteration {iteration_idx}, note {i} (measure {measure}): "
                              f"empty original measure, using start_time_ms = {display_ms}")
                else:
                    # Measure not found in original - fallback
                    display_ms = expanded_note['start_time_ms']
                    print(f"DEBUG: FALLBACK for iteration {iteration_idx}, note {i} (measure {measure}): "
                          f"measure not found in original, using start_time_ms = {display_ms}")
                
                # Create result note with display_ms
                note_with_display = expanded_note.copy()
                note_with_display['start_time_display_ms'] = display_ms
                note_with_display['iteration'] = iteration_idx
                result.append(note_with_display)
        
        print(f"DEBUG: Successfully joined {len(result)} notes with display_ms")
        return result

    def _detect_repeat_iterations_for_display(self, notes_with_ms: List[Dict]) -> List[List[Dict]]:
        """Detect repeat iterations for display_ms calculation - improved version"""
        if not notes_with_ms:
            return []
        
        # Group notes by measure number to analyze patterns
        measures_timeline = []
        current_measure = None
        
        for note in notes_with_ms:
            if note['measure'] != current_measure:
                current_measure = note['measure']
                measures_timeline.append(current_measure)
        
        print(f"DEBUG: Measures timeline: {measures_timeline}")
        
        # Look for STRUCTURAL repeat patterns, not random phrase repetitions
        # Focus on larger blocks of consecutive measures that repeat
        
        # Find blocks of consecutive repeated measures
        structural_repeats = self._find_structural_repeats(measures_timeline)
        
        if not structural_repeats:
            # No structural repeats detected, return all notes as single iteration
            print("DEBUG: No structural repeats detected - single iteration")
            return [notes_with_ms]
        
        print(f"DEBUG: Found structural repeats: {structural_repeats}")
        
        # Build iterations based on structural repeat boundaries
        iterations = self._build_iterations_from_structural_repeats(notes_with_ms, measures_timeline, structural_repeats)
        
        print(f"DEBUG: Created {len(iterations)} iterations")
        return iterations
    
    def _find_structural_repeats(self, measures_timeline: List[int]) -> List[Dict]:
        """Find structural repeat patterns (large blocks of consecutive measures)"""
        # Look for patterns where sequences of measures repeat
        # E.g. [0,1,2,3,4,5,6,7,8,0,1,2,3,4,5,6,7] -> structural repeat of 0-7
        
        structural_repeats = []
        
        # Try different block sizes (prefer larger blocks)
        for block_size in range(max(5, len(measures_timeline) // 10), 1, -1):  # Start from large blocks
            if block_size * 2 > len(measures_timeline):
                continue
                
            # Check if we can find this block size repeating
            for start_pos in range(len(measures_timeline) - block_size * 2 + 1):
                block1 = measures_timeline[start_pos:start_pos + block_size]
                
                # Look for the same block later in the timeline
                for second_start in range(start_pos + block_size, len(measures_timeline) - block_size + 1):
                    block2 = measures_timeline[second_start:second_start + block_size]
                    
                    if block1 == block2:
                        # Found a structural repeat!
                        repeat_info = {
                            'block_measures': block1,
                            'first_occurrence': (start_pos, start_pos + block_size),
                            'second_occurrence': (second_start, second_start + block_size),
                            'block_size': block_size
                        }
                        
                        # Check if this repeat doesn't overlap with existing ones
                        if not self._overlaps_with_existing_repeats(repeat_info, structural_repeats):
                            structural_repeats.append(repeat_info)
                            print(f"DEBUG: Found structural repeat: block {block1} at positions {start_pos}-{start_pos+block_size-1} and {second_start}-{second_start+block_size-1}")
                            break  # Found repeat for this start position
        
        # Sort by block size (largest first) and filter overlaps
        structural_repeats.sort(key=lambda x: x['block_size'], reverse=True)
        
        # Remove smaller overlapping repeats
        filtered_repeats = []
        for repeat in structural_repeats:
            if not any(self._repeats_overlap(repeat, existing) for existing in filtered_repeats):
                filtered_repeats.append(repeat)
        
        return filtered_repeats
    
    def _overlaps_with_existing_repeats(self, new_repeat: Dict, existing_repeats: List[Dict]) -> bool:
        """Check if new repeat overlaps with existing ones"""
        for existing in existing_repeats:
            if self._repeats_overlap(new_repeat, existing):
                return True
        return False
    
    def _repeats_overlap(self, repeat1: Dict, repeat2: Dict) -> bool:
        """Check if two repeats overlap in timeline positions"""
        r1_start, r1_end = repeat1['first_occurrence']
        r1_start2, r1_end2 = repeat1['second_occurrence']
        r2_start, r2_end = repeat2['first_occurrence']
        r2_start2, r2_end2 = repeat2['second_occurrence']
        
        # Check if any ranges overlap
        ranges1 = [(r1_start, r1_end), (r1_start2, r1_end2)]
        ranges2 = [(r2_start, r2_end), (r2_start2, r2_end2)]
        
        for start1, end1 in ranges1:
            for start2, end2 in ranges2:
                if start1 < end2 and start2 < end1:  # Ranges overlap
                    return True
        return False
    
    def _build_iterations_from_structural_repeats(self, notes_with_ms: List[Dict], 
                                                measures_timeline: List[int], 
                                                structural_repeats: List[Dict]) -> List[List[Dict]]:
        """Build iterations based on structural repeats"""
        if not structural_repeats:
            return [notes_with_ms]
        
        # For now, use the largest structural repeat to define iterations
        main_repeat = structural_repeats[0]  # Already sorted by size
        
        first_start, first_end = main_repeat['first_occurrence']
        second_start, second_end = main_repeat['second_occurrence']
        
        print(f"DEBUG: Using main repeat: measures timeline positions {first_start}-{first_end-1} and {second_start}-{second_end-1}")
        
        # Build index of where each measure starts in the notes list
        measure_start_indices = {}
        note_index = 0
        for measure_pos, measure_num in enumerate(measures_timeline):
            measure_start_indices[measure_pos] = note_index
            
            # Count notes in this measure
            measure_note_count = 0
            while (note_index + measure_note_count < len(notes_with_ms) and 
                   notes_with_ms[note_index + measure_note_count]['measure'] == measure_num):
                measure_note_count += 1
            
            note_index += measure_note_count
        
        # Add end index
        measure_start_indices[len(measures_timeline)] = len(notes_with_ms)
        
        # Create iterations:
        # 1. Everything before first repeat
        # 2. First occurrence of repeat
        # 3. Second occurrence of repeat  
        # 4. Everything after second repeat
        
        iterations = []
        
        # Before first repeat
        if first_start > 0:
            start_note_idx = 0
            end_note_idx = measure_start_indices[first_start]
            if end_note_idx > start_note_idx:
                iteration_notes = notes_with_ms[start_note_idx:end_note_idx]
                iterations.append(iteration_notes)
                print(f"DEBUG: Iteration 0 (before repeat): {len(iteration_notes)} notes")
        
        # First occurrence of repeat
        start_note_idx = measure_start_indices[first_start]
        end_note_idx = measure_start_indices[first_end]
        if end_note_idx > start_note_idx:
            iteration_notes = notes_with_ms[start_note_idx:end_note_idx]
            iterations.append(iteration_notes)
            print(f"DEBUG: Iteration {len(iterations)-1} (first repeat): {len(iteration_notes)} notes")
        
        # Between repeats (if any)
        if second_start > first_end:
            start_note_idx = measure_start_indices[first_end]
            end_note_idx = measure_start_indices[second_start]
            if end_note_idx > start_note_idx:
                iteration_notes = notes_with_ms[start_note_idx:end_note_idx]
                iterations.append(iteration_notes)
                print(f"DEBUG: Iteration {len(iterations)-1} (between repeats): {len(iteration_notes)} notes")
        
        # Second occurrence of repeat
        start_note_idx = measure_start_indices[second_start]
        end_note_idx = measure_start_indices[second_end]
        if end_note_idx > start_note_idx:
            iteration_notes = notes_with_ms[start_note_idx:end_note_idx]
            iterations.append(iteration_notes)
            print(f"DEBUG: Iteration {len(iterations)-1} (second repeat): {len(iteration_notes)} notes")
        
        # After second repeat
        if second_end < len(measures_timeline):
            start_note_idx = measure_start_indices[second_end]
            end_note_idx = len(notes_with_ms)
            if end_note_idx > start_note_idx:
                iteration_notes = notes_with_ms[start_note_idx:end_note_idx]
                iterations.append(iteration_notes)
                print(f"DEBUG: Iteration {len(iterations)-1} (after repeat): {len(iteration_notes)} notes")
        
        # Filter out empty iterations
        iterations = [it for it in iterations if it]
        
        print(f"DEBUG: Final iterations: {len(iterations)} with sizes {[len(it) for it in iterations]}")
        return iterations


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