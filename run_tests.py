#!/usr/bin/env python3
"""
Skrypt do uruchamiania testów parsera MusicXML z różnymi opcjami.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Uruchamia komendę i wyświetla wynik"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Komenda: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUKCES")
        else:
            print(f"❌ {description} - BŁĄD (kod: {result.returncode})")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Błąd uruchomienia: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Uruchamianie testów parsera MusicXML")
    parser.add_argument("--all", action="store_true", help="Uruchom wszystkie testy")
    parser.add_argument("--basic", action="store_true", help="Tylko podstawowe testy")
    parser.add_argument("--performance", action="store_true", help="Tylko testy wydajności")
    parser.add_argument("--integration", action="store_true", help="Tylko testy integracyjne")
    parser.add_argument("--edge-cases", action="store_true", help="Tylko przypadki brzegowe")
    parser.add_argument("--coverage", action="store_true", help="Uruchom z pokryciem kodu")
    parser.add_argument("--verbose", "-v", action="store_true", help="Tryb verbose")
    parser.add_argument("--fast", action="store_true", help="Pomiń wolne testy")
    parser.add_argument("--file", help="Konkretny plik testowy")
    parser.add_argument("--test", help="Konkretny test")
    
    args = parser.parse_args()
    
    # Sprawdź czy jesteśmy w odpowiednim katalogu
    if not Path("src").exists() or not Path("tests").exists():
        print("❌ Uruchom skrypt z głównego katalogu projektu (gdzie są foldery src/ i tests/)")
        sys.exit(1)
    
    # Sprawdź czy zależności są zainstalowane
    try:
        import pytest
        import psutil
    except ImportError as e:
        print(f"❌ Brak wymaganych zależności: {e}")
        print("Zainstaluj zależności: pip install -r requirements.txt")
        sys.exit(1)
    
    # Sprawdź czy pliki testowe istnieją
    test_files = [
        "tests/data/simple_score.xml",
        "tests/data/complex_score.xml",
        "data/Fur_Elise.mxl"
    ]
    
    missing_files = [f for f in test_files if not Path(f).exists()]
    if missing_files:
        print("⚠️  Brak niektórych plików testowych:")
        for f in missing_files:
            print(f"   - {f}")
        print("Niektóre testy mogą być pominięte.")
    
    success_count = 0
    total_count = 0
    
    # Ustal jakie testy uruchomić
    if args.all or not any([args.basic, args.performance, args.integration, args.edge_cases, args.file, args.test]):
        # Domyślnie uruchom wszystkie podstawowe testy
        test_configs = [
            ("tests/test_comprehensive.py", "Testy podstawowe"),
            ("tests/test_edge_cases.py", "Przypadki brzegowe"),
        ]
        
        if not args.fast:
            test_configs.append(("tests/test_performance.py", "Testy wydajności"))
    else:
        test_configs = []
        
        if args.basic:
            test_configs.append(("tests/test_comprehensive.py", "Testy podstawowe"))
        
        if args.performance:
            test_configs.append(("tests/test_performance.py", "Testy wydajności"))
        
        if args.integration:
            test_configs.append(("tests/test_comprehensive.py::TestRealWorldFiles", "Testy integracyjne"))
        
        if args.edge_cases:
            test_configs.append(("tests/test_edge_cases.py", "Przypadki brzegowe"))
        
        if args.file:
            test_configs.append((args.file, f"Plik testowy: {args.file}"))
        
        if args.test:
            test_configs.append((args.test, f"Konkretny test: {args.test}"))
    
    # Przygotuj podstawowe argumenty pytest
    base_args = ["python", "-m", "pytest"]
    
    if args.verbose:
        base_args.append("-v")
    
    if args.fast:
        base_args.extend(["-m", "not slow"])
    
    if args.coverage:
        base_args.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
    
    # Uruchom testy
    for test_target, description in test_configs:
        total_count += 1
        cmd = base_args + [test_target]
        
        if run_command(cmd, description):
            success_count += 1
    
    # Podsumowanie
    print(f"\n{'='*60}")
    print(f"📊 PODSUMOWANIE")
    print(f"{'='*60}")
    print(f"Udane testy: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 Wszystkie testy przeszły pomyślnie!")
        
        if args.coverage:
            print("\n📈 Raport pokrycia kodu został wygenerowany:")
            print("   htmlcov/index.html")
            
            # Spróbuj otworzyć raport w przeglądarce
            import webbrowser
            try:
                webbrowser.open("htmlcov/index.html")
                print("   (otwieranie w przeglądarce...)")
            except:
                pass
    else:
        print(f"❌ {total_count - success_count} testów nie powiodło się")
        sys.exit(1)


if __name__ == "__main__":
    main() 