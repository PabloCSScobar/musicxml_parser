
# MusicXML Parser

A comprehensive MusicXML parser written in Python, inspired by MuseScore's architecture. Parses MusicXML files and expands repeats and voltas into linear sequences for playback and analysis.

## Features

- **Two-pass parsing** inspired by MuseScore architecture
- **Complete MusicXML support**: .xml, .musicxml, and compressed .mxl files
- **Intelligent repeat expansion**: Automatically expands repeats and voltas into linear sequences
- **Multi-staff support**: Separates notes by staff (e.g., left/right hand for piano)
- **Timing conversion**: Converts musical time to milliseconds with tempo changes
- **Playback events**: Generates MIDI-like note_on/note_off events
- **Comprehensive analysis**: Extracts tempo changes, time signatures, key signatures

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd musicxml_parser

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Command Line Usage

```bash
# Basic analysis
python main.py path/to/score.xml

# Detailed analysis with verbose output
python main.py path/to/score.xml --verbose

# Skip repeat expansion
python main.py path/to/score.xml --no-expand
```

### Python API

```python
from src.musicxml_parser import MusicXMLParser
from src.repeat_expander import RepeatExpander, LinearSequenceGenerator

# Parse MusicXML file
parser = MusicXMLParser()
score = parser.parse_file('path/to/score.xml')

print(f"Title: {score.title}")
print(f"Composer: {score.composer}")
print(f"Parts: {len(score.parts)}")

# Expand repeats and voltas
expander = RepeatExpander()
expanded_score = expander.expand_repeats(score)

# Generate linear sequence of notes
generator = LinearSequenceGenerator()
notes = generator.generate_sequence(expanded_score)

# Separate by hand (staff 1 = right, staff 2 = left)
right_hand, left_hand = generator.get_notes_by_hand(expanded_score)

# Generate playback events with millisecond timing
notes_with_ms = generator.get_notes_with_milliseconds(expanded_score)
events = generator.get_playback_events(expanded_score)
```

## What You Can Extract

### Musical Structure
- **Score metadata**: title, composer, parts, instruments
- **Timing information**: tempo (BPM), time signatures, key signatures
- **Measure analysis**: note counts, durations, staff assignments
- **Repeat structures**: repeat marks, volta endings, expansion ratios

### Note-Level Data
- **Pitch information**: note names (e.g., "C4", "F#5") or rests
- **Timing**: start times, durations in quarter notes and milliseconds
- **Voice/Staff assignment**: multi-voice and multi-staff support
- **Musical attributes**: ties, chords, measure numbers

### Playback-Ready Output
- **Linear note sequence**: All notes in chronological order after repeat expansion
- **MIDI-like events**: note_on, note_off, tempo_change events with precise timing
- **Hand separation**: Notes split by staff for piano pieces
- **Millisecond timing**: Real-time playback positions calculated from tempo

### Analysis Results
```python
# Example output structure
{
    'pitch': 'C4',
    'start_time_ms': 0.0,
    'duration_ms': 500.0,
    'staff': 1,
    'measure': 1,
    'tempo_bpm': 120,
    'is_rest': False,
    'is_chord': False
}
```

## Supported MusicXML Elements

✅ **Fully Supported**
- Score structure (parts, measures, notes, rests)
- Repeats (forward/backward) and voltas (1st/2nd endings)
- Tempo changes (metronome, sound tempo)
- Time and key signatures
- Multi-staff parts (piano left/right hand)
- Pitch information (step, alter, octave)
- Ties and chord notation
- Implicit repeats and anacrusis measures


## Project Structure

```
musicxml_parser/
├── src/
│   ├── musicxml_parser.py       # Main parser (two-pass parsing)
│   └── repeat_expander.py       # Repeat expansion and sequence generation
├── main.py                      # CLI demo script
├── tests/                       # Test suite
└── README.md
```