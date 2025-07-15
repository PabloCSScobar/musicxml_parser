#!/usr/bin/env python3
"""
MusicXML Parser - Inspired by MuseScore's architecture

This module provides a comprehensive MusicXML parser with support for:
- Two-pass parsing (like MuseScore)
- Repeats and volta handling
- Tempo and time signature changes
- Multi-staff parts (left/right hand)
- Comprehensive error handling and logging
"""

import logging
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from fractions import Fraction
from enum import Enum
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MusicXMLError(Exception):
    """Base exception for MusicXML parsing errors"""
    pass


class BarlineType(Enum):
    """Types of barlines"""
    NORMAL = "normal"
    LIGHT_HEAVY = "light-heavy"
    HEAVY_LIGHT = "heavy-light"
    HEAVY_HEAVY = "heavy-heavy"
    DOUBLE = "double"


class RepeatDirection(Enum):
    """Repeat directions"""
    FORWARD = "forward"
    BACKWARD = "backward"


class EndingType(Enum):
    """Ending types for voltas"""
    START = "start"
    STOP = "stop"
    DISCONTINUE = "discontinue"


@dataclass
class MusicXMLNote:
    """Represents a single note or rest"""
    pitch: Optional[str] = None  # e.g., "C4", "F#5", or None for rest
    duration: Fraction = field(default_factory=lambda: Fraction(0))  # in quarter notes
    measure_number: int = 0
    staff: int = 1  # 1 for right hand, 2 for left hand (piano)
    voice: int = 1
    start_time: Fraction = field(default_factory=lambda: Fraction(0))  # absolute time from start
    is_rest: bool = False
    tie_start: bool = False
    tie_stop: bool = False
    # Additional attributes expected by tests
    is_chord: bool = False
    tie: Optional[str] = None  # "start", "stop", or None
    
    def __post_init__(self):
        """Validate note data"""
        if self.pitch is None:
            self.is_rest = True
            # Keep pitch as None for rests - tests expect this
        # Set tie based on tie_start/tie_stop
        if self.tie_start:
            self.tie = "start"
        elif self.tie_stop:
            self.tie = "stop"


@dataclass
class MusicXMLMeasure:
    """Represents a measure with its properties"""
    number: int
    _time_signature: Tuple[int, int] = (4, 4)  # (beats, beat_type)
    tempo_bpm: Optional[int] = None
    key_signature: int = 0  # fifths: -7 to 7
    divisions: int = 4  # divisions per quarter note
    repeat_start: bool = False
    repeat_end: bool = False
    repeat_count: int = 2
    ending_numbers: List[int] = field(default_factory=list)
    ending_type: Optional[EndingType] = None
    notes: List[MusicXMLNote] = field(default_factory=list)
    implicit: bool = False # Added for pickup/anacrusis
    _actual_duration: Fraction = field(default_factory=lambda: Fraction(0)) # Added for actual duration
    
    @property
    def time_signature(self) -> Tuple[int, int]:
        """Return time signature as tuple (e.g., (4, 4))"""
        return self._time_signature
    
    @time_signature.setter
    def time_signature(self, value: Tuple[int, int]):
        """Set time signature from tuple"""
        self._time_signature = value


@dataclass
class MusicXMLPart:
    """Represents a musical part (e.g., Piano)"""
    id: str
    name: str
    instrument: str = "Piano"
    midi_channel: int = 1
    midi_program: int = 1
    measures: List[MusicXMLMeasure] = field(default_factory=list)
    staves: int = 1  # Number of staves (2 for piano)


@dataclass
class MusicXMLScore:
    """Represents the complete musical score"""
    title: str = "Untitled"
    composer: str = "Unknown"
    parts: List[MusicXMLPart] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    # Global score properties (defaults from first measure)
    tempo_bpm: Optional[int] = None
    _time_signature: Tuple[int, int] = (4, 4)
    key_signature: int = 0
    
    @property
    def time_signature(self) -> Tuple[int, int]:
        """Return time signature as tuple (e.g., (4, 4))"""
        return self._time_signature
    
    @time_signature.setter
    def time_signature(self, value: Tuple[int, int]):
        """Set time signature from tuple"""
        self._time_signature = value


