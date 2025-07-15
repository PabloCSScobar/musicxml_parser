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
    print(f"   Global Tempo: {score.tempo_bpm} BPM" if score.tempo_bpm else "   Global Tempo: Not set")
    print(f"   Global Time Signature: {score.time_signature[0]}/{score.time_signature[1]}")
    print(f"   Global Key Signature: {score.key_signature} fifths")
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


def analyze_repeats_and_voltas(part):
    """Analyze repeats and voltas in detail"""
    print(f"\n🔄 Repeat and Volta Analysis:")
    
    repeat_measures = []
    volta_measures = []
    
    for i, measure in enumerate(part.measures):
        if measure.repeat_start:
            repeat_measures.append(f"Measure {measure.number}: REPEAT START")
        if measure.repeat_end:
            repeat_measures.append(f"Measure {measure.number}: REPEAT END (×{measure.repeat_count})")
        if measure.ending_numbers:
            volta_measures.append(f"Measure {measure.number}: VOLTA {measure.ending_numbers} ({measure.ending_type.value if measure.ending_type else 'unknown'})")
    
    if repeat_measures:
        print("   Repeat Marks:")
        for repeat in repeat_measures:
            print(f"      • {repeat}")
    else:
        print("   No repeat marks found")
    
    if volta_measures:
        print("   Volta Marks:")
        for volta in volta_measures:
            print(f"      • {volta}")
    else:
        print("   No volta marks found")


def analyze_tempo_and_meter_changes(part):
    """Analyze tempo and meter changes throughout the piece"""
    print(f"\n🎵 Tempo and Meter Analysis:")
    
    tempo_changes = []
    meter_changes = []
    key_changes = []
    
    current_tempo = None
    current_meter = None
    current_key = None
    
    for measure in part.measures:
        # Check for tempo changes
        if measure.tempo_bpm and measure.tempo_bpm != current_tempo:
            tempo_changes.append(f"Measure {measure.number}: {measure.tempo_bpm} BPM")
            current_tempo = measure.tempo_bpm
        
        # Check for meter changes
        if measure.time_signature != current_meter:
            meter_changes.append(f"Measure {measure.number}: {measure.time_signature[0]}/{measure.time_signature[1]}")
            current_meter = measure.time_signature
        
        # Check for key changes
        if measure.key_signature != current_key:
            key_changes.append(f"Measure {measure.number}: {measure.key_signature} fifths")
            current_key = measure.key_signature
    
    if tempo_changes:
        print("   Tempo Changes:")
        for change in tempo_changes:
            print(f"      • {change}")
    else:
        print("   No tempo changes found")
    
    if meter_changes:
        print("   Meter Changes:")
        for change in meter_changes:
            print(f"      • {change}")
    else:
        print("   No meter changes found")
    
    if key_changes:
        print("   Key Changes:")
        for change in key_changes:
            print(f"      • {change}")
    else:
        print("   No key changes found")


def print_measure_details(measures, max_measures=10):
    """Print detailed information about measures"""
    print(f"\n📊 Measure Details (showing first {min(max_measures, len(measures))}):")
    
    for i, measure in enumerate(measures[:max_measures]):
        print(f"\n   Measure {measure.number}:")
        print(f"      Time Signature: {measure.time_signature[0]}/{measure.time_signature[1]}")
        print(f"      Key Signature: {measure.key_signature} fifths")
        print(f"      Divisions: {measure.divisions}")
        
        if measure.tempo_bpm:
            print(f"      Tempo: {measure.tempo_bpm} BPM")
        
        # Repeat info
        repeat_info = []
        if measure.repeat_start:
            repeat_info.append("REPEAT START")
        if measure.repeat_end:
            repeat_info.append(f"REPEAT END (×{measure.repeat_count})")
        if repeat_info:
            print(f"      🔄 {' | '.join(repeat_info)}")
        
        # Volta info
        if measure.ending_numbers:
            print(f"      🎯 Volta: {measure.ending_numbers} ({measure.ending_type.value if measure.ending_type else 'unknown'})")
        
        print(f"      Notes: {len(measure.notes)}")
        
        # Show first few notes with more detail
        for j, note in enumerate(measure.notes[:5]):
            if note.is_rest:
                print(f"         {j+1}. Rest - Duration: {format_time(note.duration)} - Staff: {note.staff} - Voice: {note.voice}")
            else:
                print(f"         {j+1}. {note.pitch} - Duration: {format_time(note.duration)} - Staff: {note.staff} - Voice: {note.voice}")
        
        if len(measure.notes) > 5:
            print(f"         ... and {len(measure.notes) - 5} more notes")


def analyze_upbeat(measures):
    """Analyze if there's an upbeat (anacrusis)"""
    print(f"\n🎼 Upbeat Analysis:")
    
    if not measures:
        print("   No measures to analyze")
        return
    
    first_measure = measures[0]
    
    # Calculate expected measure duration based on time signature
    expected_duration = Fraction(first_measure.time_signature[0], first_measure.time_signature[1]) * 4  # Convert to quarter notes
    
    # Calculate actual duration of first measure
    actual_duration = Fraction(0)
    for note in first_measure.notes:
        actual_duration += note.duration
    
    print(f"   First measure duration: {format_time(actual_duration)} quarter notes")
    print(f"   Expected full measure: {format_time(expected_duration)} quarter notes")
    
    if actual_duration < expected_duration:
        upbeat_duration = expected_duration - actual_duration
        print(f"   ✅ UPBEAT detected: {format_time(upbeat_duration)} quarter notes missing")
        print(f"   This is a pickup/anacrusis measure")
    else:
        print(f"   ❌ No upbeat detected - first measure is complete")


