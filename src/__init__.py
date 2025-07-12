"""
MusicXML Parser Package

A comprehensive MusicXML parser with support for:
- Two-pass parsing (inspired by MuseScore)
- Repeats and volta handling
- Tempo and time signature changes
- Multi-staff parts (left/right hand)
- Linear sequence generation for playback
"""

from musicxml_parser import (
    MusicXMLParser,
    MusicXMLScore,
    MusicXMLPart,
    MusicXMLMeasure,
    MusicXMLNote,
    MusicXMLError,
    EndingType,
    BarlineType,
    RepeatDirection
)

from repeat_expander import (
    RepeatExpander,
    LinearSequenceGenerator
)

__version__ = "0.1.0"
__author__ = "MusicXML Parser Team"

__all__ = [
    "MusicXMLParser",
    "MusicXMLScore",
    "MusicXMLPart",
    "MusicXMLMeasure",
    "MusicXMLNote",
    "MusicXMLError",
    "EndingType",
    "BarlineType",
    "RepeatDirection",
    "RepeatExpander",
    "LinearSequenceGenerator"
] 