class MusicXMLLogger:
    """Logger for MusicXML parsing, inspired by MuseScore"""
    
    def __init__(self, level=logging.INFO):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(level)
        self.errors = []
        self.warnings = []
    
    def log_error(self, message: str, element: Optional[ET.Element] = None):
        """Log an error message"""
        if element is not None:
            message = f"{message} (line {element.sourceline if hasattr(element, 'sourceline') else 'unknown'})"
        self.errors.append(message)
        self.logger.error(message)
    
    def log_warning(self, message: str, element: Optional[ET.Element] = None):
        """Log a warning message"""
        if element is not None:
            message = f"{message} (line {element.sourceline if hasattr(element, 'sourceline') else 'unknown'})"
        self.warnings.append(message)
        self.logger.warning(message)
    
    def log_info(self, message: str):
        """Log an info message"""
        self.logger.info(message)


class MusicXMLParserPass1:
    """First pass parser - collects structure information"""
    
    def __init__(self, logger: MusicXMLLogger):
        self.logger = logger
        self.score = MusicXMLScore()
        self.current_divisions = 4
        self.current_tempo = 120
        self.current_time_sig = (4, 4)
        self.current_key_sig = 0
    
    def parse(self, xml_content: str) -> MusicXMLScore:
        """Parse MusicXML content - first pass"""
        try:
            root = ET.fromstring(xml_content)
            self._parse_score_header(root)
            self._parse_parts_structure(root)
            return self.score
        except ET.ParseError as e:
            self.logger.log_error(f"XML parsing error: {e}")
            raise MusicXMLError(f"Invalid XML: {e}")
    
    def _parse_score_header(self, root: ET.Element):
        """Parse score header information"""
        # Work title
        work = root.find('.//work/work-title')
        if work is not None:
            self.score.title = work.text or "Untitled"
        
        # Composer
        composer = root.find('.//identification/creator[@type="composer"]')
        if composer is not None:
            self.score.composer = composer.text or "Unknown"
        
        self.logger.log_info(f"Parsing score: {self.score.title} by {self.score.composer}")
    
    def _parse_parts_structure(self, root: ET.Element):
        """Parse part-list and basic part structure"""
        part_list = root.find('part-list')
        if part_list is None:
            raise MusicXMLError("No part-list found")
        
        # Parse score-parts
        for score_part in part_list.findall('score-part'):
            part_id = score_part.get('id')
            if not part_id:
                self.logger.log_error("score-part missing id attribute")
                continue
            
            part_name = score_part.find('part-name')
            part_name_text = part_name.text if part_name is not None else f"Part {part_id}"
            
            # Create part
            part = MusicXMLPart(id=part_id, name=part_name_text)
            
            # Parse instrument info
            instrument = score_part.find('.//score-instrument/instrument-name')
            if instrument is not None:
                part.instrument = instrument.text or "Piano"
            
            # Parse MIDI info
            midi_channel = score_part.find('.//midi-instrument/midi-channel')
            if midi_channel is not None:
                try:
                    part.midi_channel = int(midi_channel.text)
                except ValueError:
                    self.logger.log_warning(f"Invalid MIDI channel: {midi_channel.text}")
            
            midi_program = score_part.find('.//midi-instrument/midi-program')
            if midi_program is not None:
                try:
                    part.midi_program = int(midi_program.text)
                except ValueError:
                    self.logger.log_warning(f"Invalid MIDI program: {midi_program.text}")
            
            self.score.parts.append(part)
            # self.logger.log_info(f"Added part: {part.name} (id: {part.id})")


