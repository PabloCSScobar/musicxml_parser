#!/usr/bin/env python3
"""
Comprehensive tests for MusicXML Parser

These tests are inspired by MuseScore's test suite and cover:
- Basic parsing functionality
- Repeat and volta handling
- Tempo and time signature changes
- Multi-staff parts
- Error handling
"""

import pytest
import tempfile
import os
from pathlib import Path
from fractions import Fraction

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from musicxml_parser import (
    MusicXMLParser, MusicXMLScore, MusicXMLPart, MusicXMLMeasure, 
    MusicXMLNote, MusicXMLError, EndingType
)
from repeat_expander import RepeatExpander, LinearSequenceGenerator


class TestMusicXMLParser:
    """Test cases for MusicXML parser"""
    
    def setup_method(self):
        """Setup for each test"""
        self.parser = MusicXMLParser()
        self.test_data_dir = Path(__file__).parent / 'data'
    
    def test_parse_simple_score(self):
        """Test parsing a simple score without repeats"""
        score = self.parser.parse_file(str(self.test_data_dir / 'simple_score.xml'))
        
        # Check basic score info
        assert score.title == "Simple Test Score"
        assert score.composer == "Test Creator"
        assert len(score.parts) == 1
        
        # Check part info
        part = score.parts[0]
        assert part.name == "Piano"
        assert part.instrument == "Piano"
        assert part.id == "P1"
        assert len(part.measures) == 5
        
        # Check first measure
        measure1 = part.measures[0]
        assert measure1.number == 1
        assert measure1.time_signature == (4, 4)
        assert measure1.key_signature == 0
        assert measure1.divisions == 4
        assert not measure1.repeat_start
        assert not measure1.repeat_end
        assert len(measure1.notes) == 1
        
        # Check first note
        note1 = measure1.notes[0]
        assert note1.pitch == "C4"
        assert note1.duration == Fraction(4, 1)  # whole note = 4 quarter notes
        assert note1.staff == 1
        assert note1.voice == 1
        assert not note1.is_rest
    
    def test_parse_complex_score(self):
        """Test parsing a complex score with multiple staves and tempo changes"""
        score = self.parser.parse_file(str(self.test_data_dir / 'complex_score.xml'))
        
        # Check basic info
        assert score.title == "Complex Test Score"
        assert len(score.parts) == 1
        
        part = score.parts[0]
        assert part.staves == 2  # Piano has 2 staves
        assert len(part.measures) == 3
        
        # Check first measure - should have tempo 120
        measure1 = part.measures[0]
        assert measure1.tempo_bpm == 120
        assert measure1.time_signature == (4, 4)
        
        # Check second measure - should have tempo 100
        measure2 = part.measures[1]
        assert measure2.tempo_bpm == 100
        
        # Check third measure - should have time signature 3/4
        measure3 = part.measures[2]
        assert measure3.time_signature == (3, 4)
        
        # Check staff distribution
        all_notes = []
        for measure in part.measures:
            all_notes.extend(measure.notes)
        
        right_hand_notes = [n for n in all_notes if n.staff == 1]
        left_hand_notes = [n for n in all_notes if n.staff == 2]
        
        assert len(right_hand_notes) > 0
        assert len(left_hand_notes) > 0
    
    def test_parse_repeats_and_voltas(self):
        """Test parsing repeats and voltas"""
        score = self.parser.parse_file(str(self.test_data_dir / 'simple_score.xml'))
        part = score.parts[0]
        
        # Check repeat structure
        measure2 = part.measures[1]  # Should have repeat start
        assert measure2.repeat_start
        
        measure3 = part.measures[2]  # Should have volta 1 and repeat end
        assert measure3.repeat_end
        assert 1 in measure3.ending_numbers
        assert measure3.ending_type == EndingType.STOP
        
        measure4 = part.measures[3]  # Should have volta 2
        assert 2 in measure4.ending_numbers
        assert measure4.ending_type == EndingType.START
    
    def test_pitch_parsing(self):
        """Test pitch parsing including accidentals"""
        # Create a test XML with various pitches
        test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
            <part-list>
                <score-part id="P1">
                    <part-name>Test</part-name>
                </score-part>
            </part-list>
            <part id="P1">
                <measure number="1">
                    <attributes>
                        <divisions>4</divisions>
                        <key><fifths>0</fifths></key>
                        <time><beats>4</beats><beat-type>4</beat-type></time>
                        <clef><sign>G</sign><line>2</line></clef>
                    </attributes>
                    <note>
                        <pitch>
                            <step>C</step>
                            <octave>4</octave>
                        </pitch>
                        <duration>4</duration>
                        <voice>1</voice>
                        <type>quarter</type>
                    </note>
                    <note>
                        <pitch>
                            <step>F</step>
                            <alter>1</alter>
                            <octave>4</octave>
                        </pitch>
                        <duration>4</duration>
                        <voice>1</voice>
                        <type>quarter</type>
                    </note>
                    <note>
                        <pitch>
                            <step>B</step>
                            <alter>-1</alter>
                            <octave>4</octave>
                        </pitch>
                        <duration>4</duration>
                        <voice>1</voice>
                        <type>quarter</type>
                    </note>
                    <note>
                        <rest/>
                        <duration>4</duration>
                        <voice>1</voice>
                        <type>quarter</type>
                    </note>
                </measure>
            </part>
        </score-partwise>'''
        
        score = self.parser.parse_string(test_xml)
        notes = score.parts[0].measures[0].notes
        
        assert len(notes) == 4
        assert notes[0].pitch == "C4"
        assert notes[1].pitch == "F#4"
        assert notes[2].pitch == "Bb4"
        assert notes[3].is_rest
        assert notes[3].pitch is None
    
    def test_duration_calculation(self):
        """Test duration calculation with different divisions"""
        test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
            <part-list>
                <score-part id="P1">
                    <part-name>Test</part-name>
                </score-part>
            </part-list>
            <part id="P1">
                <measure number="1">
                    <attributes>
                        <divisions>2</divisions>
                        <key><fifths>0</fifths></key>
                        <time><beats>4</beats><beat-type>4</beat-type></time>
                        <clef><sign>G</sign><line>2</line></clef>
                    </attributes>
                    <note>
                        <pitch><step>C</step><octave>4</octave></pitch>
                        <duration>8</duration>
                        <voice>1</voice>
                        <type>whole</type>
                    </note>
                </measure>
                <measure number="2">
                    <attributes>
                        <divisions>4</divisions>
                    </attributes>
                    <note>
                        <pitch><step>D</step><octave>4</octave></pitch>
                        <duration>4</duration>
                        <voice>1</voice>
                        <type>quarter</type>
                    </note>
                </measure>
            </part>
        </score-partwise>'''
        
        score = self.parser.parse_string(test_xml)
        
        # First measure: divisions=2, duration=8 -> 8/2 = 4 quarter notes
        note1 = score.parts[0].measures[0].notes[0]
        assert note1.duration == Fraction(4, 1)
        
        # Second measure: divisions=4, duration=4 -> 4/4 = 1 quarter note
        note2 = score.parts[0].measures[1].notes[0]
        assert note2.duration == Fraction(1, 1)
    
    def test_error_handling(self):
        """Test error handling for invalid XML"""
        # Test invalid XML
        with pytest.raises(MusicXMLError):
            self.parser.parse_string("<invalid>xml</invalid>")
        
        # Test file not found
        with pytest.raises(MusicXMLError):
            self.parser.parse_file("nonexistent.xml")
        
        # Test missing part-list
        invalid_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
            <part id="P1">
                <measure number="1">
                    <note>
                        <pitch><step>C</step><octave>4</octave></pitch>
                        <duration>4</duration>
                        <voice>1</voice>
                        <type>quarter</type>
                    </note>
                </measure>
            </part>
        </score-partwise>'''
        
        with pytest.raises(MusicXMLError):
            self.parser.parse_string(invalid_xml)
    
    def test_mxl_file_parsing(self):
        """Test parsing compressed MXL files"""
        # This would require creating a test MXL file
        # For now, we'll test the error handling
        with pytest.raises(MusicXMLError):
            self.parser.parse_file("nonexistent.mxl")
    
    def test_time_signature_changes(self):
        """Test handling of time signature changes"""
        test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
            <part-list>
                <score-part id="P1">
                    <part-name>Test</part-name>
                </score-part>
            </part-list>
            <part id="P1">
                <measure number="1">
                    <attributes>
                        <divisions>4</divisions>
                        <key><fifths>0</fifths></key>
                        <time><beats>4</beats><beat-type>4</beat-type></time>
                        <clef><sign>G</sign><line>2</line></clef>
                    </attributes>
                    <note>
                        <pitch><step>C</step><octave>4</octave></pitch>
                        <duration>16</duration>
                        <voice>1</voice>
                        <type>whole</type>
                    </note>
                </measure>
                <measure number="2">
                    <attributes>
                        <time><beats>3</beats><beat-type>4</beat-type></time>
                    </attributes>
                    <note>
                        <pitch><step>D</step><octave>4</octave></pitch>
                        <duration>12</duration>
                        <voice>1</voice>
                        <type>half</type>
                        <dot/>
                    </note>
                </measure>
            </part>
        </score-partwise>'''
        
        score = self.parser.parse_string(test_xml)
        
        assert score.parts[0].measures[0].time_signature == (4, 4)
        assert score.parts[0].measures[1].time_signature == (3, 4)
    
    def test_key_signature_parsing(self):
        """Test key signature parsing"""
        test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
            <part-list>
                <score-part id="P1">
                    <part-name>Test</part-name>
                </score-part>
            </part-list>
            <part id="P1">
                <measure number="1">
                    <attributes>
                        <divisions>4</divisions>
                        <key><fifths>2</fifths></key>
                        <time><beats>4</beats><beat-type>4</beat-type></time>
                        <clef><sign>G</sign><line>2</line></clef>
                    </attributes>
                    <note>
                        <pitch><step>C</step><octave>4</octave></pitch>
                        <duration>4</duration>
                        <voice>1</voice>
                        <type>quarter</type>
                    </note>
                </measure>
            </part>
        </score-partwise>'''
        
        score = self.parser.parse_string(test_xml)
        assert score.parts[0].measures[0].key_signature == 2  # D major (2 sharps)


class TestRepeatExpander:
    """Test cases for repeat expansion"""
    
    def setup_method(self):
        """Setup for each test"""
        self.parser = MusicXMLParser()
        self.expander = RepeatExpander()
        self.test_data_dir = Path(__file__).parent / 'data'
    
    def test_expand_simple_repeat(self):
        """Test expanding a simple repeat without voltas"""
        # Create a simple repeat structure
        test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
            <part-list>
                <score-part id="P1">
                    <part-name>Test</part-name>
                </score-part>
            </part-list>
            <part id="P1">
                <measure number="1">
                    <attributes>
                        <divisions>4</divisions>
                        <key><fifths>0</fifths></key>
                        <time><beats>4</beats><beat-type>4</beat-type></time>
                        <clef><sign>G</sign><line>2</line></clef>
                    </attributes>
                    <note>
                        <pitch><step>C</step><octave>4</octave></pitch>
                        <duration>16</duration>
                        <voice>1</voice>
                        <type>whole</type>
                    </note>
                </measure>
                <measure number="2">
                    <barline location="left">
                        <bar-style>heavy-light</bar-style>
                        <repeat direction="forward"/>
                    </barline>
                    <note>
                        <pitch><step>D</step><octave>4</octave></pitch>
                        <duration>16</duration>
                        <voice>1</voice>
                        <type>whole</type>
                    </note>
                    <barline location="right">
                        <bar-style>light-heavy</bar-style>
                        <repeat direction="backward"/>
                    </barline>
                </measure>
            </part>
        </score-partwise>'''
        
        score = self.parser.parse_string(test_xml)
        original_measures = len(score.parts[0].measures)
        
        expanded_score = self.expander.expand_repeats(score)
        expanded_measures = len(expanded_score.parts[0].measures)
        
        # Should have expanded the repeat
        assert expanded_measures > original_measures
    
    def test_expand_volta_repeat(self):
        """Test expanding repeats with voltas"""
        score = self.parser.parse_file(str(self.test_data_dir / 'simple_score.xml'))
        original_measures = len(score.parts[0].measures)
        
        expanded_score = self.expander.expand_repeats(score)
        expanded_measures = len(expanded_score.parts[0].measures)
        
        # Should have expanded the repeat with voltas
        assert expanded_measures > original_measures
    
    def test_no_repeats(self):
        """Test that scores without repeats are handled correctly"""
        test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
            <part-list>
                <score-part id="P1">
                    <part-name>Test</part-name>
                </score-part>
            </part-list>
            <part id="P1">
                <measure number="1">
                    <attributes>
                        <divisions>4</divisions>
                        <key><fifths>0</fifths></key>
                        <time><beats>4</beats><beat-type>4</beat-type></time>
                        <clef><sign>G</sign><line>2</line></clef>
                    </attributes>
                    <note>
                        <pitch><step>C</step><octave>4</octave></pitch>
                        <duration>16</duration>
                        <voice>1</voice>
                        <type>whole</type>
                    </note>
                </measure>
            </part>
        </score-partwise>'''
        
        score = self.parser.parse_string(test_xml)
        original_measures = len(score.parts[0].measures)
        
        expanded_score = self.expander.expand_repeats(score)
        expanded_measures = len(expanded_score.parts[0].measures)
        
        # Should be the same number of measures
        assert expanded_measures == original_measures


class TestLinearSequenceGenerator:
    """Test cases for linear sequence generation"""
    
    def setup_method(self):
        """Setup for each test"""
        self.parser = MusicXMLParser()
        self.generator = LinearSequenceGenerator()
        self.test_data_dir = Path(__file__).parent / 'data'
    
    def test_generate_sequence(self):
        """Test generating a linear sequence of notes"""
        score = self.parser.parse_file(str(self.test_data_dir / 'simple_score.xml'))
        notes = self.generator.generate_sequence(score)
        
        assert len(notes) > 0
        
        # Check that notes are sorted by start time
        for i in range(1, len(notes)):
            assert notes[i].start_time >= notes[i-1].start_time
    
    def test_notes_by_hand(self):
        """Test separating notes by hand"""
        score = self.parser.parse_file(str(self.test_data_dir / 'complex_score.xml'))
        right_hand, left_hand = self.generator.get_notes_by_hand(score)
        
        # Should have notes in both hands
        assert len(right_hand) > 0
        assert len(left_hand) > 0
        
        # Check staff assignments
        for note in right_hand:
            assert note.staff == 1
        
        for note in left_hand:
            assert note.staff == 2
    
    def test_playback_events(self):
        """Test generating playback events"""
        score = self.parser.parse_file(str(self.test_data_dir / 'complex_score.xml'))
        events = self.generator.get_playback_events(score)
        
        assert len(events) > 0
        
        # Check that events are sorted by time
        for i in range(1, len(events)):
            assert events[i]['time'] >= events[i-1]['time']
        
        # Check for different event types
        event_types = {event['type'] for event in events}
        assert 'note_on' in event_types
        assert 'note_off' in event_types
        
        # Should have tempo changes
        tempo_events = [e for e in events if e['type'] == 'tempo_change']
        assert len(tempo_events) > 0


class TestIntegration:
    """Integration tests combining parser and expander"""
    
    def setup_method(self):
        """Setup for each test"""
        self.parser = MusicXMLParser()
        self.expander = RepeatExpander()
        self.generator = LinearSequenceGenerator()
        self.test_data_dir = Path(__file__).parent / 'data'
    
    def test_full_pipeline(self):
        """Test the complete pipeline: parse -> expand -> generate sequence"""
        # Parse
        score = self.parser.parse_file(str(self.test_data_dir / 'simple_score.xml'))
        assert len(score.parts) > 0
        
        # Expand repeats
        expanded_score = self.expander.expand_repeats(score)
        assert len(expanded_score.parts) > 0
        
        # Generate sequence
        notes = self.generator.generate_sequence(expanded_score)
        assert len(notes) > 0
        
        # Generate playback events
        events = self.generator.get_playback_events(expanded_score)
        assert len(events) > 0
    
    def test_error_propagation(self):
        """Test that errors are properly propagated through the pipeline"""
        # Test with invalid file
        with pytest.raises(MusicXMLError):
            score = self.parser.parse_file("nonexistent.xml")
    
    def test_consistency_checks(self):
        """Test consistency between different representations"""
        score = self.parser.parse_file(str(self.test_data_dir / 'complex_score.xml'))
        expanded_score = self.expander.expand_repeats(score)
        
        # Check that all parts are preserved
        assert len(expanded_score.parts) == len(score.parts)
        
        # Check that metadata is preserved
        assert expanded_score.title == score.title
        assert expanded_score.composer == score.composer
        
        # Generate sequences
        notes = self.generator.generate_sequence(expanded_score)
        right_hand, left_hand = self.generator.get_notes_by_hand(expanded_score)
        
        # Check that hand separation is consistent
        assert len(notes) == len(right_hand) + len(left_hand)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 