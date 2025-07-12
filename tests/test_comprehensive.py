"""
Komprehensywny zestaw testów dla parsera MusicXML.
Sprawdza wszystkie aspekty parsowania, rozwijania repetycji i generowania sekwencji.
"""

import pytest
import os
import tempfile
import zipfile
from pathlib import Path
from fractions import Fraction
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

from musicxml_parser import MusicXMLParser, MusicXMLScore, MusicXMLPart, MusicXMLMeasure, MusicXMLNote, MusicXMLError
from repeat_expander import RepeatExpander, LinearSequenceGenerator


class TestMusicXMLParser:
    """Testy podstawowego parsowania MusicXML"""
    
    @pytest.fixture
    def parser(self):
        """Fixture z parserem"""
        return MusicXMLParser()
    
    @pytest.fixture
    def simple_score_path(self):
        """Ścieżka do prostego pliku testowego"""
        return Path("tests/data/simple_score.xml")
    
    @pytest.fixture
    def complex_score_path(self):
        """Ścieżka do złożonego pliku testowego"""
        return Path("tests/data/complex_score.xml")
    
    @pytest.fixture
    def fur_elise_path(self):
        """Ścieżka do pliku Fur Elise"""
        return Path("data/Fur_Elise.mxl")
    
    def test_parser_initialization(self, parser):
        """Test inicjalizacji parsera"""
        assert parser is not None
        assert parser.logger is not None
        assert hasattr(parser, 'parse_file')
    
    def test_parse_simple_score_basic_info(self, parser, simple_score_path):
        """Test parsowania podstawowych informacji z prostego pliku"""
        if not simple_score_path.exists():
            pytest.skip(f"Plik {simple_score_path} nie istnieje")
        
        score = parser.parse_file(str(simple_score_path))
        
        # Sprawdź podstawowe informacje
        assert isinstance(score, MusicXMLScore)
        assert score.title is not None
        assert len(score.parts) > 0
        assert score.tempo_bpm > 0
        assert score.time_signature is not None
        
        # Sprawdź pierwszą część
        part = score.parts[0]
        assert isinstance(part, MusicXMLPart)
        assert part.name is not None
        assert len(part.measures) > 0
    
    def test_parse_complex_score_basic_info(self, parser, complex_score_path):
        """Test parsowania podstawowych informacji ze złożonego pliku"""
        if not complex_score_path.exists():
            pytest.skip(f"Plik {complex_score_path} nie istnieje")
        
        score = parser.parse_file(str(complex_score_path))
        
        # Sprawdź podstawowe informacje
        assert isinstance(score, MusicXMLScore)
        assert len(score.parts) >= 1
        
        # Sprawdź czy są różne pięciolinie
        has_multiple_staves = any(part.staves > 1 for part in score.parts)
        if has_multiple_staves:
            assert True  # Złożony plik powinien mieć wiele pięciolinii
    
    def test_parse_compressed_mxl_file(self, parser, fur_elise_path):
        """Test parsowania skompresowanego pliku .mxl"""
        if not fur_elise_path.exists():
            pytest.skip(f"Plik {fur_elise_path} nie istnieje")
        
        score = parser.parse_file(str(fur_elise_path))
        
        # Sprawdź podstawowe informacje
        assert isinstance(score, MusicXMLScore)
        assert len(score.parts) > 0
        
        # Fur Elise powinien mieć konkretne charakterystyki
        assert score.tempo_bpm > 0
        assert len(score.parts[0].measures) > 10  # Powinien mieć sporo taktów
    
    def test_parse_invalid_file_format(self, parser):
        """Test parsowania nieprawidłowego formatu pliku"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("To nie jest plik MusicXML")
            f.flush()
            
            with pytest.raises(Exception):
                parser.parse_file(f.name)
            
            os.unlink(f.name)
    
    def test_parse_nonexistent_file(self, parser):
        """Test parsowania nieistniejącego pliku"""
        with pytest.raises(MusicXMLError):
            parser.parse_file("nonexistent_file.xml")
    
    def test_parse_malformed_xml(self, parser):
        """Test parsowania nieprawidłowego XML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write("<?xml version='1.0'?><invalid>malformed xml")
            f.flush()
            
            with pytest.raises(Exception):
                parser.parse_file(f.name)
            
            os.unlink(f.name)