class MusicXMLParserPass2:
    """Second pass parser - parses detailed musical content"""
    
    def __init__(self, score: MusicXMLScore, logger: MusicXMLLogger):
        self.score = score
        self.logger = logger
        self.current_divisions = 4
        self.current_tempo = 120
        self.current_time_sig = (4, 4)
        self.current_key_sig = 0
        self.current_time = Fraction(0)
    
    def parse(self, xml_content: str) -> MusicXMLScore:
        """Parse MusicXML content - second pass"""
        try:
            root = ET.fromstring(xml_content)
            self._parse_parts_content(root)
            return self.score
        except ET.ParseError as e:
            self.logger.log_error(f"XML parsing error: {e}")
            raise MusicXMLError(f"Invalid XML: {e}")
    
    def _parse_parts_content(self, root: ET.Element):
        """Parse detailed content of all parts"""
        for part_elem in root.findall('part'):
            part_id = part_elem.get('id')
            if not part_id:
                self.logger.log_error("part missing id attribute")
                continue
            
            # Find corresponding part from pass1
            part = next((p for p in self.score.parts if p.id == part_id), None)
            if part is None:
                self.logger.log_error(f"Part {part_id} not found in part-list")
                continue
            
            self._parse_part_measures(part_elem, part)
    
    def _parse_part_measures(self, part_elem: ET.Element, part: MusicXMLPart):
        """Parse all measures in a part"""
        self.current_time = Fraction(0)
        
        for measure_elem in part_elem.findall('measure'):
            measure_number = measure_elem.get('number')
            if not measure_number:
                self.logger.log_error("measure missing number attribute")
                continue
            
            try:
                measure_num = int(measure_number)
            except ValueError:
                self.logger.log_error(f"Invalid measure number: {measure_number}")
                continue
            
            measure = self._parse_measure(measure_elem, measure_num)
            part.measures.append(measure)
            
            # Update current time
            measure_duration = self._calculate_measure_duration(measure)
            self.current_time += measure_duration
    
    def _parse_measure(self, measure_elem: ET.Element, measure_num: int) -> MusicXMLMeasure:
        """Parse a single measure"""
        measure = MusicXMLMeasure(
            number=measure_num,
            tempo_bpm=self.current_tempo,
            key_signature=self.current_key_sig,
            divisions=self.current_divisions
        )
        # Set time signature using the property setter
        measure._time_signature = self.current_time_sig
        
        # Check if this is an implicit measure (pickup/anacrusis)
        if measure_elem.get('implicit') == 'yes':
            measure.implicit = True
        
        # Track timing within measure like MuseScore
        measure_start_time = self.current_time
        m_time = Fraction(0)  # current time within measure
        m_dura = Fraction(0)  # maximum time reached in measure
        
        # Parse attributes first
        for attr_elem in measure_elem.findall('attributes'):
            self._parse_attributes(attr_elem, measure)
        
        # Parse directions (tempo, etc.)
        for direction_elem in measure_elem.findall('direction'):
            self._parse_direction(direction_elem, measure)
        
        # Parse barlines - prioritize right barline over left barline
        left_ending_types = []
        right_ending_types = []
        all_ending_numbers = []
        
        for barline_elem in measure_elem.findall('barline'):
            self._parse_barline(barline_elem, measure)
            
            # Parse ending (volta) information
            ending_elem = barline_elem.find('ending')
            if ending_elem is not None:
                ending_type = ending_elem.get('type')
                ending_number = ending_elem.get('number')
                
                if ending_type and ending_number:
                    try:
                        ending_numbers = [int(n.strip()) for n in ending_number.split(',')]
                        all_ending_numbers.extend(ending_numbers)
                        
                        location = barline_elem.get('location', 'right')
                        if location == 'left':
                            left_ending_types.append(EndingType(ending_type))
                        else:  # right or no location (defaults to right)
                            right_ending_types.append(EndingType(ending_type))
                    except ValueError:
                        self.logger.log_warning(f"Invalid ending number: {ending_number}")
        
        # Use right barline endings if available, otherwise left barline endings
        final_ending_types = right_ending_types if right_ending_types else left_ending_types
        
        if all_ending_numbers:
            measure.ending_numbers = list(set(all_ending_numbers))
        
        if final_ending_types:
            # Within the same barline, prioritize: STOP > DISCONTINUE > START
            # STOP is most important as it indicates the definitive end of a volta
            if EndingType.STOP in final_ending_types:
                measure.ending_type = EndingType.STOP
            elif EndingType.DISCONTINUE in final_ending_types:
                measure.ending_type = EndingType.DISCONTINUE
            elif EndingType.START in final_ending_types:
                measure.ending_type = EndingType.START
        
        # Parse measure content in order, handling backup/forward
        last_note_start_time = measure_start_time  # Track start time of the last non-chord note
        
        for child in measure_elem:
            if child.tag == 'note':
                # Determine start time for this note
                has_chord_element = child.find('chord') is not None
                
                if has_chord_element:
                    # This is a chord note - use the start time of the last non-chord note
                    note_start_time = last_note_start_time
                else:
                    # This is a regular note (potentially the first note of a new chord)
                    note_start_time = measure_start_time + m_time
                    last_note_start_time = note_start_time  # Update for potential following chord notes
                
                note = self._parse_note(child, measure_num, note_start_time)
                if note:
                    measure.notes.append(note)
                    # Update m_time and m_dura like MuseScore
                    if not note.is_chord:  # Don't advance time for chord notes
                        old_m_time = m_time
                        m_time += note.duration
                        # self.logger.log_info(f"Measure {measure_num}: note duration {note.duration} quarter notes, m_time {old_m_time} -> {m_time}")
                        if m_time > m_dura:
                            old_m_dura = m_dura
                            m_dura = m_time
                            # self.logger.log_info(f"Measure {measure_num}: updated m_dura {old_m_dura} -> {m_dura}")
                    else:
                        pass
                        # self.logger.log_info(f"Measure {measure_num}: chord note, m_time unchanged at {m_time}")
            
            elif child.tag == 'backup':
                duration_elem = child.find('duration')
                if duration_elem is not None:
                    try:
                        backup_duration = int(duration_elem.text)
                        backup_quarter_notes = Fraction(backup_duration, self.current_divisions)
                        old_m_time = m_time
                        m_time -= backup_quarter_notes
                        # self.logger.log_info(f"Measure {measure_num}: backup {backup_duration} units ({backup_quarter_notes} quarter notes), m_time {old_m_time} -> {m_time}")
                        if m_time < Fraction(0):
                            m_time = Fraction(0)
                    except ValueError:
                        self.logger.log_warning(f"Invalid backup duration: {duration_elem.text}")
            
            elif child.tag == 'forward':
                duration_elem = child.find('duration')
                if duration_elem is not None:
                    try:
                        forward_duration = int(duration_elem.text)
                        forward_quarter_notes = Fraction(forward_duration, self.current_divisions)
                        old_m_time = m_time
                        m_time += forward_quarter_notes
                        # self.logger.log_info(f"Measure {measure_num}: forward {forward_duration} units ({forward_quarter_notes} quarter notes), m_time {old_m_time} -> {m_time}")
                        if m_time > m_dura:
                            m_dura = m_time
                    except ValueError:
                        self.logger.log_warning(f"Invalid forward duration: {duration_elem.text}")
        
        # Set final duration based on actual content
        measure._actual_duration = m_dura
        
        # # Debug logging
        # self.logger.log_info(f"Measure {measure_num}: m_dura={m_dura}, notes_count={len(measure.notes)}")
        # self.logger.log_info(f"Measure {measure_num}: divisions={self.current_divisions}")
        
        return measure
    
    def _parse_attributes(self, attr_elem: ET.Element, measure: MusicXMLMeasure):
        """Parse measure attributes"""
        # Divisions
        divisions = attr_elem.find('divisions')
        if divisions is not None:
            try:
                self.current_divisions = int(divisions.text)
                measure.divisions = self.current_divisions
            except ValueError:
                self.logger.log_warning(f"Invalid divisions: {divisions.text}")
        
        # Time signature
        time_elem = attr_elem.find('time')
        if time_elem is not None:
            beats = time_elem.find('beats')
            beat_type = time_elem.find('beat-type')
            if beats is not None and beat_type is not None:
                try:
                    beats_val = int(beats.text)
                    beat_type_val = int(beat_type.text)
                    self.current_time_sig = (beats_val, beat_type_val)
                    measure._time_signature = self.current_time_sig
                except ValueError:
                    self.logger.log_warning(f"Invalid time signature: {beats.text}/{beat_type.text}")
        
        # Key signature
        key_elem = attr_elem.find('key/fifths')
        if key_elem is not None:
            try:
                self.current_key_sig = int(key_elem.text)
                measure.key_signature = self.current_key_sig
            except ValueError:
                self.logger.log_warning(f"Invalid key signature: {key_elem.text}")
        
        # Staves
        staves = attr_elem.find('staves')
        if staves is not None:
            try:
                # Find the part this measure belongs to
                for part in self.score.parts:
                    if measure in part.measures or len(part.measures) == 0:
                        part.staves = int(staves.text)
                        break
            except ValueError:
                self.logger.log_warning(f"Invalid staves count: {staves.text}")
    
    def _parse_direction(self, direction_elem: ET.Element, measure: MusicXMLMeasure):
        """Parse direction elements (tempo, etc.)"""
        # Metronome/tempo
        metronome = direction_elem.find('.//metronome')
        if metronome is not None:
            per_minute = metronome.find('per-minute')
            if per_minute is not None:
                try:
                    self.current_tempo = int(per_minute.text)
                    measure.tempo_bpm = self.current_tempo
                except ValueError:
                    self.logger.log_warning(f"Invalid tempo: {per_minute.text}")
        
        # Sound element for tempo
        sound = direction_elem.find('sound')
        if sound is not None:
            tempo = sound.get('tempo')
            if tempo:
                try:
                    self.current_tempo = int(float(tempo))
                    measure.tempo_bpm = self.current_tempo
                except ValueError:
                    self.logger.log_warning(f"Invalid sound tempo: {tempo}")
    
    def _parse_barline(self, barline_elem: ET.Element, measure: MusicXMLMeasure):
        """Parse barline elements"""
        # Repeat
        repeat = barline_elem.find('repeat')
        if repeat is not None:
            direction = repeat.get('direction')
            if direction == 'forward':
                measure.repeat_start = True
            elif direction == 'backward':
                measure.repeat_end = True
                times = repeat.get('times')
                if times:
                    try:
                        measure.repeat_count = int(times)
                    except ValueError:
                        self.logger.log_warning(f"Invalid repeat count: {times}")
    
    def _parse_note(self, note_elem: ET.Element, measure_num: int, start_time: Fraction) -> Optional[MusicXMLNote]:
        """Parse a single note"""
        # Check if it's a rest
        is_rest = note_elem.find('rest') is not None
        
        # Check if it's a chord note
        is_chord = note_elem.find('chord') is not None
        
        # Parse pitch
        pitch = None
        if not is_rest:
            pitch_elem = note_elem.find('pitch')
            if pitch_elem is not None:
                step = pitch_elem.find('step')
                octave = pitch_elem.find('octave')
                alter = pitch_elem.find('alter')
                
                if step is not None and octave is not None:
                    pitch_str = step.text
                    if alter is not None:
                        alter_val = float(alter.text)
                        if alter_val > 0:
                            pitch_str += '#' * int(alter_val)
                        elif alter_val < 0:
                            pitch_str += 'b' * int(-alter_val)
                    pitch_str += octave.text
                    pitch = pitch_str
        
        # Parse duration
        duration_elem = note_elem.find('duration')
        if duration_elem is None:
            self.logger.log_warning(f"Note missing duration in measure {measure_num}")
            return None
        
        try:
            duration_val = int(duration_elem.text)
            # Convert to quarter notes based on divisions
            # In MusicXML, duration is in divisions per quarter note
            # So duration_val / divisions gives us the duration in quarter notes
            duration = Fraction(duration_val, self.current_divisions)
        except ValueError:
            self.logger.log_warning(f"Invalid duration: {duration_elem.text}")
            return None
        
        # Parse staff
        staff_elem = note_elem.find('staff')
        staff = 1
        if staff_elem is not None:
            try:
                staff = int(staff_elem.text)
            except ValueError:
                self.logger.log_warning(f"Invalid staff: {staff_elem.text}")
        
        # Parse voice
        voice_elem = note_elem.find('voice')
        voice = 1
        if voice_elem is not None:
            try:
                voice = int(voice_elem.text)
            except ValueError:
                self.logger.log_warning(f"Invalid voice: {voice_elem.text}")
        
        # Parse tie
        tie_start = note_elem.find('tie[@type="start"]') is not None
        tie_stop = note_elem.find('tie[@type="stop"]') is not None
        
        return MusicXMLNote(
            pitch=pitch,
            duration=duration,
            measure_number=measure_num,
            staff=staff,
            voice=voice,
            start_time=start_time,
            is_rest=is_rest,
            tie_start=tie_start,
            tie_stop=tie_stop,
            is_chord=is_chord
        )
    
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
        # beats/beat_type gives the duration in terms of whole notes
        # Multiply by 4 to convert to quarter notes
        # For 4/4: 4/4 * 4 = 4 quarter notes
        # For 3/4: 3/4 * 4 = 3 quarter notes  
        # For 2/2: 2/2 * 4 = 4 quarter notes
        return Fraction(beats * 4, beat_type)


