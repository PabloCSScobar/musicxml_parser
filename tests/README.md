# Testy Parsera MusicXML

## Przegląd

Komprehensywny zestaw testów dla parsera MusicXML sprawdzający wszystkie aspekty funkcjonalności:

- **Podstawowe parsowanie** - metadane, struktura, elementy MusicXML
- **Rozwijanie repetycji** - proste i złożone struktury repeat/volta
- **Generowanie sekwencji** - liniowe sekwencje nut, podział na ręce
- **Obsługa błędów** - nieprawidłowe pliki, brakujące elementy
- **Przypadki brzegowe** - ekstremalne wartości, specjalne notacje
- **Wydajność** - benchmarki, zużycie pamięci, skalowalność
- **Rzeczywiste pliki** - testy z prawdziwymi plikami MusicXML

## Struktura Testów

```
tests/
├── conftest.py              # Konfiguracja pytest i fixtures
├── test_comprehensive.py    # Główny zestaw testów
├── test_edge_cases.py       # Przypadki brzegowe
├── test_performance.py      # Testy wydajności
├── data/                    # Pliki testowe
│   ├── simple_score.xml     # Prosty plik z repetycjami
│   └── complex_score.xml    # Złożony plik z wieloma funkcjami
└── README.md               # Ten plik
```

## Uruchamianie Testów

### Wszystkie testy
```bash
pytest tests/ -v
```

### Konkretny plik testowy
```bash
pytest tests/test_comprehensive.py -v
```

### Konkretna klasa testów
```bash
pytest tests/test_comprehensive.py::TestMusicXMLParser -v
```

### Konkretny test
```bash
pytest tests/test_comprehensive.py::TestMusicXMLParser::test_parse_simple_score_basic_info -v
```

### Testy z markerami
```bash
# Tylko testy wydajności
pytest tests/ -m performance -v

# Tylko testy integracyjne
pytest tests/ -m integration -v

# Pomiń wolne testy
pytest tests/ -m "not slow" -v
```

### Testy z pokryciem kodu
```bash
pytest tests/ --cov=src --cov-report=html
```

### Testy z outputem
```bash
pytest tests/ -v -s  # -s pokazuje printy
```

## Kategorie Testów

### 1. Testy Podstawowe (`TestMusicXMLParser`)
- Inicjalizacja parsera
- Parsowanie prostych i złożonych plików
- Obsługa formatów .xml, .musicxml, .mxl
- Walidacja nieprawidłowych plików

### 2. Testy Elementów MusicXML (`TestMusicXMLElements`)
- Parsowanie nut i przerw
- Obsługa alteracji (krzyżyki, bemole)
- Zmiany metrum i tonacji
- Zmiany tempa
- Wielogłosowość

### 3. Testy Repetycji (`TestRepeatExpansion`)
- Proste repetycje (repeat forward/backward)
- Volty (ending 1, 2, etc.)
- Volty z wieloma numerami
- Repetycje bez explicit forward

### 4. Testy Sekwencji (`TestLinearSequenceGeneration`)
- Generowanie liniowej sekwencji nut
- Podział na ręce (staff 1/2)
- Zdarzenia playback
- Obliczanie czasów

### 5. Testy Błędów (`TestErrorHandling`)
- Brak wymaganych elementów
- Nieprawidłowe wartości
- Obsługa wyjątków
- Logowanie błędów

### 6. Testy Rzeczywistych Plików (`TestRealWorldFiles`)
- simple_score.xml - prosty plik z repetycjami
- Fur_Elise.mxl - złożony plik skompresowany
- Kompletna analiza end-to-end

### 7. Testy Wydajności (`TestPerformanceBenchmarks`)
- Benchmarki parsowania
- Zużycie pamięci
- Skalowalność
- Współbieżność

### 8. Przypadki Brzegowe (`TestEdgeCases`)
- Ekstremalne wartości pitch/tempo
- Złożone metrum
- Wiele głosów
- Akordy i ozdobniki

## Fixtures