def print_linear_sequence(notes, max_notes=15):
    """Print linear sequence of notes"""
    print(f"\n🎵 Linear Sequence (showing first {min(max_notes, len(notes))}):")
    
    for i, note in enumerate(notes[:max_notes]):
        start_time = format_time(note.start_time)
        duration = format_time(note.duration)
        
        if note.is_rest:
            print(f"   {i+1:2d}. [{start_time:>8}] Rest - Duration: {duration:>6} - Staff: {note.staff} - Measure: {note.measure_number}")
        else:
            print(f"   {i+1:2d}. [{start_time:>8}] {note.pitch:>4} - Duration: {duration:>6} - Staff: {note.staff} - Measure: {note.measure_number}")
    
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


def print_playback_events(events, max_events=520):
    """Print playback events"""
    print(f"\n🎮 Playback Events (showing first {min(max_events, len(events))}):")
    
    for i, event in enumerate(events[:max_events]):
        time_str = format_time(event['time'])
        
        if event['type'] == 'tempo_change':
            print(f"   {i+1:2d}. [{time_str:>8}] 🎵 Tempo: {event['tempo']} BPM")
        elif event['type'] == 'note_on':
            print(f"   {i+1:2d}. [{time_str:>8}] ▶️  Note On:  {event['pitch']:>4} (Staff {event['staff']}, Measure {event['measure']})")
        elif event['type'] == 'note_off':
            print(f"   {i+1:2d}. [{time_str:>8}] ⏹️  Note Off: {event['pitch']:>4} (Staff {event['staff']}, Measure {event['measure']})")
    
    if len(events) > max_events:
        print(f"   ... and {len(events) - max_events} more events")


def print_notes_with_milliseconds(notes_with_ms, max_notes=305):
    """Print notes with millisecond timing"""
    print(f"\n⏱️  Notes with Millisecond Timing (showing first {min(max_notes, len(notes_with_ms))}):")
    
    for i, note_info in enumerate(notes_with_ms[:max_notes]):
        if note_info['is_rest']:
            print(f"   {i+1:2d}. [{note_info['start_time_ms']:>8.1f}ms] Rest - Duration: {note_info['duration_ms']:>6.1f}ms - Staff: {note_info['staff']} - Measure: {note_info['measure']}")
        else:
            print(f"   {i+1:2d}. [{note_info['start_time_ms']:>8.1f}ms] {note_info['pitch']:>4} - Duration: {note_info['duration_ms']:>6.1f}ms - Staff: {note_info['staff']} - Measure: {note_info['measure']}")
    
    if len(notes_with_ms) > max_notes:
        print(f"   ... and {len(notes_with_ms) - max_notes} more notes")
    
    # Show tempo changes
    tempo_changes = {}
    for note_info in notes_with_ms:
        tempo = note_info['tempo_bpm']
        if tempo not in tempo_changes:
            tempo_changes[tempo] = []
        tempo_changes[tempo].append(note_info['start_time_ms'])
    
    print(f"\n   Tempo Zones:")
    for tempo, times in tempo_changes.items():
        start_time = min(times)
        end_time = max(times)
        print(f"      {tempo} BPM: {start_time:.1f}ms - {end_time:.1f}ms")


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
            
            # Analyze repeats and voltas
            analyze_repeats_and_voltas(part)
            
            # Analyze tempo and meter changes
            analyze_tempo_and_meter_changes(part)
            
            # Analyze upbeat
            analyze_upbeat(part.measures)
            
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
            
            # Show expanded sequence for first part
            if expanded_score.parts and verbose:
                print(f"\n📊 Expanded Measure Sequence (first 20):")
                for i, measure in enumerate(expanded_score.parts[0].measures[:20]):
                    print(f"   {i+1:2d}. Measure {measure.number} - {len(measure.notes)} notes")
                if len(expanded_score.parts[0].measures) > 20:
                    print(f"   ... and {len(expanded_score.parts[0].measures) - 20} more measures")
            
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
        
        # Generate notes with milliseconds
        notes_with_ms = generator.get_notes_with_milliseconds(score)
        print(f"\n⏱️  Notes with millisecond timing: {len(notes_with_ms)}")
        
        if verbose:
            print_notes_with_milliseconds(notes_with_ms)
        
        # Summary statistics
        print(f"\n📈 Summary Statistics:")
        tempo_changes = len([e for e in events if e['type'] == 'tempo_change'])
        note_events = len([e for e in events if e['type'] in ['note_on', 'note_off']])
        
        print(f"   Tempo changes: {tempo_changes}")
        print(f"   Note events: {note_events}")
        
        if notes:
            total_duration = max(note.start_time + note.duration for note in notes)
            print(f"   Total duration: {format_time(total_duration)} quarter notes")
        
        if notes_with_ms:
            total_duration_ms = max(note['end_time_ms'] for note in notes_with_ms)
            print(f"   Total duration: {total_duration_ms:.1f} milliseconds ({total_duration_ms/1000:.1f} seconds)")
        
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
  python main.py data/Fur_Elise.mxl --verbose
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
    return analyze_file(args.file, expand_repeats=not args.no_expand, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main()) 