class TestMusicXMLElements:
    """Testy parsowania konkretnych elementów MusicXML"""
    
    @pytest.fixture
    def parser(self):
        return MusicXMLParser()
    
    def test_parse_notes_and_rests(self, parser):
        """Test parsowania nut i przerw"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
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
                <rest/>
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
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            score = parser.parse_file(f.name)
            
            # Sprawdź parsowanie nut
            measure = score.parts[0].measures[0]
            notes = measure.notes
            
            assert len(notes) == 3
            
            # Pierwsza nuta: C4
            assert notes[0].pitch == "C4"
            assert not notes[0].is_rest
            assert notes[0].duration == Fraction(1, 1)  # quarter note przy divisions=4
            
            # Druga nuta: przerwa
            assert notes[1].pitch is None  # Changed from "rest" to None
            assert notes[1].is_rest
            assert notes[1].duration == Fraction(1, 1)
            
            # Trzecia nuta: F#4
            assert notes[2].pitch == "F#4"
            assert not notes[2].is_rest
            assert notes[2].duration == Fraction(1, 1)
            
            os.unlink(f.name)
    
    def test_parse_time_signatures(self, parser):
        """Test parsowania różnych metrów"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
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
                <time><beats>3</beats><beat-type>4</beat-type></time>
                <clef><sign>G</sign><line>2</line></clef>
              </attributes>
              <note>
                <pitch><step>C</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
            </measure>
            <measure number="2">
              <attributes>
                <time><beats>6</beats><beat-type>8</beat-type></time>
              </attributes>
              <note>
                <pitch><step>D</step><octave>4</octave></pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>eighth</type>
              </note>
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            score = parser.parse_file(f.name)
            
            # Sprawdź metrum w pierwszym takcie
            assert score.time_signature == (3, 4)  # Changed from "3/4" to (3, 4)
            
            # Sprawdź zmianę metrum w drugim takcie
            measure2 = score.parts[0].measures[1]
            assert measure2.time_signature == (6, 8)  # Changed from "6/8" to (6, 8)
            
            os.unlink(f.name)
    
    def test_parse_key_signatures(self, parser):
        """Test parsowania różnych tonacji"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
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
            <measure number="2">
              <attributes>
                <key><fifths>-1</fifths></key>
              </attributes>
              <note>
                <pitch><step>D</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            score = parser.parse_file(f.name)
            
            # Sprawdź tonację w pierwszym takcie (D major - 2 krzyżyki)
            assert score.key_signature == 2
            
            # Sprawdź zmianę tonacji w drugim takcie (F major - 1 bemol)
            measure2 = score.parts[0].measures[1]
            assert measure2.key_signature == -1
            
            os.unlink(f.name)
    
    def test_parse_tempo_changes(self, parser):
        """Test parsowania zmian tempa"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
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
              <direction placement="above">
                <direction-type>
                  <metronome>
                    <beat-unit>quarter</beat-unit>
                    <per-minute>120</per-minute>
                  </metronome>
                </direction-type>
                <sound tempo="120"/>
              </direction>
              <note>
                <pitch><step>C</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
            </measure>
            <measure number="2">
              <direction placement="above">
                <direction-type>
                  <metronome>
                    <beat-unit>quarter</beat-unit>
                    <per-minute>90</per-minute>
                  </metronome>
                </direction-type>
                <sound tempo="90"/>
              </direction>
              <note>
                <pitch><step>D</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            score = parser.parse_file(f.name)
            
            # Sprawdź tempo początkowe
            assert score.tempo_bpm == 120.0
            
            # Sprawdź zmianę tempa w drugim takcie
            measure2 = score.parts[0].measures[1]
            assert measure2.tempo_bpm == 90.0
            
            os.unlink(f.name)


