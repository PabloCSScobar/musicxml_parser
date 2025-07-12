"""
Testy wydajności i benchmarki dla parsera MusicXML.
"""

import pytest
import time
import os
import tempfile
from pathlib import Path
import psutil
from memory_profiler import profile
from musicxml_parser import MusicXMLParser
from repeat_expander import RepeatExpander, LinearSequenceGenerator


class TestPerformanceBenchmarks:
    """Benchmarki wydajności parsera"""
    
    @pytest.fixture
    def parser(self):
        return MusicXMLParser()
    
    @pytest.fixture
    def expander(self):
        return RepeatExpander()
    
    @pytest.fixture
    def generator(self):
        return LinearSequenceGenerator()
    
    def test_small_file_parsing_speed(self, parser):
        """Benchmark parsowania małego pliku"""
        file_path = "tests/data/simple_score.xml"
        if not os.path.exists(file_path):
            pytest.skip(f"Plik {file_path} nie istnieje")
        
        # Rozgrzewka
        parser.parse_file(file_path)
        
        # Właściwy benchmark
        times = []
        for _ in range(10):
            start_time = time.time()
            score = parser.parse_file(file_path)
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"\nParsowanie małego pliku:")
        print(f"  Średni czas: {avg_time:.4f}s")
        print(f"  Min czas: {min_time:.4f}s")
        print(f"  Max czas: {max_time:.4f}s")
        print(f"  Części: {len(score.parts)}")
        print(f"  Takty: {sum(len(p.measures) for p in score.parts)}")
        
        # Parsowanie małego pliku powinno być szybkie
        assert avg_time < 0.1  # Mniej niż 100ms
    
    def test_large_file_parsing_speed(self, parser):
        """Benchmark parsowania dużego pliku"""
        file_path = "data/Fur_Elise.mxl"
        if not os.path.exists(file_path):
            pytest.skip(f"Plik {file_path} nie istnieje")
        
        # Rozgrzewka
        parser.parse_file(file_path)
        
        # Właściwy benchmark
        times = []
        for _ in range(5):
            start_time = time.time()
            score = parser.parse_file(file_path)
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        total_notes = sum(len(m.notes) for p in score.parts for m in p.measures)
        
        print(f"\nParsowanie dużego pliku:")
        print(f"  Średni czas: {avg_time:.4f}s")
        print(f"  Min czas: {min_time:.4f}s")
        print(f"  Max czas: {max_time:.4f}s")
        print(f"  Części: {len(score.parts)}")
        print(f"  Takty: {sum(len(p.measures) for p in score.parts)}")
        print(f"  Nuty: {total_notes}")
        print(f"  Wydajność: {total_notes/avg_time:.1f} nut/s")
        
        # Parsowanie dużego pliku powinno być rozsądnie szybkie
        assert avg_time < 5.0  # Mniej niż 5 sekund
    
    def test_repeat_expansion_speed(self, parser, expander):
        """Benchmark rozwijania repetycji"""
        file_path = "tests/data/simple_score.xml"
        if not os.path.exists(file_path):
            pytest.skip(f"Plik {file_path} nie istnieje")
        
        score = parser.parse_file(file_path)
        
        # Rozgrzewka
        expander.expand_repeats(score)
        
        # Właściwy benchmark
        times = []
        for _ in range(20):
            start_time = time.time()
            expanded_score = expander.expand_repeats(score)
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        original_measures = sum(len(p.measures) for p in score.parts)
        expanded_measures = sum(len(p.measures) for p in expanded_score.parts)
        
        print(f"\nRozwijanie repetycji:")
        print(f"  Średni czas: {avg_time:.4f}s")
        print(f"  Min czas: {min_time:.4f}s")
        print(f"  Max czas: {max_time:.4f}s")
        print(f"  Oryginalne takty: {original_measures}")
        print(f"  Rozwinięte takty: {expanded_measures}")
        print(f"  Wydajność: {expanded_measures/avg_time:.1f} taktów/s")
        
        # Rozwijanie repetycji powinno być bardzo szybkie
        assert avg_time < 0.01  # Mniej niż 10ms
    
    def test_sequence_generation_speed(self, parser, generator):
        """Benchmark generowania sekwencji"""
        file_path = "data/Fur_Elise.mxl"
        if not os.path.exists(file_path):
            pytest.skip(f"Plik {file_path} nie istnieje")
        
        score = parser.parse_file(file_path)
        
        # Rozgrzewka
        generator.generate_sequence(score)
        
        # Właściwy benchmark
        times = []
        for _ in range(10):
            start_time = time.time()
            notes = generator.generate_sequence(score)
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"\nGenerowanie sekwencji:")
        print(f"  Średni czas: {avg_time:.4f}s")
        print(f"  Min czas: {min_time:.4f}s")
        print(f"  Max czas: {max_time:.4f}s")
        print(f"  Nuty: {len(notes)}")
        print(f"  Wydajność: {len(notes)/avg_time:.1f} nut/s")
        
        # Generowanie sekwencji powinno być szybkie
        assert avg_time < 0.5  # Mniej niż 500ms
    
    def test_memory_usage_small_file(self, parser):
        """Test zużycia pamięci dla małego pliku"""
        file_path = "tests/data/simple_score.xml"
        if not os.path.exists(file_path):
            pytest.skip(f"Plik {file_path} nie istnieje")
        
        process = psutil.Process(os.getpid())
        
        # Zmierz pamięć przed parsowaniem
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Parsuj plik
        score = parser.parse_file(file_path)
        
        # Zmierz pamięć po parsowaniu
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        
        print(f"\nZużycie pamięci (mały plik):")
        print(f"  Przed: {memory_before:.2f} MB")
        print(f"  Po: {memory_after:.2f} MB")
        print(f"  Użyte: {memory_used:.2f} MB")
        
        # Mały plik nie powinien zużywać dużo pamięci
        assert memory_used < 10.0  # Mniej niż 10MB
    
    def test_memory_usage_large_file(self, parser):
        """Test zużycia pamięci dla dużego pliku"""
        file_path = "data/Fur_Elise.mxl"
        if not os.path.exists(file_path):
            pytest.skip(f"Plik {file_path} nie istnieje")
        
        process = psutil.Process(os.getpid())
        
        # Zmierz pamięć przed parsowaniem
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Parsuj plik
        score = parser.parse_file(file_path)
        
        # Zmierz pamięć po parsowaniu
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        
        total_notes = sum(len(m.notes) for p in score.parts for m in p.measures)
        memory_per_note = memory_used / total_notes if total_notes > 0 else 0
        
        print(f"\nZużycie pamięci (duży plik):")
        print(f"  Przed: {memory_before:.2f} MB")
        print(f"  Po: {memory_after:.2f} MB")
        print(f"  Użyte: {memory_used:.2f} MB")
        print(f"  Nuty: {total_notes}")
        print(f"  Pamięć/nuta: {memory_per_note*1024:.2f} KB")
        
        # Duży plik nie powinien zużywać nadmiernie dużo pamięci
        assert memory_used < 100.0  # Mniej niż 100MB
    
    def test_scalability_with_file_size(self, parser):
        """Test skalowalności względem rozmiaru pliku"""
        # Stwórz pliki o różnych rozmiarach
        test_files = []
        file_sizes = [10, 50, 100, 200]  # Liczba taktów
        
        for size in file_sizes:
            xml_content = self._generate_large_xml(size)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
                f.write(xml_content)
                f.flush()
                test_files.append((size, f.name))
        
        try:
            results = []
            for size, file_path in test_files:
                start_time = time.time()
                score = parser.parse_file(file_path)
                end_time = time.time()
                
                parse_time = end_time - start_time
                total_notes = sum(len(m.notes) for p in score.parts for m in p.measures)
                
                results.append((size, parse_time, total_notes))
                print(f"Rozmiar: {size} taktów, Czas: {parse_time:.4f}s, Nuty: {total_notes}")
            
            # Sprawdź czy czas rośnie liniowo z rozmiarem
            if len(results) >= 2:
                time_ratio = results[-1][1] / results[0][1]
                size_ratio = results[-1][0] / results[0][0]
                
                print(f"\nSkalowalność:")
                print(f"  Stosunek rozmiarów: {size_ratio:.2f}")
                print(f"  Stosunek czasów: {time_ratio:.2f}")
                
                # Czas powinien rosnąć w miarę liniowo
                assert time_ratio < size_ratio * 2  # Nie więcej niż 2x wolniej niż liniowo
        
        finally:
            # Usuń pliki testowe
            for _, file_path in test_files:
                os.unlink(file_path)
    
    def _generate_large_xml(self, num_measures):
        """Generuje duży plik XML z określoną liczbą taktów"""
        xml_header = """<?xml version="1.0" encoding="UTF-8"?>
        <score-partwise version="4.0">
          <part-list>
            <score-part id="P1">
              <part-name>Large Test</part-name>
            </score-part>
          </part-list>
          <part id="P1">"""
        
        xml_footer = """
          </part>
        </score-partwise>"""
        
        measures = []
        for i in range(1, num_measures + 1):
            if i == 1:
                measure = f"""
            <measure number="{i}">
              <attributes>
                <divisions>4</divisions>
                <key><fifths>0</fifths></key>
                <time><beats>4</beats><beat-type>4</beat-type></time>
                <clef><sign>G</sign><line>2</line></clef>
              </attributes>
              <note>
                <pitch><step>C</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
              <note>
                <pitch><step>D</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
              <note>
                <pitch><step>E</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
              <note>
                <pitch><step>F</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
            </measure>"""
            else:
                measure = f"""
            <measure number="{i}">
              <note>
                <pitch><step>G</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
              <note>
                <pitch><step>A</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
              <note>
                <pitch><step>B</step><octave>4</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
              <note>
                <pitch><step>C</step><octave>5</octave></pitch>
                <duration>4</duration>
                <voice>1</voice>
                <type>quarter</type>
              </note>
            </measure>"""
            measures.append(measure)
        
        return xml_header + "".join(measures) + xml_footer


