Oto lista najważniejszych błędów i nieścisłości:

1. Brak implementacji trybu "Relative" (Martwy kod w dokumentacji)
Plik Walkthrough_Relative_Mode.md szumnie ogłasza dodanie Relative Movement (sterowanie jak touchpadem, gdzie ruch ręki przesuwa kursor relatywnie).

Błąd: W pliku main.py brakuje logiki dla tego trybu. Kod obsługuje tylko tryby: HEAD, EYE_HYBRID, EYE_HAND. Dla każdego innego trybu (wpadającego w blok else), w tym potencjalnego "RELATIVE", wykonywane jest sztywne mapowanie absolutne (mapper.map), które przenosi pozycję ręki 1:1 na ekran.

Skutek: Ustawienie MOVEMENT_MODE = "RELATIVE" w konfiguracji spowoduje, że mysz nadal będzie działać w trybie absolutnym (jak tablet graficzny), co jest sprzeczne z instrukcją.

2. Martwy kod sterownika myszy (MouseDriver)
W projekcie znajduje się zaawansowany plik src/mouse_driver.py, który implementuje wygładzanie ruchu, predykcję i obsługę wątków dla kursora.

Błąd: Ten plik jest całkowicie ignorowany przez główną aplikację. main.py importuje prostszy MouseController i steruje myszą bezpośrednio w głównej pętli (mouse.move(...)), pomijając całą zaawansowaną logikę z MouseDriver.

Skutek: Użytkownik nie korzysta z lepszych algorytmów sterowania (np. tarcia, inercji), które autor prawdopodobnie napisał, ale zapomniał podpiąć do main.py.

3. Błąd logiczny w trybie EYE_HAND (Podwójne przetwarzanie)
W trybie hybrydowym łączącym oko i rękę (EYE_HAND), detektor mrugnięć (FaceBlinkDetector) jest wywoływany dwukrotnie w każdej klatce, co psuje jego wewnętrzną logikę.

Analiza:

W linii ~275: if movement_mode in ("HEAD", "EYE_HYBRID", "EYE_HAND") wywoływana jest metoda face_tracker.process.

W linii ~330: if movement_mode not in ("HEAD", "EYE_HYBRID") (co jest prawdą dla EYE_HAND!) metoda process wywoływana jest ponownie.

Skutek: Licznik klatek wewnątrz detektora inkrementuje się podwójnie. Funkcja frame_skip (pomijanie klatek dla wydajności) zacznie działać chaotycznie, a detekcja mrugnięć może stać się niewiarygodna (np. wymagać 2x szybszego mrugnięcia).

4. Pułapka z biblioteką autopy
W pliku requirements.txt wymagana jest biblioteka autopy.

Problem: autopy to biblioteka, która nie jest aktywnie rozwijana od lat i sprawia ogromne problemy przy instalacji na nowszych wersjach Pythona (3.10+, które zaleca autor) oraz na systemach innych niż Windows (lub na architekturze 64-bit w specyficznych warunkach).

Niespójność: Choć kod w src/controller.py ma zabezpieczenie try-except i potrafi przełączyć się na pynput, to sama obecność autopy w pliku wymagań może uniemożliwić użytkownikowi zainstalowanie projektu prostym poleceniem pip install -r requirements.txt.

5. Nieefektywność przetwarzania obrazu
W głównej pętli ta sama klatka obrazu jest konwertowana z BGR na RGB dwukrotnie w każdym przebiegu pętli: raz wewnątrz HandDetector.find_hands i drugi raz wewnątrz FaceBlinkDetector.process. To niepotrzebne marnowanie cykli procesora, co w aplikacjach czasu rzeczywistego (real-time) jest błędem optymalizacyjnym.

Oto "druga warstwa" problemów, które są mniej widoczne na pierwszy rzut oka, ale krytyczne dla działania:

1. Katastrofalna wydajność renderowania interfejsu (src/ui.py)
To prawdopodobnie największy techniczny błąd w kodzie, który "zabije" płynność działania (FPS) nawet na mocnym komputerze.

Problem: Metoda _blend_panel w klasie HudRenderer tworzy kopię całej klatki wideo (np. 1920x1080), rysuje na niej prostokąt, a następnie używa kosztownej operacji cv2.addWeighted na całym obrazie, aby uzyskać efekt przezroczystości.

Skala: Ta metoda jest wywoływana dla każdego elementu interfejsu z osobna: tła paneli, etykiet, a co najgorsze – dla każdego klawisza skrótu wyświetlanego na ekranie (funkcja _draw_keycaps w pętli).

