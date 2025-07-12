#!/usr/bin/env python3
"""
Main demonstration script for MusicXML Parser

This script demonstrates the complete functionality of the MusicXML parser:
- Parsing MusicXML files
- Expanding repeats and voltas
- Generating linear sequences
- Extracting playback events
- Separating notes by hand (for piano)
"""

import argparse
import sys
from pathlib import Path
from fractions import Fraction

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from musicxml_parser import MusicXMLParser, MusicXMLError
from repeat_expander import RepeatExpander, LinearSequenceGenerator


def format_time(time_fraction: Fraction) -> str:
    """Format time fraction as readable string"""
    if time_fraction.denominator == 1:
        return str(time_fraction.numerator)
    else:
        return f"{time_fraction.numerator}/{time_fraction.denominator}"


def print_score_info(score):
    """Print basic information about the score"""
    print(f"\n📄 Score Information:")
    print(f"   Title: {score.title}")
    print(f"   Composer: {score.composer}")
    print(f"   Parts: {len(score.parts)}")
    
    if score.errors:
        print(f"   ⚠️  Errors: {len(score.errors)}")
        for error in score.errors[:3]:  # Show first 3 errors
            print(f"      • {error}")
        if len(score.errors) > 3:
            print(f"      ... and {len(score.errors) - 3} more")


def print_part_info(part):
    """Print information about a part"""
    print(f"\n🎹 Part: {part.name} (ID: {part.id})")
    print(f"   Instrument: {part.instrument}")
    print(f"   Staves: {part.staves}")
    print(f"   MIDI Channel: {part.midi_channel}")
    print(f"   Measures: {len(part.measures)}")
    
    # Count notes and rests
    total_notes = 0
    total_rests = 0
    for measure in part.measures:
        for note in measure.notes:
            if note.is_rest:
                total_rests += 1
            else:
                total_notes += 1
    
    print(f"   Notes: {total_notes}")
    print(f"   Rests: {total_rests}")


def print_measure_details(measures, max_measures=5):
    """Print detailed information about measures"""
    print(f"\n📊 Measure Details (showing first {min(max_measures, len(measures))}):")
    
    for i, measure in enumerate(measures[:max_measures]):
        print(f"\n   Measure {measure.number}:")
        print(f"      Time Signature: {measure.time_signature}")
        print(f"      Key Signature: {measure.key_signature} fifths")
        print(f"      Divisions: {measure.divisions}")
        
        if measure.tempo_bpm:
            print(f"      Tempo: {measure.tempo_bpm} BPM")
        
        if measure.repeat_start:
            print(f"      🔄 Repeat Start")
        if measure.repeat_end:
            print(f"      🔄 Repeat End (×{measure.repeat_count})")
        
        if measure.ending_numbers:
            print(f"      🎯 Volta: {measure.ending_numbers} ({measure.ending_type.value if measure.ending_type else 'unknown'})")
        
        print(f"      Notes: {len(measure.notes)}")
        
        # Show first few notes
        for j, note in enumerate(measure.notes[:3]):
            if note.is_rest:
                print(f"         {j+1}. Rest - Duration: {format_time(note.duration)} - Staff: {note.staff}")
            else:
                print(f"         {j+1}. {note.pitch} - Duration: {format_time(note.duration)} - Staff: {note.staff}")
        
        if len(measure.notes) > 3:
            print(f"         ... and {len(measure.notes) - 3} more notes")


def print_linear_sequence(notes, max_notes=10):
    """Print linear sequence of notes"""
    print(f"\n🎵 Linear Sequence (showing first {min(max_notes, len(notes))}):")
    
    for i, note in enumerate(notes[:max_notes]):
        start_time = format_time(note.start_time)
        duration = format_time(note.duration)
        
        if note.is_rest:
            print(f"   {i+1:2d}. [{start_time:>6}] Rest - Duration: {duration} - Staff: {note.staff} - Measure: {note.measure_number}")
        else:
            print(f"   {i+1:2d}. [{start_time:>6}] {note.pitch:>4} - Duration: {duration} - Staff: {note.staff} - Measure: {note.measure_number}")
    
    if len(notes) > max_notes:
        print(f"   ... and {len(notes) - max_notes} more notes")