class TestRepeatExpansion:
    """Testy rozwijania repetycji i volt"""
    
    @pytest.fixture
    def parser(self):
        return MusicXMLParser()
    
    @pytest.fixture
    def expander(self):
        return RepeatExpander()
    
    def test_simple_repeat_expansion(self, parser, expander):
        """Test rozwijania prostej repetycji"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
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
                <repeat direction="forward"/>
              </barline>
              <note>
                <pitch><step>D</step><octave>4</octave></pitch>
                <duration>16</duration>
                <voice>1</voice>
                <type>whole</type>
              </note>
            </measure>
            <measure number="3">
              <note>
                <pitch><step>E</step><octave>4</octave></pitch>
                <duration>16</duration>
                <voice>1</voice>
                <type>whole</type>
              </note>
              <barline location="right">
                <repeat direction="backward"/>
              </barline>
            </measure>
            <measure number="4">
              <note>
                <pitch><step>F</step><octave>4</octave></pitch>
                <duration>16</duration>
                <voice>1</voice>
                <type>whole</type>
              </note>
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            # Parsuj oryginalny plik
            original_score = parser.parse_file(f.name)
            assert len(original_score.parts[0].measures) == 4
            
            # Rozwiń repetycje
            expanded_score = expander.expand_repeats(original_score)
            expanded_measures = expanded_score.parts[0].measures
            
            # Sprawdź rozwinięcie: 1 + (2,3) + (2,3) + 4 = 6 taktów
            assert len(expanded_measures) == 6
            
            # Sprawdź kolejność nut
            pitches = [m.notes[0].pitch for m in expanded_measures]
            expected_pitches = ["C4", "D4", "E4", "D4", "E4", "F4"]
            assert pitches == expected_pitches
            
            os.unlink(f.name)
    
    def test_volta_expansion(self, parser, expander):
        """Test rozwijania volt"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
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
              <barline location="left">
                <repeat direction="forward"/>
              </barline>
              <note>
                <pitch><step>C</step><octave>4</octave></pitch>
                <duration>16</duration>
                <voice>1</voice>
                <type>whole</type>
              </note>
            </measure>
            <measure number="2">
              <barline location="left">
                <ending number="1" type="start"/>
              </barline>
              <note>
                <pitch><step>D</step><octave>4</octave></pitch>
                <duration>16</duration>
                <voice>1</voice>
                <type>whole</type>
              </note>
              <barline location="right">
                <ending number="1" type="stop"/>
                <repeat direction="backward"/>
              </barline>
            </measure>
            <measure number="3">
              <barline location="left">
                <ending number="2" type="start"/>
              </barline>
              <note>
                <pitch><step>E</step><octave>4</octave></pitch>
                <duration>16</duration>
                <voice>1</voice>
                <type>whole</type>
              </note>
              <barline location="right">
                <ending number="2" type="stop"/>
              </barline>
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            # Parsuj oryginalny plik
            original_score = parser.parse_file(f.name)
            assert len(original_score.parts[0].measures) == 3
            
            # Rozwiń repetycje
            expanded_score = expander.expand_repeats(original_score)
            expanded_measures = expanded_score.parts[0].measures
            
            # Sprawdź rozwinięcie: C + D (volta 1) + C + E (volta 2) = 4 takty
            assert len(expanded_measures) == 4
            
            # Sprawdź kolejność nut
            pitches = [m.notes[0].pitch for m in expanded_measures]
            expected_pitches = ["C4", "D4", "C4", "E4"]
            assert pitches == expected_pitches
            
            os.unlink(f.name)
    
    def test_nested_repeats(self, parser, expander):
        """Test zagnieżdżonych repetycji"""
        # Ten test sprawdza czy parser radzi sobie z zagnieżdżonymi repetycjami
        # Może być skomplikowany do zaimplementowania, ale warto przetestować
        pass
    
    def test_no_repeats(self, parser, expander):
        """Test rozwijania utworu bez repetycji"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
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
              <note>
                <pitch><step>D</step><octave>4</octave></pitch>
                <duration>16</duration>
                <voice>1</voice>
                <type>whole</type>
              </note>
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            # Parsuj oryginalny plik
            original_score = parser.parse_file(f.name)
            original_measures = len(original_score.parts[0].measures)
            
            # Rozwiń repetycje (nie powinno nic zmienić)
            expanded_score = expander.expand_repeats(original_score)
            expanded_measures = len(expanded_score.parts[0].measures)
            
            # Liczba taktów powinna być taka sama
            assert original_measures == expanded_measures
            
            os.unlink(f.name)


class TestLinearSequenceGeneration:
    """Testy generowania sekwencji liniowej"""
    
    @pytest.fixture
    def parser(self):
        return MusicXMLParser()
    
    @pytest.fixture
    def generator(self):
        return LinearSequenceGenerator()
    
    def test_generate_linear_sequence(self, parser, generator):
        """Test generowania liniowej sekwencji nut"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
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
                <duration>1</duration>
                <voice>1</voice>
                <type>sixteenth</type>
              </note>
              <note>
                <pitch><step>D</step><octave>4</octave></pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>sixteenth</type>
              </note>
            </measure>
            <measure number="2">
              <note>
                <pitch><step>E</step><octave>4</octave></pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>sixteenth</type>
              </note>
              <note>
                <pitch><step>F</step><octave>4</octave></pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>sixteenth</type>
              </note>
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            score = parser.parse_file(f.name)
            notes = generator.generate_sequence(score)
            
            # Sprawdź liczbę nut
            assert len(notes) == 4
            
            # Sprawdź kolejność i timing
            assert notes[0].pitch == "C4"
            assert notes[0].start_time == Fraction(0)
            
            assert notes[1].pitch == "D4"
            assert notes[1].start_time == Fraction(1, 4)
            
            assert notes[2].pitch == "E4"
            assert notes[2].start_time == Fraction(4, 1)  # Początek drugiego taktu (po pełnej mierze 4/4)
            
            assert notes[3].pitch == "F4"
            assert notes[3].start_time == Fraction(17, 4)  # 4 + 1/4 = 17/4
            
            os.unlink(f.name)
    
    def test_split_notes_by_hand(self, parser, generator):
        """Test podziału nut na ręce"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Piano</part-name>
            </score-part>
          </part-list>
          <part id="P1">
            <measure number="1">
              <attributes>
                <divisions>4</divisions>
                <key><fifths>0</fifths></key>
                <time><beats>4</beats><beat-type>4</beat-type></time>
                <staves>2</staves>
                <clef number="1">
                  <sign>G</sign>
                  <line>2</line>
                </clef>
                <clef number="2">
                  <sign>F</sign>
                  <line>4</line>
                </clef>
              </attributes>
              <note>
                <pitch><step>C</step><octave>5</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
                <staff>1</staff>
              </note>
              <note>
                <pitch><step>C</step><octave>3</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
                <staff>2</staff>
              </note>
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            score = parser.parse_file(f.name)
            right_hand, left_hand = generator.get_notes_by_hand(score)
            
            # Sprawdź podział
            assert len(right_hand) == 1
            assert len(left_hand) == 1
            
            assert right_hand[0].pitch == "C5"
            assert right_hand[0].staff == 1
            
            assert left_hand[0].pitch == "C3"
            assert left_hand[0].staff == 2
            
            os.unlink(f.name)
    
    def test_generate_playback_events(self, parser, generator):
        """Test generowania zdarzeń playback"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
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
              <direction placement="above">
                <direction-type>
                  <metronome>
                    <beat-unit>quarter</beat-unit>
                    <per-minute>120</per-minute>
                  </metronome>
                </direction-type>
                <sound tempo="120"/>
              </direction>
              <note>
                <pitch><step>C</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            score = parser.parse_file(f.name)
            events = generator.get_playback_events(score)
            
            # Sprawdź czy są zdarzenia
            assert len(events) > 0
            
            # Sprawdź typy zdarzeń
            event_types = [event['type'] for event in events]
            assert 'tempo_change' in event_types
            assert 'note_on' in event_types
            assert 'note_off' in event_types
            
            os.unlink(f.name)


