
# MusicXML Parser

A comprehensive MusicXML parser written in Python, inspired by MuseScore's architecture. Parses MusicXML files and expands repeats and voltas into linear sequences for playback and analysis.

## Features

- **Two-pass parsing** inspired by MuseScore architecture
- **Complete MusicXML support**: .xml, .musicxml, and compressed .mxl files
- **Intelligent repeat expansion**: Automatically expands repeats and voltas into linear sequences
- **Multi-staff support**: Separates notes by staff (e.g., left/right hand for piano)
- **Timing conversion**: Converts musical time to milliseconds with tempo changes
- **Playback events**: Generates MIDI-like note_on/note_off events
- **Advanced cursor positioning**: Dual timing system for proper UI cursor handling in scores with repeats
- **Repeat iteration tracking**: Full metadata about which repeat iteration each note belongs to
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

# 🚀 ADVANCED: Get notes with dual timing + repeat metadata for UI cursor positioning (OSMD integration)
# This handles repeat display correctly - cursor shows original position
# while playback uses expanded timeline + detailed repeat information
notes_with_display = generator.get_expanded_notes_with_milliseconds(score, expanded_score)
```

## What You Can Extract

### Musical Structure
- **Score metadata**: title, composer, parts, instruments
- **Timing information**: tempo (BPM), time signatures, key signatures
- **Measure analysis**: note counts, durations, staff assignments
- **Repeat structures**: repeat marks, volta endings, expansion ratios
- **Repeat metadata**: detailed information about which iteration each note belongs to

### Note-Level Data
- **Pitch information**: note names (e.g., "C4", "F#5") or rests
- **Timing**: start times, durations in quarter notes and milliseconds
- **Voice/Staff assignment**: multi-voice and multi-staff support
- **Musical attributes**: ties, chords, measure numbers
- **Repeat information**: iteration number, repeat ID, section type (main/volta)

### Playback-Ready Output
- **Linear note sequence**: All notes in chronological order after repeat expansion
- **MIDI-like events**: note_on, note_off, tempo_change events with precise timing
- **Hand separation**: Notes split by staff for piano pieces
- **Millisecond timing**: Real-time playback positions calculated from tempo
- **Dual timing for UI cursors**: Both `start_time_ms` (playback) and `start_time_display_ms` (score cursor) for proper repeat handling in music notation software
- **Repeat iteration tracking**: Know exactly which repeat iteration is playing

### Analysis Results
```python
# Basic note structure
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

# Advanced: Notes with dual timing + repeat metadata (for UI cursor positioning)
{
    'pitch': 'C4',
    'start_time_ms': 2000.0,        # Real playback time (with repeats)
    'start_time_display_ms': 0.0,   # UI cursor position (original score)
    'duration_ms': 500.0,
    'staff': 1,
    'measure': 1,
    'iteration': 1,                  # Which repeat iteration (0, 1, 2...)
    'tempo_bpm': 120,
    # NEW: Detailed repeat metadata
    'is_repeat': True,               # Is this note from a repeat?
    'repeat_id': 'repeat_0_3',       # Unique identifier for this repeat section
    'repeat_section': 'main',        # Section type: 'main', 'volta_1', 'volta_2'
    'total_iterations': 2            # Total number of iterations for this repeat
}
```

## Advanced Use Case: Music Notation UI Cursor Positioning with Repeat Tracking

When building music notation software (like OSMD integration), scores with repeats need special handling for cursor positioning. The problem: during playback, the actual time progresses linearly through expanded repeats, but the visual cursor should show the position in the original score notation.

**NEW**: Now with detailed repeat iteration tracking!

```python
# For UI applications (like OSMD integration)
parser = MusicXMLParser()
score = parser.parse_file('score_with_repeats.xml')

expander = RepeatExpander()
expanded_score = expander.expand_repeats(score)

generator = LinearSequenceGenerator()

# Get notes with dual timing + repeat metadata - key for UI cursor positioning
notes_with_display = generator.get_expanded_notes_with_milliseconds(score, expanded_score)

for note in notes_with_display:
    # start_time_ms: Real playback time (0, 500, 1000, 1500, 2000, 2500...)
    # start_time_display_ms: Score cursor position (0, 500, 1000, 0, 500, 1000...)
    # iteration: Which repeat iteration (0, 0, 0, 1, 1, 1...)
    # is_repeat: Is this note from a repeat section?
    # repeat_id: Which repeat section is this?
    
    print(f"Measure {note['measure']}, Iteration {note['iteration']}")
    print(f"  Playback time: {note['start_time_ms']}ms")
    print(f"  Cursor position: {note['start_time_display_ms']}ms")
    print(f"  Repeat: {note['repeat_id']} ({'Yes' if note['is_repeat'] else 'No'})")
    print(f"  Section: {note['repeat_section']}")
```

This enables:
- **Accurate playback timing**: Audio plays at correct times with expanded repeats
- **Correct cursor positioning**: Visual cursor jumps back to measure 1 when repeat starts
- **Repeat iteration tracking**: Know exactly which iteration is currently playing (0-based: 0=1st time, 1=2nd time, etc.)
- **Repeat section identification**: Distinguish between main sections and volta endings
- **Advanced UI features**: Display "1st time" (iteration=0), "2nd time" (iteration=1) indicators, highlight active repeats

## Repeat Iteration Examples

```python
# Example output for a score with repeats
notes = generator.get_expanded_notes_with_milliseconds(score, expanded_score)

# Measure 1, first time through
{'measure': 1, 'iteration': 0, 'is_repeat': True, 'repeat_id': 'repeat_0_3', 'repeat_section': 'main'}

# Measure 2, first ending (volta 1)
{'measure': 2, 'iteration': 0, 'is_repeat': True, 'repeat_id': 'repeat_0_3', 'repeat_section': 'volta_1'}

# Measure 1, second time through
{'measure': 1, 'iteration': 1, 'is_repeat': True, 'repeat_id': 'repeat_0_3', 'repeat_section': 'main'}

# Measure 3, second ending (volta 2)
{'measure': 3, 'iteration': 1, 'is_repeat': True, 'repeat_id': 'repeat_0_3', 'repeat_section': 'volta_2'}

# Measure 4, no repeat
{'measure': 4, 'iteration': 0, 'is_repeat': False, 'repeat_id': None, 'repeat_section': 'main'}
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
- **NEW**: Detailed repeat iteration metadata and section tracking


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