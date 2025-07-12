# Architektura Parsera MusicXML

## Przegląd Ogólny

Parser MusicXML to zaawansowany system parsowania plików nutowych inspirowany architekturą MuseScore. Implementuje dwuprzebiegowe parsowanie dla maksymalnej precyzji i obsługuje pełen zakres funkcji MusicXML 4.0.

## Architektura Systemu

### 🏗️ Dwuprzebiegowe Parsowanie

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Plik MusicXML │───▶│     Pass 1      │───▶│     Pass 2      │
│  (.xml/.mxl)    │    │   (Struktura)   │    │   (Zawartość)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────┐         ┌─────────────┐
                       │  Metadane   │         │ Kompletny   │
                       │ & Struktura │         │   Obiekt    │
                       │   Części    │         │ MusicXMLScore│
                       └─────────────┘         └─────────────┘
```

#### **Pass 1: Analiza Struktury**
- **Cel**: Zbieranie metadanych i struktury utworu
- **Zadania**:
  - Parsowanie nagłówka (`<work>`, `<identification>`)
  - Analiza listy części (`<part-list>`)
  - Tworzenie szkieletu struktury danych
  - Walidacja podstawowej składni XML
  - Zbieranie informacji o błędach

#### **Pass 2: Parsowanie Zawartości**
- **Cel**: Szczegółowe parsowanie treści muzycznej
- **Zadania**:
  - Parsowanie nut, przerw, akordów
  - Obsługa repetycji i volt
  - Analiza zmian tempa i metrum
  - Obliczanie czasów i duracji
  - Przypisywanie elementów do pięciolinii

## Struktura Klas

### 📊 Hierarchia Danych

```python
MusicXMLScore
├── title: str
├── composer: str
├── tempo_bpm: float
├── time_signature: str
├── key_signature: int
├── parts: List[MusicXMLPart]
└── errors: List[str]

MusicXMLPart
├── name: str
├── instrument: str
├── staves: int
├── measures: List[MusicXMLMeasure]
└── midi_channel: int

MusicXMLMeasure
├── number: int
├── time_signature: Optional[str]
├── tempo_bpm: Optional[float]
├── key_signature: Optional[int]
├── notes: List[MusicXMLNote]
├── has_repeat_start: bool
├── has_repeat_end: bool
├── repeat_count: int
├── volta_numbers: List[int]
└── volta_type: Optional[str]

MusicXMLNote
├── pitch: str  # "C4", "F#5", "rest"
├── duration: Fraction
├── measure: int
├── staff: int
├── voice: int
├── start_time: Fraction
├── is_rest: bool
├── is_chord: bool
└── tie: Optional[str]
```

### 🔧 Klasy Funkcjonalne

#### **MusicXMLParser**
```python
class MusicXMLParser:
    def __init__(self, log_level=logging.INFO):
        self.logger = MusicXMLLogger(log_level)
    
    def parse_file(self, file_path: str) -> MusicXMLScore:
        """Główna metoda parsowania pliku"""
        
    def _parse_xml(self, root: ET.Element) -> MusicXMLScore:
        """Dwuprzebiegowe parsowanie XML"""
```

#### **MusicXMLParserPass1**
```python
class MusicXMLParserPass1:
    def parse_structure(self, root: ET.Element) -> Dict:
        """Parsowanie struktury i metadanych"""
        
    def _parse_score_header(self, root: ET.Element) -> Dict:
        """Parsowanie nagłówka utworu"""
        
    def _parse_part_list(self, root: ET.Element) -> List[Dict]:
        """Parsowanie listy części"""
```

#### **MusicXMLParserPass2**
```python
class MusicXMLParserPass2:
    def parse_content(self, root: ET.Element, structure: Dict) -> MusicXMLScore:
        """Parsowanie zawartości muzycznej"""
        
    def _parse_part(self, part_elem: ET.Element, part_info: Dict) -> MusicXMLPart:
        """Parsowanie pojedynczej części"""
        
    def _parse_measure(self, measure_elem: ET.Element, part_info: Dict) -> MusicXMLMeasure:
        """Parsowanie taktu"""
