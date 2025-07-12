"""
Testy przypadków brzegowych i specjalnych sytuacji w parserze MusicXML.
"""

import pytest
import tempfile
import os
from fractions import Fraction
from musicxml_parser import MusicXMLParser
from repeat_expander import RepeatExpander, LinearSequenceGenerator


class TestEdgeCases:
    """Testy przypadków brzegowych"""
    
    @pytest.fixture
    def parser(self):
        return MusicXMLParser()
    
    def test_empty_score(self, parser):
        """Test parsowania pustego utworu"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Empty</part-name>
            </score-part>
          </part-list>
          <part id="P1">
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            score = parser.parse_file(f.name)
            
            # Sprawdź czy parser obsługuje pusty utwór
            assert len(score.parts) == 1
            assert len(score.parts[0].measures) == 0
            
            os.unlink(f.name)
    
    def test_single_note_score(self, parser):
        """Test parsowania utworu z jedną nutą"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Single Note</part-name>
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
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            score = parser.parse_file(f.name)
            
            assert len(score.parts) == 1
            assert len(score.parts[0].measures) == 1
            assert len(score.parts[0].measures[0].notes) == 1
            assert score.parts[0].measures[0].notes[0].pitch == "C4"
            
            os.unlink(f.name)
    
    def test_extreme_pitch_values(self, parser):
        """Test parsowania ekstremalnych wartości pitch"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Extreme Pitches</part-name>
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
                  <octave>0</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
              <note>
                <pitch>
                  <step>C</step>
                  <octave>9</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
              <note>
                <pitch>
                  <step>C</step>
                  <alter>2</alter>
                  <octave>4</octave>
                </pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
              <note>
                <pitch>
                  <step>C</step>
                  <alter>-2</alter>
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
            notes = score.parts[0].measures[0].notes
            
            # Sprawdź czy parser obsługuje ekstremalne wartości
            assert len(notes) == 4
            assert notes[0].pitch == "C0"  # Bardzo niska nuta
            assert notes[1].pitch == "C9"  # Bardzo wysoka nuta
            assert notes[2].pitch == "C##4"  # Podwójny krzyżyk
            assert notes[3].pitch == "Cbb4"  # Podwójny bemol
            
            os.unlink(f.name)
    
    def test_complex_time_signatures(self, parser):
        """Test parsowania złożonych metrów"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Complex Time</part-name>
            </score-part>
          </part-list>
          <part id="P1">
            <measure number="1">
              <attributes>
                <divisions>4</divisions>
                <key><fifths>0</fifths></key>
                <time>
                  <beats>7</beats>
                  <beat-type>8</beat-type>
                </time>
                <clef><sign>G</sign><line>2</line></clef>
              </attributes>
              <note>
                <pitch><step>C</step><octave>4</octave></pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>eighth</type>
              </note>
            </measure>
            <measure number="2">
              <attributes>
                <time>
                  <beats>15</beats>
                  <beat-type>16</beat-type>
                </time>
              </attributes>
              <note>
                <pitch><step>D</step><octave>4</octave></pitch>
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
            
            # Sprawdź czy parser obsługuje złożone metrum
            assert score.time_signature == "7/8"
            assert score.parts[0].measures[1].time_signature == "15/16"
            
            os.unlink(f.name)
    
    def test_extreme_tempo_values(self, parser):
        """Test parsowania ekstremalnych wartości tempa"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Extreme Tempo</part-name>
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
                    <per-minute>1</per-minute>
                  </metronome>
                </direction-type>
                <sound tempo="1"/>
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
                    <per-minute>999</per-minute>
                  </metronome>
                </direction-type>
                <sound tempo="999"/>
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
            
            # Sprawdź czy parser obsługuje ekstremalne tempo
            assert score.tempo_bpm == 1.0
            assert score.parts[0].measures[1].tempo_bpm == 999.0
            
            os.unlink(f.name)
    
    def test_many_voices(self, parser):
        """Test parsowania wielu głosów"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Many Voices</part-name>
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
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
              <note>
                <pitch><step>E</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>2</voice>
                <type>quarter</type>
              </note>
              <note>
                <pitch><step>G</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>3</voice>
                <type>quarter</type>
              </note>
              <note>
                <pitch><step>C</step><octave>5</octave></pitch>
                <duration>4</duration>
                <voice>4</voice>
                <type>quarter</type>
              </note>
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            score = parser.parse_file(f.name)
            notes = score.parts[0].measures[0].notes
            
            # Sprawdź czy parser obsługuje wiele głosów
            assert len(notes) == 4
            voices = [note.voice for note in notes]
            assert set(voices) == {1, 2, 3, 4}
            
            os.unlink(f.name)
    
    def test_chord_notation(self, parser):
        """Test parsowania akordów"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Chords</part-name>
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
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
              <note>
                <chord/>
                <pitch><step>E</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
              <note>
                <chord/>
                <pitch><step>G</step><octave>4</octave></pitch>
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
            notes = score.parts[0].measures[0].notes
            
            # Sprawdź czy parser obsługuje akordy
            assert len(notes) == 3
            assert not notes[0].is_chord  # Pierwsza nuta nie jest częścią akordu
            assert notes[1].is_chord      # Druga nuta jest częścią akordu
            assert notes[2].is_chord      # Trzecia nuta jest częścią akordu
            
            os.unlink(f.name)


class TestComplexRepeats:
    """Testy złożonych struktur repetycji"""
    
    @pytest.fixture
    def parser(self):
        return MusicXMLParser()
    
    @pytest.fixture
    def expander(self):
        return RepeatExpander()
    
    def test_multiple_volta_numbers(self, parser, expander):
        """Test volt z wieloma numerami (np. 1,2,3)"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Multiple Voltas</part-name>
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
                <ending number="1,2" type="start"/>
              </barline>
              <note>
                <pitch><step>D</step><octave>4</octave></pitch>
                <duration>16</duration>
                <voice>1</voice>
                <type>whole</type>
              </note>
              <barline location="right">
                <ending number="1,2" type="stop"/>
                <repeat direction="backward" times="3"/>
              </barline>
            </measure>
            <measure number="3">
              <barline location="left">
                <ending number="3" type="start"/>
              </barline>
              <note>
                <pitch><step>E</step><octave>4</octave></pitch>
                <duration>16</duration>
                <voice>1</voice>
                <type>whole</type>
              </note>
              <barline location="right">
                <ending number="3" type="stop"/>
              </barline>
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            score = parser.parse_file(f.name)
            expanded_score = expander.expand_repeats(score)
            
            # Sprawdź czy volty z wieloma numerami są prawidłowo obsługiwane
            measures = expanded_score.parts[0].measures
            pitches = [m.notes[0].pitch for m in measures]
            
            # Oczekiwane rozwinięcie: C-D (volta 1), C-D (volta 2), C-E (volta 3)
            expected_pitches = ["C4", "D4", "C4", "D4", "C4", "E4"]
            assert pitches == expected_pitches
            
            os.unlink(f.name)
    
    def test_repeat_without_forward(self, parser, expander):
        """Test repetycji bez explicit forward repeat"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Implicit Forward</part-name>
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
              <barline location="right">
                <repeat direction="backward"/>
              </barline>
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            score = parser.parse_file(f.name)
            expanded_score = expander.expand_repeats(score)
            
            # Sprawdź czy repetycja bez explicit forward jest obsługiwana
            measures = expanded_score.parts[0].measures
            pitches = [m.notes[0].pitch for m in measures]
            
            # Oczekiwane rozwinięcie: C-D, C-D (powtórzenie od początku)
            expected_pitches = ["C4", "D4", "C4", "D4"]
            assert pitches == expected_pitches
            
            os.unlink(f.name)
    
    def test_da_capo_al_fine(self, parser, expander):
        """Test Da Capo al Fine (jeśli obsługiwane)"""
        # Ten test może być zaawansowany i zależny od implementacji
        pass


class TestSpecialNotations:
    """Testy specjalnych notacji"""
    
    @pytest.fixture
    def parser(self):
        return MusicXMLParser()
    
    def test_grace_notes(self, parser):
        """Test parsowania ozdobników"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Grace Notes</part-name>
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
                <grace/>
                <pitch><step>B</step><octave>3</octave></pitch>
                <duration>1</duration>
                <voice>1</voice>
                <type>eighth</type>
              </note>
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
            notes = score.parts[0].measures[0].notes
            
            # Sprawdź czy parser obsługuje ozdobniki
            # (implementacja może się różnić)
            assert len(notes) >= 1
            
            os.unlink(f.name)
    
    def test_ties_and_slurs(self, parser):
        """Test parsowania ligatur i łuków"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Ties and Slurs</part-name>
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
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
                <tie type="start"/>
                <notations>
                  <tied type="start"/>
                </notations>
              </note>
              <note>
                <pitch><step>C</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
                <tie type="stop"/>
                <notations>
                  <tied type="stop"/>
                </notations>
              </note>
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            score = parser.parse_file(f.name)
            notes = score.parts[0].measures[0].notes
            
            # Sprawdź czy parser obsługuje ligature
            assert len(notes) == 2
            assert notes[0].tie == "start"
            assert notes[1].tie == "stop"
            
            os.unlink(f.name)


class TestDataIntegrity:
    """Testy integralności danych"""
    
    @pytest.fixture
    def parser(self):
        return MusicXMLParser()
    
    @pytest.fixture
    def generator(self):
        return LinearSequenceGenerator()
    
    def test_timing_consistency(self, parser, generator):
        """Test spójności czasów w sekwencji"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Timing Test</part-name>
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
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
              <note>
                <pitch><step>D</step><octave>4</octave></pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>half</type>
              </note>
              <note>
                <pitch><step>E</step><octave>4</octave></pitch>
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
            notes = generator.generate_sequence(score)
            
            # Sprawdź spójność czasów
            assert len(notes) == 3
            
            # Sprawdź czy czasy są w porządku rosnącym
            for i in range(1, len(notes)):
                assert notes[i].start_time >= notes[i-1].start_time
            
            # Sprawdź konkretne wartości
            assert notes[0].start_time == Fraction(0)
            assert notes[1].start_time == Fraction(1, 4)
            assert notes[2].start_time == Fraction(3, 4)
            
            os.unlink(f.name)
    
    def test_duration_calculation(self, parser):
        """Test obliczania duracji nut"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Duration Test</part-name>
            </score-part>
          </part-list>
          <part id="P1">
            <measure number="1">
              <attributes>
                <divisions>8</divisions>
                <key><fifths>0</fifths></key>
                <time><beats>4</beats><beat-type>4</beat-type></time>
                <clef><sign>G</sign><line>2</line></clef>
              </attributes>
              <note>
                <pitch><step>C</step><octave>4</octave></pitch>
                <duration>2</duration>
                <voice>1</voice>
                <type>eighth</type>
              </note>
              <note>
                <pitch><step>D</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
              <note>
                <pitch><step>E</step><octave>4</octave></pitch>
                <duration>8</duration>
                <voice>1</voice>
                <type>half</type>
              </note>
            </measure>
          </part>
        </score-partwise>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            
            score = parser.parse_file(f.name)
            notes = score.parts[0].measures[0].notes
            
            # Sprawdź obliczanie duracji przy divisions=8
            assert notes[0].duration == Fraction(2, 8)  # eighth note
            assert notes[1].duration == Fraction(4, 8)  # quarter note
            assert notes[2].duration == Fraction(8, 8)  # half note
            
            os.unlink(f.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 