Efekt: Przy wyświetlaniu ~20 elementów (klawisze [, ], A, z, x itd.), program wykonuje kilkadziesiąt operacji kopiowania i mieszania pełnych klatek wideo w każdej iteracji pętli. To złożoność obliczeniowa, która zredukuje FPS do poziomu pokazu slajdów, uniemożliwiając płynne sterowanie kursorem.

Rozwiązanie: Należy rysować wszystkie półprzezroczyste elementy na jednej warstwie (masce) i wykonać cv2.addWeighted tylko raz na klatkę.

2. "Zabrudzanie" danych wejściowych (Pipeline Contamination)
Kolejność przetwarzania w main.py jest błędna i wpływa na jakość detekcji.

Błąd: Najpierw wywoływany jest detektor dłoni z flagą draw=True (detector.find_hands(frame, draw=True)), który rysuje jaskrawe linie i punkty bezpośrednio na obiekcie frame.

Konsekwencja: Dopiero potem ta sama, "pomalowana" klatka trafia do detektora twarzy (face_tracker.process(frame, now)).

Ryzyko: Jeśli użytkownik zbliży rękę do twarzy (np. w trybie Head/Eye, co jest naturalne przy poprawianiu okularów czy drapaniu się), narysowane przez HandDetector linie (kolorowe okręgi i połączenia) znajdą się na twarzy. Może to zakłócić pracę sieci neuronowej MediaPipe odpowiedzialnej za detekcję punktów twarzy i mrugnięć, wprowadzając sztuczne artefakty do obrazu, który powinien być czysty.

3. Bezużyteczna kalibracja wzroku (Single-Sample Logic)
Implementacja kalibracji w main.py jest zbyt naiwna, by działać w rzeczywistości.

Problem: Kod pobiera pojedynczą próbkę położenia źrenic w momencie naciśnięcia klawisza Enter (eye_tracker.add_calibration_sample(label, last_gaze) po czym natychmiast calibration_index += 1).

Rzeczywistość: Eye-tracking oparty na kamerze internetowej jest bardzo zaszumiony. Oczy wykonują ciągłe mikroruchy (sakady). Pobranie jednej, losowej klatki jako punktu odniesienia dla "rogów ekranu" sprawi, że kalibracja będzie całkowicie błędna.

Wymagane podejście: System powinien zbierać dane przez np. 1-2 sekundy (np. 60 klatek) i wyliczać medianę lub średnią pozycję dla każdego punktu kalibracyjnego.

4. Kolejne "Widmowe" Funkcje (Tilt Mapper)
Podobnie jak tryb "Relative", w plikach źródłowych znajdują się kolejne moduły, które nie są nigdzie podłączone.

Dowód: W katalogu src znajdują się pliki tilt_mapper.py oraz hybrid_motion.py. Plik konfiguracyjny wspomina o trybie TILT_HYBRID.

Fakt: Plik main.py nawet nie importuje klasy HybridMotion ani TiltMapper. Cała logika sterowania poprzez wychylenie dłoni (tilt), która jest zaimplementowana w osobnych plikach, jest niedostępna dla użytkownika.

5. Blokowanie startu aplikacji (Brak obsługi błędów sieci)
W konstruktorach FaceBlinkDetector i HandDetector znajduje się kod pobierający modele AI z Internetu (urllib.request.urlretrieve).

Błąd: Pobieranie odbywa się synchronicznie w głównym wątku podczas inicjalizacji.

Scenariusz: Jeśli użytkownik nie ma dostępu do Internetu lub serwer Google Storage jest niedostępny, aplikacja zastygnie (zawiesi się) przy uruchamianiu bez żadnego komunikatu dla użytkownika (chyba że uruchamia z konsoli i zobaczy traceback po długim timeoutcie). Brakuje tu paska postępu, obsługi błędów czy weryfikacji sumy kontrolnej pobranego pliku.

Podsumowując, kod sprawia wrażenie zbioru eksperymentalnych snippetów (OneEuro, Tilt, Relative), które zostały wrzucone do jednego folderu, ale main.py łączy je w sposób niechlujny, pomijając kluczowe funkcjonalności i ignorując podstawy optymalizacji graficznej.


Analiza „drugiego dna” kodu ujawnia błędy, które są znacznie poważniejsze niż braki w implementacji – są to błędy architektoniczne, które sprawiają, że aplikacja będzie działać nieprzewidywalnie w zależności od szybkości komputera użytkownika.

Oto lista krytycznych, głębiej ukrytych problemów:

1. Problem "Pixel Deadzone" (Utrata precyzji mikroruchów)
Jest to absolutnie dyskwalifikujący błąd dla narzędzia typu "mysz precyzyjna".