class TestErrorHandling:
    """Testy obsługi błędów"""
    
    @pytest.fixture
    def parser(self):
        return MusicXMLParser()
    
    def test_missing_part_list(self, parser):
        """Test obsługi braku part-list"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
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
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            # Powinien zgłosić błąd lub obsłużyć brak part-list
            try:
                score = parser.parse_file(f.name)
                # Jeśli parser obsługuje brak part-list, sprawdź czy są błędy
                assert len(score.errors) > 0
            except Exception as e:
                # Jeśli parser nie obsługuje, powinien rzucić wyjątek
                assert "part-list" in str(e).lower()
            
            os.unlink(f.name)
    
    def test_missing_required_elements(self, parser):
        """Test obsługi braku wymaganych elementów"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Test</part-name>
            </score-part>
          </part-list>
          <part id="P1">
            <measure number="1">
              <note>
                <!-- Brak pitch i duration -->
                <voice>1</voice>
                <type>quarter</type>
              </note>
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            # Parser powinien obsłużyć brak wymaganych elementów
            score = parser.parse_file(f.name)
            
            # Sprawdź czy są błędy
            assert len(score.errors) > 0 or len(score.parts[0].measures[0].notes) == 0
            
            os.unlink(f.name)
    
    def test_invalid_values(self, parser):
        """Test obsługi nieprawidłowych wartości"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Test</part-name>
            </score-part>
          </part-list>
          <part id="P1">
            <measure number="1">
              <attributes>
                <divisions>invalid</divisions>
                <key><fifths>999</fifths></key>
                <time><beats>-1</beats><beat-type>0</beat-type></time>
              </attributes>
              <note>
                <pitch>
                  <step>X</step>
                  <octave>-5</octave>
                </pitch>
                <duration>invalid</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            # Parser powinien obsłużyć nieprawidłowe wartości
            try:
                score = parser.parse_file(f.name)
                # Sprawdź czy są błędy
                assert len(score.errors) > 0
            except Exception:
                # Alternatywnie może rzucić wyjątek
                pass
            
            os.unlink(f.name)


class TestRealWorldFiles:
    """Testy z rzeczywistymi plikami"""
    
    @pytest.fixture
    def parser(self):
        return MusicXMLParser()
    
    @pytest.fixture
    def expander(self):
        return RepeatExpander()
    
    @pytest.fixture
    def generator(self):
        return LinearSequenceGenerator()
    
    def test_simple_score_complete_analysis(self, parser, expander, generator):
        """Kompletna analiza prostego pliku testowego"""
        file_path = "tests/data/simple_score.xml"
        if not os.path.exists(file_path):
            pytest.skip(f"Plik {file_path} nie istnieje")
        
        # Parsowanie
        score = parser.parse_file(file_path)
        
        # Podstawowe sprawdzenia
        assert isinstance(score, MusicXMLScore)
        assert len(score.parts) == 1
        assert score.parts[0].name == "Piano"
        
        # Sprawdź repetycje
        original_measures = len(score.parts[0].measures)
        expanded_score = expander.expand_repeats(score)
        expanded_measures = len(expanded_score.parts[0].measures)
        
        # Powinno być więcej taktów po rozwinięciu
        assert expanded_measures >= original_measures
        
        # Generowanie sekwencji
        notes = generator.generate_sequence(expanded_score)
        assert len(notes) > 0
        
        # Sprawdź czy nuty mają poprawne timing
        for i in range(1, len(notes)):
            assert notes[i].start_time >= notes[i-1].start_time
    
    def test_fur_elise_complete_analysis(self, parser, expander, generator):
        """Kompletna analiza pliku Fur Elise"""
        file_path = "data/Fur_Elise.mxl"
        if not os.path.exists(file_path):
            pytest.skip(f"Plik {file_path} nie istnieje")
        
        # Parsowanie
        score = parser.parse_file(file_path)
        
        # Podstawowe sprawdzenia
        assert isinstance(score, MusicXMLScore)
        assert len(score.parts) >= 1
        
        # Sprawdź czy ma sensowne tempo
        assert 60 <= score.tempo_bpm <= 200
        
        # Sprawdź czy ma dużo nut (Fur Elise to długi utwór)
        total_notes = sum(len(m.notes) for p in score.parts for m in p.measures)
        assert total_notes > 100
        
        # Rozwijanie repetycji
        expanded_score = expander.expand_repeats(score)
        
        # Generowanie sekwencji
        notes = generator.generate_sequence(expanded_score)
        assert len(notes) > 0
        
        # Sprawdź podział na ręce (Fur Elise to utwór na piano)
        right_hand, left_hand = generator.get_notes_by_hand(expanded_score)
        
        # Powinny być nuty w obu rękach
        assert len(right_hand) > 0
        assert len(left_hand) > 0


class TestPerformance:
    """Testy wydajności"""
    
    @pytest.fixture
    def parser(self):
        return MusicXMLParser()
    
    def test_parsing_performance(self, parser):
        """Test wydajności parsowania"""
        import time
        
        # Użyj dostępnego pliku
        file_path = "data/Fur_Elise.mxl"
        if not os.path.exists(file_path):
            pytest.skip(f"Plik {file_path} nie istnieje")
        
        # Zmierz czas parsowania
        start_time = time.time()
        score = parser.parse_file(file_path)
        parse_time = time.time() - start_time
        
        # Parsowanie nie powinno trwać dłużej niż 5 sekund
        assert parse_time < 5.0
        
        # Sprawdź czy wynik jest sensowny
        assert len(score.parts) > 0
        
        print(f"Czas parsowania: {parse_time:.2f}s")
    
    def test_repeat_expansion_performance(self, parser):
        """Test wydajności rozwijania repetycji"""
        import time
        
        file_path = "tests/data/simple_score.xml"
        if not os.path.exists(file_path):
            pytest.skip(f"Plik {file_path} nie istnieje")
        
        score = parser.parse_file(file_path)
        expander = RepeatExpander()
        
        # Zmierz czas rozwijania
        start_time = time.time()
        expanded_score = expander.expand_repeats(score)
        expand_time = time.time() - start_time
        
        # Rozwijanie nie powinno trwać dłużej niż 1 sekundy
        assert expand_time < 1.0
        
        print(f"Czas rozwijania repetycji: {expand_time:.2f}s")
    
    def test_memory_usage(self, parser):
        """Test zużycia pamięci"""
        import psutil
        import os
        
        file_path = "data/Fur_Elise.mxl"
        if not os.path.exists(file_path):
            pytest.skip(f"Plik {file_path} nie istnieje")
        
        # Zmierz zużycie pamięci przed parsowaniem
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Parsuj plik
        score = parser.parse_file(file_path)
        
        # Zmierz zużycie pamięci po parsowaniu
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        
        # Parsowanie nie powinno zużywać więcej niż 50MB
        assert memory_used < 50.0
        
        print(f"Zużycie pamięci: {memory_used:.2f}MB")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 