```

## Proces Parsowania

### 1. **Inicjalizacja**
```python
parser = MusicXMLParser()
score = parser.parse_file("example.xml")
```

### 2. **Wykrywanie Formatu**
```python
def _detect_format(self, file_path: str) -> Tuple[str, Any]:
    """Wykrywa format pliku i zwraca dane"""
    if file_path.endswith('.mxl'):
        return 'compressed', self._extract_mxl(file_path)
    elif file_path.endswith(('.xml', '.musicxml')):
        return 'xml', self._load_xml(file_path)
    else:
        raise ValueError(f"Nieobsługiwany format: {file_path}")
```

### 3. **Pass 1: Struktura**
```python
def parse_structure(self, root: ET.Element) -> Dict:
    structure = {
        'work': self._parse_work(root),
        'identification': self._parse_identification(root),
        'part_list': self._parse_part_list(root),
        'defaults': self._parse_defaults(root)
    }
    return structure
```

### 4. **Pass 2: Zawartość**
```python
def parse_content(self, root: ET.Element, structure: Dict) -> MusicXMLScore:
    score = MusicXMLScore()
    
    # Metadane z Pass 1
    score.title = structure['work'].get('title', 'Untitled')
    score.composer = structure['identification'].get('composer', 'Unknown')
    
    # Parsowanie części
    for part_elem in root.findall('.//part'):
        part = self._parse_part(part_elem, structure)
        score.parts.append(part)
    
    return score
```

## Obsługa Elementów MusicXML

### 🎵 **Elementy Muzyczne**

#### **Nuty (`<note>`)**
```python
def _parse_note(self, note_elem: ET.Element) -> MusicXMLNote:
    note = MusicXMLNote()
    
    # Pitch lub Rest
    if note_elem.find('rest') is not None:
        note.pitch = 'rest'
        note.is_rest = True
    else:
        pitch_elem = note_elem.find('pitch')
        if pitch_elem is not None:
            step = pitch_elem.find('step').text
            octave = pitch_elem.find('octave').text
            alter_elem = pitch_elem.find('alter')
            alter = int(alter_elem.text) if alter_elem is not None else 0
            note.pitch = self._format_pitch(step, alter, octave)
    
    # Duration
    duration_elem = note_elem.find('duration')
    if duration_elem is not None:
        note.duration = Fraction(int(duration_elem.text), self.divisions)
    
    # Voice i Staff
    voice_elem = note_elem.find('voice')
    note.voice = int(voice_elem.text) if voice_elem is not None else 1
    
    staff_elem = note_elem.find('staff')
    note.staff = int(staff_elem.text) if staff_elem is not None else 1
    
    return note
```

#### **Atrybuty (`<attributes>`)**
```python
def _parse_attributes(self, attr_elem: ET.Element) -> Dict:
    attributes = {}
    
    # Divisions
    divisions_elem = attr_elem.find('divisions')
    if divisions_elem is not None:
        attributes['divisions'] = int(divisions_elem.text)
    
    # Key Signature
    key_elem = attr_elem.find('key')
    if key_elem is not None:
        fifths_elem = key_elem.find('fifths')
        if fifths_elem is not None:
            attributes['key_signature'] = int(fifths_elem.text)
    
    # Time Signature
    time_elem = attr_elem.find('time')
    if time_elem is not None:
        beats = time_elem.find('beats').text
        beat_type = time_elem.find('beat-type').text
        attributes['time_signature'] = f"{beats}/{beat_type}"
    
    return attributes