class TestMemoryProfiling:
    """Testy profilowania pamięci"""
    
    @pytest.fixture
    def parser(self):
        return MusicXMLParser()
    
    @profile
    def test_memory_profile_parsing(self, parser):
        """Profilowanie pamięci podczas parsowania"""
        file_path = "data/Fur_Elise.mxl"
        if not os.path.exists(file_path):
            pytest.skip(f"Plik {file_path} nie istnieje")
        
        # Ten test wymaga uruchomienia z: python -m memory_profiler test_file.py
        score = parser.parse_file(file_path)
        
        # Wykonaj różne operacje
        expander = RepeatExpander()
        expanded_score = expander.expand_repeats(score)
        
        generator = LinearSequenceGenerator()
        notes = generator.generate_sequence(expanded_score)
        
        print(f"Sparsowano {len(notes)} nut")


class TestConcurrency:
    """Testy współbieżności"""
    
    @pytest.fixture
    def parser(self):
        return MusicXMLParser()
    
    def test_concurrent_parsing(self, parser):
        """Test parsowania współbieżnego"""
        import threading
        import concurrent.futures
        
        file_path = "tests/data/simple_score.xml"
        if not os.path.exists(file_path):
            pytest.skip(f"Plik {file_path} nie istnieje")
        
        def parse_file():
            return parser.parse_file(file_path)
        
        # Test z ThreadPoolExecutor
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(parse_file) for _ in range(10)]
            scores = [future.result() for future in futures]
        end_time = time.time()
        
        concurrent_time = end_time - start_time
        
        # Test sekwencyjny
        start_time = time.time()
        sequential_scores = [parse_file() for _ in range(10)]
        end_time = time.time()
        
        sequential_time = end_time - start_time
        
        print(f"\nWspółbieżność:")
        print(f"  Czas sekwencyjny: {sequential_time:.4f}s")
        print(f"  Czas współbieżny: {concurrent_time:.4f}s")
        print(f"  Przyspieszenie: {sequential_time/concurrent_time:.2f}x")
        
        # Sprawdź czy wyniki są identyczne
        assert len(scores) == len(sequential_scores)
        for i in range(len(scores)):
            assert len(scores[i].parts) == len(sequential_scores[i].parts)
    
    def test_thread_safety(self, parser):
        """Test bezpieczeństwa wątków"""
        import threading
        
        file_path = "tests/data/simple_score.xml"
        if not os.path.exists(file_path):
            pytest.skip(f"Plik {file_path} nie istnieje")
        
        results = []
        errors = []
        
        def parse_with_error_handling():
            try:
                score = parser.parse_file(file_path)
                results.append(score)
            except Exception as e:
                errors.append(e)
        
        # Uruchom wiele wątków jednocześnie
        threads = []
        for _ in range(20):
            thread = threading.Thread(target=parse_with_error_handling)
            threads.append(thread)
            thread.start()
        
        # Poczekaj na zakończenie wszystkich wątków
        for thread in threads:
            thread.join()
        
        # Sprawdź wyniki
        assert len(errors) == 0, f"Błędy w wątkach: {errors}"
        assert len(results) == 20
        
        # Sprawdź czy wszystkie wyniki są identyczne
        first_result = results[0]
        for result in results[1:]:
            assert len(result.parts) == len(first_result.parts)
            assert result.tempo_bpm == first_result.tempo_bpm


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s aby pokazać printy 