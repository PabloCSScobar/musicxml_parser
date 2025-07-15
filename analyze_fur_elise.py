#!/usr/bin/env python3

from src.musicxml_parser import MusicXMLParser
from src.repeat_expander import RepeatExpander
import logging

logging.basicConfig(level=logging.DEBUG)

def main():
    parser = MusicXMLParser()
    score = parser.parse_file('data/Fur_Elise_simplified_repetitions.musicxml')

    print('=== ANALIZA STRUKTURY REPETYCJI ===')
    print(f'Ilość części: {len(score.parts)}')
    
    if score.parts:
        part = score.parts[0]
        print(f'Ilość taktów oryginalnych: {len(part.measures)}')
        
        print('\n🔄 Repeat and Volta Analysis:')
        print('   Repeat Marks:')
        for i, measure in enumerate(part.measures):
            if measure.repeat_start or measure.repeat_end:
                repeat_info = []
                if measure.repeat_start:
                    repeat_info.append('REPEAT START')
                if measure.repeat_end:
                    repeat_info.append(f'REPEAT END (×{measure.repeat_count})')
                print(f'      • Measure {measure.number}: {" + ".join(repeat_info)}')
        
        print('   Volta Marks:')
        for i, measure in enumerate(part.measures):
            if measure.ending_numbers and measure.ending_type:
                print(f'      • Measure {measure.number}: VOLTA {measure.ending_numbers} ({measure.ending_type.value})')

        print('\n🎼 Oczekiwana sekwencja taktów po rozwinięciu:')
        print('   1. Takty 0,1,2 (pierwsza volta)')
        print('   2. Takty 0,1,3 (druga volta)')  
        print('   3. Takty 4,5,6 (pierwsza volta)')
        print('   4. Takty 4,5,7 (druga volta)')
        print('   5. Takty 8,9,10')
        print('   Razem: 15 taktów (0,1,2,0,1,3,4,5,6,4,5,7,8,9,10)')

        print('\n🧪 Testujemy RepeatExpander:')
        expander = RepeatExpander()
        expanded_score = expander.expand_repeats(score)
        
        if expanded_score.parts:
            expanded_part = expanded_score.parts[0]
            print(f'Ilość taktów po rozwinięciu: {len(expanded_part.measures)}')
            
            expanded_numbers = [m.number for m in expanded_part.measures]
            print(f'Aktualna sekwencja: {expanded_numbers}')
            
            expected = [0,1,2,0,1,3,4,5,6,4,5,7,8,9,10]
            print(f'Oczekiwana sekwencja: {expected}')
            
            if expanded_numbers == expected:
                print('✅ POPRAWNIE!')
            else:
                print('❌ BŁĄD - sekwencje się różnią')

if __name__ == "__main__":
    main() 