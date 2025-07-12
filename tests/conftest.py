"""
Konfiguracja pytest dla testów parsera MusicXML.
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Dodaj src do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from musicxml_parser import MusicXMLParser
from repeat_expander import RepeatExpander, LinearSequenceGenerator


@pytest.fixture(scope="session")
def test_data_dir():
    """Zwraca ścieżkę do katalogu z danymi testowymi"""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def sample_files():
    """Zwraca słownik z ścieżkami do plików przykładowych"""
    test_data_dir = Path(__file__).parent / "data"
    data_dir = Path(__file__).parent.parent / "data"
    
    return {
        "simple_score": test_data_dir / "simple_score.xml",
        "complex_score": test_data_dir / "complex_score.xml",
        "fur_elise": data_dir / "Fur_Elise.mxl"
    }


@pytest.fixture
def parser():
    """Zwraca instancję parsera MusicXML"""
    return MusicXMLParser()


@pytest.fixture
def expander():
    """Zwraca instancję expandera repetycji"""
    return RepeatExpander()


@pytest.fixture
def generator():
    """Zwraca instancję generatora sekwencji"""
    return LinearSequenceGenerator()


@pytest.fixture
def temp_xml_file():
    """Tworzy tymczasowy plik XML i zwraca jego ścieżkę"""
    temp_file = None
    
    def _create_temp_xml(content):
        nonlocal temp_file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False)
        temp_file.write(content)
        temp_file.flush()
        temp_file.close()
        return temp_file.name
    
    yield _create_temp_xml
    
    # Cleanup
    if temp_file and os.path.exists(temp_file.name):
        os.unlink(temp_file.name)


@pytest.fixture
def minimal_musicxml():
    """Zwraca minimalny poprawny MusicXML"""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <score-partwise version="4.0">
      <part-list>
        <score-part id="P1">
          <part-name>Test Part</part-name>
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
        </measure>
      </part>
    </score-partwise>"""