```

### 🔄 **Repetycje i Volty**

#### **Barlines z Repetycjami**
```python
def _parse_barline(self, barline_elem: ET.Element) -> Dict:
    barline = {}
    
    # Repeat
    repeat_elem = barline_elem.find('repeat')
    if repeat_elem is not None:
        direction = repeat_elem.get('direction')
        if direction == 'forward':
            barline['repeat_start'] = True
        elif direction == 'backward':
            barline['repeat_end'] = True
            times = repeat_elem.get('times')
            barline['repeat_count'] = int(times) if times else 2
    
    # Ending (Volta)
    ending_elem = barline_elem.find('ending')
    if ending_elem is not None:
        number = ending_elem.get('number')
        ending_type = ending_elem.get('type')
        barline['volta_numbers'] = [int(n) for n in number.split(',')]
        barline['volta_type'] = ending_type
    
    return barline
```

#### **Directions z Tempo**
```python
def _parse_direction(self, direction_elem: ET.Element) -> Optional[float]:
    direction_type = direction_elem.find('direction-type')
    if direction_type is None:
        return None
    
    # Metronome
    metronome_elem = direction_type.find('metronome')
    if metronome_elem is not None:
        beat_unit = metronome_elem.find('beat-unit')
        per_minute = metronome_elem.find('per-minute')
        if beat_unit is not None and per_minute is not None:
            # Konwersja na quarter note BPM
            note_value = self._note_type_to_value(beat_unit.text)
            bpm = float(per_minute.text)
            return bpm * (note_value / 0.25)  # Normalize to quarter note
    
    return None
```

## Rozwijanie Repetycji

### 🎯 **RepeatExpander**

```python
class RepeatExpander:
    def expand_repeats(self, score: MusicXMLScore) -> MusicXMLScore:
        """Rozwija wszystkie repetycje w utworze"""
        expanded_score = copy.deepcopy(score)
        
        for part in expanded_score.parts:
            part.measures = self._expand_part_repeats(part.measures)
        
        return expanded_score
    
    def _expand_part_repeats(self, measures: List[MusicXMLMeasure]) -> List[MusicXMLMeasure]:
        """Rozwija repetycje w pojedynczej części"""
        expanded_measures = []
        i = 0
        
        while i < len(measures):
            measure = measures[i]
            
            if measure.has_repeat_start:
                # Znajdź koniec repetycji
                repeat_end_idx = self._find_repeat_end(measures, i)
                if repeat_end_idx is not None:
                    repeat_section = measures[i:repeat_end_idx + 1]
                    expanded_section = self._expand_repeat_section(repeat_section)
                    expanded_measures.extend(expanded_section)
                    i = repeat_end_idx + 1
                else:
                    expanded_measures.append(measure)
                    i += 1
            else:
                expanded_measures.append(measure)
                i += 1
        
        return expanded_measures
```

### 🎼 **Obsługa Volt**

```python
def _expand_repeat_section(self, measures: List[MusicXMLMeasure]) -> List[MusicXMLMeasure]:
    """Rozwija sekcję z repetycją, obsługując volty"""
    expanded = []
    repeat_count = measures[-1].repeat_count
    
    for iteration in range(1, repeat_count + 1):
        for measure in measures:
            if measure.volta_numbers:
                # Sprawdź czy ta volta ma być zagrana w tej iteracji
                if iteration in measure.volta_numbers:
                    expanded.append(copy.deepcopy(measure))
            else:
                expanded.append(copy.deepcopy(measure))
    
    return expanded
```

## Generowanie Sekwencji Liniowej

### 🎹 **LinearSequenceGenerator**

```python
class LinearSequenceGenerator:
    def generate_sequence(self, score: MusicXMLScore) -> List[MusicXMLNote]:
        """Generuje liniową sekwencję wszystkich nut"""
        all_notes = []
        
        for part in score.parts:
            part_notes = self._generate_part_sequence(part)
            all_notes.extend(part_notes)
        
        # Sortuj według czasu rozpoczęcia
        all_notes.sort(key=lambda n: (n.start_time, n.staff, n.voice))
        return all_notes
    
    def _generate_part_sequence(self, part: MusicXMLPart) -> List[MusicXMLNote]:
        """Generuje sekwencję nut dla pojedynczej części"""
        notes = []
        current_time = Fraction(0)
        
        for measure in part.measures:
            measure_notes = self._process_measure_notes(measure, current_time)
            notes.extend(measure_notes)
            current_time += self._calculate_measure_duration(measure)
        
        return notes