### Parsery i Generatory
- `parser` - instancja MusicXMLParser
- `expander` - instancja RepeatExpander  
- `generator` - instancja LinearSequenceGenerator

### Pliki Testowe
- `sample_files` - słownik ścieżek do plików
- `test_data_dir` - katalog z danymi testowymi

### XML Testowe
- `minimal_musicxml` - minimalny poprawny XML
- `complex_musicxml` - złożony XML z repetycjami
- `invalid_musicxml` - niepoprawny XML
- `temp_xml_file` - tworzy tymczasowy plik

### Pomocnicze
- `test_helpers` - klasa z metodami pomocniczymi

## Wymagania

### Podstawowe
```bash
pip install pytest
```

### Dodatkowe (dla testów wydajności)
```bash
pip install psutil memory-profiler
```

### Wszystkie zależności
```bash
pip install -r requirements.txt
```

## Przykłady Użycia

### Uruchomienie konkretnego testu
```bash
pytest tests/test_comprehensive.py::TestMusicXMLParser::test_parse_simple_score_basic_info -v
```

### Testy wydajności z outputem
```bash
pytest tests/test_performance.py -v -s
```

### Testy bez wolnych operacji
```bash
pytest tests/ -m "not slow" -v
```

### Generowanie raportu pokrycia
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## Debugowanie Testów

### Uruchomienie z debuggerem
```bash
pytest tests/test_comprehensive.py::test_name --pdb
```

### Pokazanie wszystkich printów
```bash
pytest tests/ -v -s --tb=short
```

### Uruchomienie tylko nieudanych testów
```bash
pytest tests/ --lf
```

### Zatrzymanie po pierwszym błędzie
```bash
pytest tests/ -x
```

## Dodawanie Nowych Testów

### 1. Dodaj test do odpowiedniej klasy
```python
class TestMusicXMLParser:
    def test_new_functionality(self, parser):
        # Twój test
        pass
```

### 2. Użyj fixtures
```python
def test_with_fixtures(self, parser, sample_files, test_helpers):
    score = parser.parse_file(sample_files["simple_score"])
    test_helpers.assert_score_validity(score)
```

### 3. Dodaj markery jeśli potrzebne
```python
@pytest.mark.slow
def test_large_operation(self):
    # Wolny test
    pass

@pytest.mark.performance  
def test_benchmark(self):
    # Test wydajności
    pass
```

## Continuous Integration

### GitHub Actions
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        pytest tests/ -v --cov=src
```

## Troubleshooting

### Brak plików testowych
```bash
# Sprawdź czy istnieją pliki
ls tests/data/
ls data/

# Jeśli nie, stwórz je ręcznie lub uruchom setup
python -c "import tests.conftest"
```

### Problemy z importami
```bash
# Upewnij się że src jest w PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/
```

### Wolne testy
```bash
# Pomiń wolne testy
pytest tests/ -m "not slow"

# Uruchom tylko szybkie testy
pytest tests/ -m "not performance and not slow"
```

## Metryki Testów

### Oczekiwane czasy wykonania
- Podstawowe testy: < 1s każdy
- Testy repetycji: < 0.1s każdy  
- Testy sekwencji: < 0.5s każdy
- Testy wydajności: < 10s każdy

### Pokrycie kodu
- Cel: > 90% pokrycia
- Krytyczne ścieżki: 100% pokrycia
- Obsługa błędów: > 80% pokrycia

### Liczba testów
- Podstawowe: ~15 testów
- Elementy MusicXML: ~10 testów
- Repetycje: ~8 testów
- Sekwencje: ~6 testów
- Błędy: ~5 testów
- Wydajność: ~8 testów
- Przypadki brzegowe: ~12 testów

**Razem: ~64 testy**

## Wsparcie

Jeśli masz problemy z testami:
1. Sprawdź czy wszystkie zależności są zainstalowane
2. Upewnij się że pliki testowe istnieją
3. Sprawdź logi błędów
4. Uruchom testy z `-v -s` dla więcej informacji 
5. sprawdz kod Musescore
6. Sprawdz dokumentacje musicxml
7. sprawdz internet