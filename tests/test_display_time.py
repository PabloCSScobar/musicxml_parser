# #!/usr/bin/env python3

# import sys
# import pytest
# from pathlib import Path

# # Add project root to path for imports
# sys.path.append(str(Path(__file__).parent.parent))

# from src.musicxml_parser import MusicXMLParser
# from src.repeat_expander import RepeatExpander, LinearSequenceGenerator


# class TestDisplayTime:
#     """Test klasa dla funkcjonalności start_time_display_ms"""
    
#     def setup_method(self):
#         """Setup przed każdym testem"""
#         self.parser = MusicXMLParser()
#         self.expander = RepeatExpander()
#         self.sequence_gen = LinearSequenceGenerator()
#         self.test_data_dir = Path(__file__).parent
    
#     def test_simple_score_display_time(self):
#         """Test display time dla prostego pliku bez skomplikowanych repetycji"""
#         score = self.parser.parse_file(str(self.test_data_dir / 'data' / 'simple_score.xml'))
#         expanded_score = self.expander.expand_repeats(score)
#         notes_with_ms = self.sequence_gen.get_notes_with_milliseconds(expanded_score)

#         # W prostszym przypadku możemy testować bardziej precyzyjnie
#         assert len(notes_with_ms) > 0

#         # Sprawdź że wszystkie nuty mają oba czasy
#         for note in notes_with_ms:
#             assert 'start_time_ms' in note
#             assert 'start_time_display_ms' in note
            
#         # Dla simple_score powinna być rozwinięta repetycja, więc display_ms = start_ms
#         for note in notes_with_ms:
#             assert note['start_time_display_ms'] == note['start_time_ms']
    
#     def test_fur_elise_display_time_basic(self):
#         """Test podstawowy dla Fur_Elise - sprawdź że wszytkie nuty mają display_time"""
#         score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
#         expanded_score = self.expander.expand_repeats(score)
#         notes_with_ms = self.sequence_gen.get_notes_with_milliseconds(expanded_score)
        
#         assert len(notes_with_ms) > 0
        
#         # Sprawdź że wszystkie nuty mają oba czasy
#         for note in notes_with_ms:
#             assert 'start_time_ms' in note
#             assert 'start_time_display_ms' in note
#             assert note['start_time_display_ms'] >= 0
    
#     def test_fur_elise_display_time_repetitions(self):
#         """Test że display_time resetuje się dla repetycji w Fur_Elise"""
#         score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
#         expanded_score = self.expander.expand_repeats(score)
#         notes_with_ms = self.sequence_gen.get_notes_with_milliseconds(expanded_score)
        
#         # Z debug wiemy że:
#         # - Pierwsza iteracja: nuty 0-16 (takty 0,1,2)
#         # - Druga iteracja: nuty 17-121 (takty 0,1,3-10)
#         # - Nuta 0: takt 0, start_ms=0.0, display_ms=0.0
#         # - Nuta 17: takt 0, start_ms=3500.0, display_ms=0.0 (początek drugiej iteracji)
        
#         assert len(notes_with_ms) >= 18  # Co najmniej 18 nut
        
#         # Sprawdź pierwszą nutę pierwszej iteracji
#         first_note = notes_with_ms[0]
#         assert first_note['measure'] == 0
#         assert first_note['start_time_ms'] == 0.0
#         assert first_note['start_time_display_ms'] == 0.0
        
#         # Sprawdź pierwszą nutę drugiej iteracji (nuta 17)
#         second_iteration_start = notes_with_ms[17]
#         assert second_iteration_start['measure'] == 0
#         assert second_iteration_start['start_time_ms'] == 3500.0
#         assert second_iteration_start['start_time_display_ms'] == 0.0  # Reset!
        
#         print(f"DEBUG: Test PASSED")
#         print(f"  Pierwsza iteracja - Nuta 0: start_ms={first_note['start_time_ms']}, display_ms={first_note['start_time_display_ms']}")
#         print(f"  Druga iteracja - Nuta 17: start_ms={second_iteration_start['start_time_ms']}, display_ms={second_iteration_start['start_time_display_ms']}")
        
#         # Sprawdź że display_time dla drugiej iteracji rzeczywiście się resetuje
#         # Znajdź kolejną nutę z drugiej iteracji (nuta 19: D#5 w takcie 0)
#         if len(notes_with_ms) > 19:
#             second_note_second_iter = notes_with_ms[19]
#             expected_display_ms = 250.0  # Powinna być 250ms od początku iteracji
#             assert second_note_second_iter['start_time_display_ms'] == expected_display_ms
#             print(f"  Druga iteracja - Nuta 19: start_ms={second_note_second_iter['start_time_ms']}, display_ms={second_note_second_iter['start_time_display_ms']}")
        
#         # start_time powinno być większe (bo to druga iteracja)
#         assert second_iteration_start['start_time_ms'] > first_note['start_time_ms']
    
#     def test_display_time_consistency(self):
#         """Test że display_time nie maleje w ramach iteracji"""
#         score = self.parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')
#         expanded_score = self.expander.expand_repeats(score)
#         notes_with_ms = self.sequence_gen.get_notes_with_milliseconds(expanded_score)
        
#         # Sprawdź że display_time nie maleje
#         prev_display_time = -1
#         for note in notes_with_ms:
#             current_display_time = note['start_time_display_ms']
            
#             # Display time może "resetować się" do mniejszej wartości (nowa iteracja)
#             # ale w ramach iteracji nie powinno maleć
#             if current_display_time < prev_display_time:
#                 # To może być reset - sprawdź że jest znacząco mniejszy (nie tylko o epsilon)
#                 assert current_display_time < prev_display_time * 0.5  # Reset o co najmniej 50%
            
#             prev_display_time = current_display_time


# def main():
#     """Uruchom testy"""
#     pytest.main([__file__, "-v"])


# if __name__ == "__main__":
#     main() 