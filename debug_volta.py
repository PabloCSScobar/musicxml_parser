import tempfile
import sys
sys.path.append('src')
from musicxml_parser import MusicXMLParser
from repeat_expander import RepeatExpander

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
    
    parser = MusicXMLParser()
    score = parser.parse_file(f.name)
    
    print('Original measures:')
    for i, m in enumerate(score.parts[0].measures):
        print(f'  {i}: {m.number} - repeat_start={m.repeat_start}, repeat_end={m.repeat_end}, ending_numbers={m.ending_numbers}, ending_type={m.ending_type}')
    
    expander = RepeatExpander()
    structures = expander._analyze_repeat_structures(score.parts[0].measures)
    
    print('\nAnalyzed structures:')
    for i, s in enumerate(structures):
        print(f'  {i}: {s}')
        
    expanded = expander.expand_repeats(score)
    
    print('\nExpanded measures:')
    for i, m in enumerate(expanded.parts[0].measures):
        print(f'  {i}: {m.number} - {m.notes[0].pitch if m.notes else "no notes"} - start_time={m.notes[0].start_time if m.notes else "N/A"}') 