class MusicXMLParser:
    """Main MusicXML parser class"""
    
    def __init__(self, log_level=logging.INFO):
        self.logger = MusicXMLLogger(log_level)
    
    def parse_file(self, file_path: str) -> MusicXMLScore:
        """Parse a MusicXML file (.xml, .musicxml, or .mxl)"""
        path = Path(file_path)
        
        if not path.exists():
            raise MusicXMLError(f"File not found: {file_path}")
        
        if path.suffix.lower() == '.mxl':
            xml_content = self._extract_mxl(path)
        else:
            xml_content = path.read_text(encoding='utf-8')
        
        return self.parse_string(xml_content)
    
    def parse_string(self, xml_content: str) -> MusicXMLScore:
        """Parse MusicXML content from string"""
        # Two-pass parsing like MuseScore
        
        # Pass 1: Structure and metadata
        pass1 = MusicXMLParserPass1(self.logger)
        score = pass1.parse(xml_content)
        
        # Pass 2: Detailed content
        pass2 = MusicXMLParserPass2(score, self.logger)
        score = pass2.parse(xml_content)
        
        # Set global score properties from first measure
        self._set_global_properties(score)
        
        # Add any errors to the score
        score.errors = self.logger.errors
        
        self.logger.log_info(f"Parsing completed with {len(score.errors)} errors")
        return score
    
    def _set_global_properties(self, score: MusicXMLScore):
        """Set global score properties from first measure"""
        if score.parts and score.parts[0].measures:
            first_measure = score.parts[0].measures[0]
            score.tempo_bpm = first_measure.tempo_bpm
            score._time_signature = first_measure._time_signature
            score.key_signature = first_measure.key_signature
    
    def _extract_mxl(self, mxl_path: Path) -> str:
        """Extract MusicXML content from compressed .mxl file"""
        try:
            with zipfile.ZipFile(mxl_path, 'r') as zip_file:
                # Find the root file
                container_xml = zip_file.read('META-INF/container.xml').decode('utf-8')
                container_root = ET.fromstring(container_xml)
                
                # Find the rootfile
                rootfile_elem = container_root.find('.//rootfile')
                if rootfile_elem is None:
                    raise MusicXMLError("No rootfile found in container.xml")
                
                rootfile_path = rootfile_elem.get('full-path')
                if not rootfile_path:
                    raise MusicXMLError("Rootfile path not specified")
                
                # Extract the main MusicXML file
                return zip_file.read(rootfile_path).decode('utf-8')
        
        except zipfile.BadZipFile:
            raise MusicXMLError(f"Invalid MXL file: {mxl_path}")
        except KeyError as e:
            raise MusicXMLError(f"Missing file in MXL archive: {e}")


def main():
    """Example usage"""
    parser = MusicXMLParser()
    
    # Parse a file
    try:
        score = parser.parse_file('tests/data/simple_score.xml')
        print(f"Parsed score: {score.title} by {score.composer}")
        print(f"Parts: {len(score.parts)}")
        for part in score.parts:
            print(f"  {part.name}: {len(part.measures)} measures")
    except MusicXMLError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 