def print_hand_separation(right_hand, left_hand):
    """Print hand separation statistics"""
    print(f"\n👐 Hand Separation:")
    print(f"   Right Hand (Staff 1): {len(right_hand)} notes")
    print(f"   Left Hand (Staff 2): {len(left_hand)} notes")
    
    if right_hand:
        print(f"   Right Hand Range: {format_time(right_hand[0].start_time)} - {format_time(right_hand[-1].start_time + right_hand[-1].duration)}")
    
    if left_hand:
        print(f"   Left Hand Range: {format_time(left_hand[0].start_time)} - {format_time(left_hand[-1].start_time + left_hand[-1].duration)}")


def print_playback_events(events, max_events=15):
    """Print playback events"""
    print(f"\n🎮 Playback Events (showing first {min(max_events, len(events))}):")
    
    for i, event in enumerate(events[:max_events]):
        time_str = format_time(event['time'])
        
        if event['type'] == 'tempo_change':
            print(f"   {i+1:2d}. [{time_str:>6}] 🎵 Tempo: {event['tempo']} BPM")
        elif event['type'] == 'note_on':
            print(f"   {i+1:2d}. [{time_str:>6}] ▶️  Note On:  {event['pitch']} (Staff {event['staff']}, Measure {event['measure']})")
        elif event['type'] == 'note_off':
            print(f"   {i+1:2d}. [{time_str:>6}] ⏹️  Note Off: {event['pitch']} (Staff {event['staff']}, Measure {event['measure']})")
    
    if len(events) > max_events:
        print(f"   ... and {len(events) - max_events} more events")


def analyze_file(file_path: str, expand_repeats: bool = True, verbose: bool = False):
    """Analyze a MusicXML file"""
    print(f"🎼 Analyzing MusicXML file: {file_path}")
    
    try:
        # Parse the file
        parser = MusicXMLParser()
        score = parser.parse_file(file_path)
        
        # Print basic info
        print_score_info(score)
        
        # Print part information
        for part in score.parts:
            print_part_info(part)
            
            if verbose:
                print_measure_details(part.measures)
        
        # Expand repeats if requested
        if expand_repeats:
            print(f"\n🔄 Expanding repeats...")
            expander = RepeatExpander()
            expanded_score = expander.expand_repeats(score)
            
            # Compare before and after
            original_measures = sum(len(part.measures) for part in score.parts)
            expanded_measures = sum(len(part.measures) for part in expanded_score.parts)
            
            print(f"   Original measures: {original_measures}")
            print(f"   Expanded measures: {expanded_measures}")
            print(f"   Expansion ratio: {expanded_measures/original_measures:.2f}x")
            
            # Use expanded score for further analysis
            score = expanded_score
        
        # Generate linear sequence
        print(f"\n🎵 Generating linear sequence...")
        generator = LinearSequenceGenerator()
        notes = generator.generate_sequence(score)
        
        print(f"   Total notes: {len(notes)}")
        
        if verbose:
            print_linear_sequence(notes)
        
        # Separate by hand
        right_hand, left_hand = generator.get_notes_by_hand(score)
        print_hand_separation(right_hand, left_hand)
        
        # Generate playback events
        events = generator.get_playback_events(score)
        print(f"\n🎮 Playback events: {len(events)}")
        
        if verbose:
            print_playback_events(events)
        
        # Summary statistics
        print(f"\n📈 Summary Statistics:")
        tempo_changes = len([e for e in events if e['type'] == 'tempo_change'])
        note_events = len([e for e in events if e['type'] in ['note_on', 'note_off']])
        
        print(f"   Tempo changes: {tempo_changes}")
        print(f"   Note events: {note_events}")
        
        if notes:
            total_duration = max(note.start_time + note.duration for note in notes)
            print(f"   Total duration: {format_time(total_duration)} quarter notes")
        
        print(f"\n✅ Analysis complete!")
        
    except MusicXMLError as e:
        print(f"❌ Error parsing MusicXML: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    return 0


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="MusicXML Parser - Analyze and process MusicXML files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py tests/data/simple_score.xml
  python main.py tests/data/complex_score.xml --verbose
  python main.py Fur_Elise.mxl --no-expand
        """
    )
    
    parser.add_argument(
        "file",
        help="MusicXML file to analyze (.xml, .musicxml, or .mxl)"
    )
    
    parser.add_argument(
        "--no-expand",
        action="store_true",
        help="Don't expand repeats and voltas"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed information"
    )
    
    args = parser.parse_args()
    
    # Check if file exists
    if not Path(args.file).exists():
        print(f"❌ File not found: {args.file}")
        return 1
    
    # Analyze the file
    return analyze_file(
        args.file,
        expand_repeats=not args.no_expand,
        verbose=args.verbose
    )


if __name__ == "__main__":
    sys.exit(main()) 