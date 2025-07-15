#!/usr/bin/env python3
"""
Skrypt do rozwijania powtórzeń w plikach MusicXML/MXL używając music21.
Pobiera plik MusicXML lub MXL, rozwija powtórzenia i zapisuje z sufiksem '_expanded'.
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from music21 import converter, stream
except ImportError:
    print("Błąd: Biblioteka music21 nie jest zainstalowana.")
    print("Zainstaluj ją używając: pip install music21")
    sys.exit(1)


def expand_repeats(input_file: str, output_file: str = None) -> str:
    """
    Rozwija powtórzenia w pliku MusicXML/MXL.
    
    Args:
        input_file: Ścieżka do pliku wejściowego
        output_file: Ścieżka do pliku wyjściowego (opcjonalne)
    
    Returns:
        Ścieżka do utworzonego pliku
    """
    # Sprawdź czy plik istnieje
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Plik {input_file} nie istnieje")
    
    # Wczytaj plik
    print(f"Wczytuję plik: {input_file}")
    try:
        score = converter.parse(input_file)
    except Exception as e:
        raise Exception(f"Błąd podczas wczytywania pliku: {e}")
    
    # Rozwij powtórzenia
    print("Rozwijam powtórzenia...")
    try:
        expanded_score = score.expandRepeats()
    except Exception as e:
        raise Exception(f"Błąd podczas rozwijania powtórzeń: {e}")
    
    # Określ nazwę pliku wyjściowego
    if output_file is None:
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_expanded{input_path.suffix}"
    
    # Zapisz plik
    print(f"Zapisuję do: {output_file}")
    try:
        expanded_score.write('musicxml', fp=output_file)
    except Exception as e:
        raise Exception(f"Błąd podczas zapisywania pliku: {e}")
    
    return str(output_file)


def main():
    """Główna funkcja programu."""
    parser = argparse.ArgumentParser(
        description="Rozwija powtórzenia w plikach MusicXML/MXL używając music21"
    )
    parser.add_argument(
        "input_file", 
        help="Ścieżka do pliku MusicXML lub MXL"
    )
    parser.add_argument(
        "-o", "--output", 
        help="Ścieżka do pliku wyjściowego (domyślnie: {input}_expanded.{ext})"
    )
    
    args = parser.parse_args()
    
    try:
        # Sprawdź rozszerzenie pliku
        input_path = Path(args.input_file)
        if input_path.suffix.lower() not in ['.xml', '.musicxml', '.mxl']:
            print("Ostrzeżenie: Plik może nie być w formacie MusicXML/MXL")
        
        # Rozwij powtórzenia
        output_file = expand_repeats(args.input_file, args.output)
        
        print(f"✅ Sukces! Plik z rozwiniętymi powtórzeniami zapisany jako: {output_file}")
        
    except FileNotFoundError as e:
        print(f"❌ Błąd: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Błąd: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 