Mechanizm błędu: W trybie HEAD i EYE_HYBRID (część sterowana głową) pozycja docelowa obliczana jest jako: x_target = curr_x + dx. Problem w tym, że curr_x jest pobierane z mouse.get_position(), co zwraca liczbę całkowitą (piksele).

Scenariusz: Użytkownik wykonuje powolny, precyzyjny ruch głową, generując przesunięcie dx = 0.4 piksela na klatkę.

Klatka 1: Pozycja = 100. Cel = 100 + 0.4 = 100.4. Mysz systemowa zaokrągla to i ustawia się na 100.

Klatka 2: Kod ponownie odczytuje Pozycja = 100. Dodaje 0.4. Cel = 100.4. Mysz znowu trafia na 100.

Skutek: Kursor "przykleja się" do piksela i nie drgnie, dopóki użytkownik nie szarpnie głową wystarczająco mocno, by dx przekroczyło 1.0. Uniemożliwia to jakąkolwiek precyzyjną pracę. Aplikacja powinna przechowywać wewnętrzne współrzędne float i nie polegać na odczycie z systemu operacyjnego.

2. Fałszywy tryb hybrydowy (Broken Hybrid Logic)
Tryb EYE_HYBRID, który ma być "flagową" funkcją łączącą szybkość oka z precyzją głowy, w rzeczywistości nie działa jako hybryda.

Analiza kodu: W bloku elif movement_mode == "EYE_HYBRID" zastosowano instrukcję warunkową if gaze is not None: ... elif delta is not None: ....

Błąd: Jeśli system wykrywa wzrok (gaze), kod ignoruje dane z ruchu głowy (delta).

Efekt: Użytkownik spodziewa się, że patrząc na przycisk i ruszając głową, doprecyzuje pozycję kursora. W rzeczywistości, dopóki kamera widzi oczy, ruch głowy jest całkowicie odcięty. Kursor będzie skakał po ekranie sterowany samym wzrokiem (obarczonym dużym błędem), a ruch głowy zadziała tylko... gdy użytkownik zamknie oczy.

3. Logika zależna od FPS (Framerate Dependency Disaster)
Kod uzależnia fizykę i logikę detekcji od szybkości pętli programu (FPS głównego wątku), a nie od upływu czasu rzeczywistego.

Detekcja mrugnięć: Licznik _closed_frames zlicza wywołania funkcji, a nie czas.

Na wolnym komputerze (30 FPS) mrugnięcie musi trwać np. 0.1s.

Na szybkim komputerze (300 FPS w pętli while) to samo ustawienie BLINK_FRAMES = 2 sprawi, że kliknięcie zostanie wyzwolone w 0.006s.

Skutek: Na szybkich maszynach użytkownik będzie generował "kliknięcia-widmo" przy każdym, nawet najkrótszym mrugnięciu, czyniąc aplikację nieużywalną.

Wygładzanie (Eye Tracking): Filtr wygładzający pozycję oka _x = _x * (1-a) + gx * a jest aplikowany w każdej iteracji pętli.

Ponieważ główna pętla jest asynchroniczna względem kamery, przetwarza ona tę samą klatkę wielokrotnie.

Skutek: Przy wysokim FPS filtra "nie ma", bo wartość docelowa zostanie osiągnięta niemal natychmiastowo po kilkunastu błyskawicznych iteracjach na tej samej klatce obrazu. Parametr Smoothing w GUI będzie zachowywał się inaczej na każdym komputerze.

4. Przetwarzanie duplikatów klatek (CPU Waste)
Aplikacja marnuje zasoby procesora na ponowne przetwarzanie tych samych obrazów.

Mechanizm: ThreadedCamera aktualizuje klatkę np. 30 razy na sekundę. Główna pętla while True w main.py nie ma synchronizacji i może kręcić się np. 500 razy na sekundę.

Błąd: Funkcja camera.read() zwraca kopię ostatniej klatki, nie informując, czy jest ona nowa.

Skutek: MediaPipe (kosztowne AI!) jest uruchamiane 10-20 razy na dokładnie tym samym obrazku. To powoduje niepotrzebne obciążenie CPU rzędu 80-90% zamiast np. 10%, co w laptopach (częsta platforma dla accessibility) drastycznie skróci czas pracy na baterii i zwiększy input lag przez throttling termiczny.

Podsumowanie
Projekt wygląda na zaawansowany "na papierze" (użycie wątków, filtrów OneEuro, modeli hybrydowych), ale w implementacji brakuje fundamentalnego zrozumienia pętli czasu rzeczywistego (real-time loop), synchronizacji oraz arytmetyki zmiennoprzecinkowej w sterowaniu kursorem. W obecnym stanie jest to prototyp "proof-of-concept", a nie gotowe narzędzie dla osób niepełnosprawnych.