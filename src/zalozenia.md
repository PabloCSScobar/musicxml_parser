 Teraz zajmiemy się aktualizowaniem pozycji. używam get_notes_with_milliseconds i start_time_ms to dla mnie kluczowa informacja dla frontendu ze wzlgędu na to ze na tej podstawie aktualizuję cursor w wizualizacji zapisu nutowego. Jednak gdy utwór ma repetycje to synchronizacja się rozjeżdza poniewaz backend gra drugą repetycje i ms się zwiększa a a na froncie wizualnie jesteśmy już poza repetycją.

Na przykladzie tego fur_elise_suimplified_repetitions.musicxml  przy drugiej repetycji pierwsza nuta przedtaktu (takt 0) powinna mieć pozyucję 0ms a nie 3500ms. Powinno to być inteligentnie przeliczane zeby wziąć tez pod uwagę volty itd.
Jednak ze względu na to ze na podstawie start_time_ms mogą się robić jakies grupowania nut, nie chciałbym się pozbywac tego pola i wolalbym zeby powstal dodatkowy atrybut  start_time_display_ms. Mam nadzieje ze wiesz o co chodzi i pomozesz mi to zaimplementować. Tak jak wczesniej, chciałbym zebys zaczął od napisania testu a potem przjdziemy do implementacji kodu.
 
  W drugiej rpetycji do pierwszej nuty w 3 takcie powinien zostać dodany czas z całego taktu 2. W obecnym rozwiązaniu wizualnie frontend znowu pokaże pierwszą voltę zamiast drugiej mimo ze grana będzie druga volta. 
  Cały display_ms ma zastosowanie dla frontendu i to jest dla mnie współrzędnymi gdzie ma pojawic sie kursor. wiec to ze to jest ta sama pozycja sekwencyjna mnie nie interesuje.
 
 
 measure 0 w drugiej iteracji też powinno mieć 0.0ms. W wizualizacji zapisu nutowego w frontendzie przeciez to to samo miejsce. measure 1 powinno też rozpoczynać się od 500ms.
  A takt 3 czyli druga volta to powinnien być czas wcześniejszych taktów + czas 1 volty.



 jeden takt ma 1500ms a tu różnice są o wiele większe. coś sie ostro popsulo.

Jest 10 taktów + jeden takt 0 który trwa 500ms.
Jeśli dobrze liczę to powinny wychodzić takie czasy:
Nr taktu | MS przy starcie taktu
0: 0ms
1: 500ms
2 (1 volta): 2000ms
0: 0ms
1: 500ms
3 (2 volta): 3500ms
4: 5000ms
5: 6000ms
6 (1 volta): 7500ms
4: 5000ms
5: 6500ms
7: 9000ms
8: 10500ms
9: 12000ms
10: 13500ms


zeby liczyć display_ms chciałbym policzyc get_notes_with_milliseconds na zwyklym score a nie na expanded_score i potem zmergować to jakos  w danymi z notes_with_ms z expanded score. 
wtedy display_ms będzie obliczony prawidlowo 
bo kazdy takt będzie występowal tylko raz jeśli nie beda tam liczone repetycje, no i dodam te wyniki to moich danych z repetycjami tzn dołącze display_ms do odpowiednich taktów.

powinno być coś w stylu
def get_expanded_notes_with_milliseconds(score, expanded_score):
notes_with_ms = get_notes_with_milliseconds(score)
expanded_notes_with_ms = get_notes_with_milliseconds(expanded_score)
notes_with_display = join_display_with_expanded(expanded_notes_with_ms, notes_with_ms)
return notes_with_display

join_display_with_expanded:
lecimy po kolei po nutach/taktach i łączymy je z display_ms z notes_with_ms. nuty są juz posortowane i powinno byc tyle sam nut w każdym takcie w obu listach.



powinno być coś w stylu
def get_expanded_notes_with_milliseconds(score, expanded_score):
notes_with_ms = get_notes_with_milliseconds(score)
expanded_notes_with_ms = get_notes_with_milliseconds(expanded_score)
notes_with_display = join_display_with_expanded(expanded_notes_with_ms, notes_with_ms)
return notes_with_display

join_display_with_expanded:
lecimy po kolei po nutach/taktach i łączymy je z display_ms z notes_with_ms. nuty są juz posortowane i powinno byc tyle sam nut w każdym takcie w obu listach.