```

### 🎯 **Podział na Ręce**

```python
def get_notes_by_hand(self, score: MusicXMLScore) -> Tuple[List[MusicXMLNote], List[MusicXMLNote]]:
    """Dzieli nuty na prawą i lewą rękę"""
    right_hand = []
    left_hand = []
    
    for part in score.parts:
        for measure in part.measures:
            for note in measure.notes:
                if note.staff == 1:  # Górna pięciolinia
                    right_hand.append(note)
                elif note.staff == 2:  # Dolna pięciolinia
                    left_hand.append(note)
    
    return right_hand, left_hand
```

## Obsługa Błędów

### 🚨 **MusicXMLLogger**

```python
class MusicXMLLogger:
    def __init__(self, log_level=logging.INFO):
        self.logger = logging.getLogger('MusicXMLParser')
        self.logger.setLevel(log_level)
        self.errors = []
        self.warnings = []
    
    def log_error(self, message: str, element: Optional[ET.Element] = None):
        """Loguje błąd z kontekstem"""
        if element is not None:
            line_info = f" (line {element.sourceline})" if hasattr(element, 'sourceline') else ""
            full_message = f"{message}{line_info}"
        else:
            full_message = message
        
        self.errors.append(full_message)
        self.logger.error(full_message)
    
    def log_warning(self, message: str, element: Optional[ET.Element] = None):
        """Loguje ostrzeżenie z kontekstem"""
        if element is not None:
            line_info = f" (line {element.sourceline})" if hasattr(element, 'sourceline') else ""
            full_message = f"{message}{line_info}"
        else:
            full_message = message
        
        self.warnings.append(full_message)
        self.logger.warning(full_message)
```

### 🔍 **Walidacja**

```python
def _validate_structure(self, root: ET.Element) -> List[str]:
    """Waliduje podstawową strukturę MusicXML"""
    errors = []
    
    # Sprawdź root element
    if root.tag not in ['score-partwise', 'score-timewise']:
        errors.append(f"Nieprawidłowy element główny: {root.tag}")
    
    # Sprawdź part-list
    part_list = root.find('part-list')
    if part_list is None:
        errors.append("Brak wymaganego elementu part-list")
    
    # Sprawdź części
    parts = root.findall('part')
    if not parts:
        errors.append("Brak części w utworze")
    
    return errors
```

## Optymalizacje Wydajności

### ⚡ **Lazy Loading**

```python
class LazyMusicXMLNote:
    def __init__(self, note_elem: ET.Element, context: Dict):
        self._element = note_elem
        self._context = context
        self._parsed = False
        self._note_data = None
    
    def _parse_if_needed(self):
        if not self._parsed:
            self._note_data = self._parse_note_element()
            self._parsed = True
    
    @property
    def pitch(self) -> str:
        self._parse_if_needed()
        return self._note_data.pitch
```

### 🔄 **Caching**

```python
from functools import lru_cache

class MusicXMLParser:
    @lru_cache(maxsize=128)
    def _parse_pitch(self, step: str, alter: int, octave: int) -> str:
        """Cache dla konwersji pitch"""
        alterations = {-2: 'bb', -1: 'b', 0: '', 1: '#', 2: '##'}
        return f"{step}{alterations[alter]}{octave}"
```

## Przykłady Użycia

### 🎼 **Podstawowe Parsowanie**

```python
# Parsowanie pliku
parser = MusicXMLParser()
score = parser.parse_file('example.xml')

# Informacje o utworze
print(f"Tytuł: {score.title}")
print(f"Kompozytor: {score.composer}")
print(f"Tempo: {score.tempo_bpm} BPM")
print(f"Metrum: {score.time_signature}")