@pytest.fixture
def complex_musicxml():
    """Zwraca złożony MusicXML z repetycjami i voltami"""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <score-partwise version="4.0">
      <work>
        <work-title>Test Complex Score</work-title>
      </work>
      <identification>
        <creator type="composer">Test Composer</creator>
      </identification>
      <part-list>
        <score-part id="P1">
          <part-name>Piano</part-name>
          <score-instrument id="P1-I1">
            <instrument-name>Piano</instrument-name>
          </score-instrument>
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
        <measure number="2">
          <barline location="left">
            <repeat direction="forward"/>
          </barline>
          <note>
            <pitch><step>D</step><octave>5</octave></pitch>
            <duration>4</duration>
            <voice>1</voice>
            <type>quarter</type>
            <staff>1</staff>
          </note>
          <note>
            <pitch><step>D</step><octave>3</octave></pitch>
            <duration>4</duration>
            <voice>1</voice>
            <type>quarter</type>
            <staff>2</staff>
          </note>
        </measure>
        <measure number="3">
          <barline location="left">
            <ending number="1" type="start"/>
          </barline>
          <note>
            <pitch><step>E</step><octave>5</octave></pitch>
            <duration>4</duration>
            <voice>1</voice>
            <type>quarter</type>
            <staff>1</staff>
          </note>
          <note>
            <pitch><step>E</step><octave>3</octave></pitch>
            <duration>4</duration>
            <voice>1</voice>
            <type>quarter</type>
            <staff>2</staff>
          </note>
          <barline location="right">
            <ending number="1" type="stop"/>
            <repeat direction="backward"/>
          </barline>
        </measure>
        <measure number="4">
          <barline location="left">
            <ending number="2" type="start"/>
          </barline>
          <note>
            <pitch><step>F</step><octave>5</octave></pitch>
            <duration>4</duration>
            <voice>1</voice>
            <type>quarter</type>
            <staff>1</staff>
          </note>
          <note>
            <pitch><step>F</step><octave>3</octave></pitch>
            <duration>4</duration>
            <voice>1</voice>
            <type>quarter</type>
            <staff>2</staff>
          </note>
          <barline location="right">
            <ending number="2" type="stop"/>
          </barline>
        </measure>
      </part>
    </score-partwise>"""


@pytest.fixture
def invalid_musicxml():
    """Zwraca niepoprawny MusicXML do testów błędów"""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <score-partwise version="4.0">
      <!-- Brak part-list -->
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


def pytest_configure(config):
    """Konfiguracja pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modyfikuje kolekcję testów"""
    for item in items:
        # Automatycznie oznacz testy wydajności
        if "performance" in item.nodeid or "benchmark" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        # Automatycznie oznacz testy integracyjne
        if "integration" in item.nodeid or "real_world" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Automatycznie oznacz wolne testy
        if "large_file" in item.nodeid or "scalability" in item.nodeid:
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Automatyczna konfiguracja środowiska testowego"""
    # Sprawdź czy istnieją wymagane katalogi
    test_data_dir = Path(__file__).parent / "data"
    if not test_data_dir.exists():
        test_data_dir.mkdir(parents=True)
    
    # Sprawdź czy istnieją pliki testowe
    simple_score = test_data_dir / "simple_score.xml"
    if not simple_score.exists():
        # Stwórz podstawowy plik testowy jeśli nie istnieje
        minimal_xml = """<?xml version="1.0" encoding="UTF-8"?>
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
        
        with open(simple_score, 'w') as f:
            f.write(minimal_xml)
    
    yield
    
    # Cleanup po testach (jeśli potrzebne)
    pass


class TestHelpers:
    """Klasa pomocnicza z metodami użytecznymi w testach"""
    
    @staticmethod
    def create_test_xml(measures_count=1, notes_per_measure=4, with_repeats=False):
        """Tworzy XML testowy z określonymi parametrami"""
        xml_header = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Test</part-name>
            </score-part>
          </part-list>
          <part id="P1">"""
        
        xml_footer = """
          </part>
        </score-partwise>"""
        
        measures = []
        pitches = ["C", "D", "E", "F", "G", "A", "B"]
        
        for i in range(1, measures_count + 1):
            measure_xml = f'<measure number="{i}">'
            
            if i == 1:
                measure_xml += """
                <attributes>
                  <divisions>4</divisions>
                  <key><fifths>0</fifths></key>
                  <time><beats>4</beats><beat-type>4</beat-type></time>
                  <clef><sign>G</sign><line>2</line></clef>
                </attributes>"""
            
            if with_repeats and i == 2:
                measure_xml += '<barline location="left"><repeat direction="forward"/></barline>'
            
            for j in range(notes_per_measure):
                pitch = pitches[j % len(pitches)]
                octave = 4 + (j // len(pitches))
                measure_xml += f"""
                <note>
                  <pitch><step>{pitch}</step><octave>{octave}</octave></pitch>
                  <duration>4</duration>
                  <voice>1</voice>
                  <type>quarter</type>
                </note>"""
            
            if with_repeats and i == measures_count:
                measure_xml += '<barline location="right"><repeat direction="backward"/></barline>'
            
            measure_xml += '</measure>'
            measures.append(measure_xml)
        
        return xml_header + "".join(measures) + xml_footer
    
    @staticmethod
    def assert_score_validity(score):
        """Sprawdza podstawową poprawność sparsowanego utworu"""
        assert score is not None
        assert len(score.parts) > 0
        assert score.tempo_bpm > 0
        assert score.time_signature is not None
        
        for part in score.parts:
            assert part.name is not None
            assert len(part.measures) > 0
            
            for measure in part.measures:
                assert measure.number > 0
                # Nuty mogą być puste w niektórych taktach
    
    @staticmethod
    def count_total_notes(score):
        """Liczy całkowitą liczbę nut w utworze"""
        return sum(len(m.notes) for p in score.parts for m in p.measures)
    
    @staticmethod
    def get_pitch_sequence(score):
        """Zwraca sekwencję pitch wszystkich nut"""
        pitches = []
        for part in score.parts:
            for measure in part.measures:
                for note in measure.notes:
                    pitches.append(note.pitch)
        return pitches


@pytest.fixture
def test_helpers():
    """Zwraca instancję klasy pomocniczej"""
    return TestHelpers() 