# Analiza części
for i, part in enumerate(score.parts):
    print(f"Część {i+1}: {part.name}")
    print(f"  Instrument: {part.instrument}")
    print(f"  Pięciolinie: {part.staves}")
    print(f"  Takty: {len(part.measures)}")
```

### 🔄 **Rozwijanie Repetycji**

```python
# Rozwijanie repetycji
expander = RepeatExpander()
expanded_score = expander.expand_repeats(score)

# Porównanie
original_measures = sum(len(part.measures) for part in score.parts)
expanded_measures = sum(len(part.measures) for part in expanded_score.parts)

print(f"Oryginał: {original_measures} taktów")
print(f"Po rozwinięciu: {expanded_measures} taktów")
```

### 🎹 **Generowanie Sekwencji**

```python
# Generowanie liniowej sekwencji
generator = LinearSequenceGenerator()
notes = generator.generate_sequence(expanded_score)

# Podział na ręce
right_hand, left_hand = generator.get_notes_by_hand(expanded_score)

print(f"Wszystkie nuty: {len(notes)}")
print(f"Prawa ręka: {len(right_hand)}")
print(f"Lewa ręka: {len(left_hand)}")

# Pierwsze 10 nut
for i, note in enumerate(notes[:10]):
    print(f"{i+1}. {note.pitch} (t={note.start_time}, dur={note.duration})")
```

## Rozszerzalność

### 🔌 **Plugin System**

```python
class MusicXMLPlugin:
    def process_note(self, note: MusicXMLNote, context: Dict) -> MusicXMLNote:
        """Przetwarzanie nuty"""
        return note
    
    def process_measure(self, measure: MusicXMLMeasure, context: Dict) -> MusicXMLMeasure:
        """Przetwarzanie taktu"""
        return measure

class DynamicsPlugin(MusicXMLPlugin):
    def process_note(self, note: MusicXMLNote, context: Dict) -> MusicXMLNote:
        # Dodaj obsługę dynamiki
        return note
```

### 🎯 **Custom Parsery**

```python
class CustomMusicXMLParser(MusicXMLParser):
    def _parse_custom_element(self, element: ET.Element) -> Dict:
        """Parsowanie niestandardowych elementów"""
        return {}
    
    def _post_process_score(self, score: MusicXMLScore) -> MusicXMLScore:
        """Post-processing po parsowaniu"""
        return score
```

## Testowanie

### 🧪 **Struktura Testów**

```python
class TestMusicXMLParser:
    def test_basic_parsing(self):
        """Test podstawowego parsowania"""
        
    def test_repeat_expansion(self):
        """Test rozwijania repetycji"""
        
    def test_error_handling(self):
        """Test obsługi błędów"""
        
    def test_performance(self):
        """Test wydajności"""
```

### 📊 **Benchmarki**

```python
def benchmark_parser():
    """Benchmark wydajności parsera"""
    import time
    
    parser = MusicXMLParser()
    
    start_time = time.time()
    score = parser.parse_file('large_score.xml')
    parse_time = time.time() - start_time
    
    print(f"Parsowanie: {parse_time:.2f}s")
    print(f"Nuty: {sum(len(m.notes) for p in score.parts for m in p.measures)}")
    print(f"Wydajność: {len(score.parts) / parse_time:.1f} części/s")
```

## Podsumowanie

Parser MusicXML implementuje profesjonalną architekturę inspirowaną MuseScore, oferując:

- **Dwuprzebiegowe parsowanie** dla maksymalnej precyzji
- **Kompletną obsługę** repetycji, volt i zmian tempa
- **Modułową strukturę** ułatwiającą rozszerzanie
- **Robustną obsługę błędów** z szczegółowym logowaniem
- **Optymalizacje wydajności** dla dużych plików
- **Łatwą integrację** z systemami playback i analizy

Architektura umożliwia łatwe dodawanie nowych funkcji i integrację z różnymi systemami muzycznymi. 