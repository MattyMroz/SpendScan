# SpendScan - aplikacja analizująca wydatki na podstawie zdjęć paragonów

Mateusz Mróz, Igor Typiński, Mateusz Słoń, Jakub Bryła, Piotr Marczak, dr hab. inż. Ewa Korzeniewska, prof. PŁ (opiekun projektu)

Politechnika Łódzka, WEEIA, Informatyka, Łódź, Polska

> ℹ️ **Uwaga redakcyjna (do usunięcia przed oddaniem):** nagłówki sekcji i ich numeracja (I, II, A, B) są zgodne z szablonem `06-raport-proj-komp-2026.md`. Miejsca oznaczone `[...]` oraz placeholdery rysunków `![Rys. N ...]` wymagają uzupełnienia: prawdziwych zrzutów ekranu, wykresów i danych osobowych zespołu. Każdy rysunek ma już przygotowane odwołanie w tekście i opis, co ma przedstawiać.

## STRESZCZENIE

W raporcie przedstawiono SpendScan - wieloużytkownikową aplikację webową (klient-serwer) do skanowania paragonów i analizy wydatków. System przekształca zdjęcie paragonu w ustrukturyzowane dane poprzez trzystopniowy potok realizowany po stronie serwera: rozpoznawanie tekstu modelem OCR na GPU (PaddleOCR-VL), ekstrakcję pozycji i kwot przez model językowy Google Gemini oraz zapis do bazy PostgreSQL. Zebrane dane prezentowane są na pulpicie analitycznym z wykresami kategorii, sklepów i trendów czasowych. Potrzebę produktu zweryfikowano ankietą (55 ważnych odpowiedzi): 78% respondentów nie zna dokładnie swoich wydatków w podziale na kategorie, a 92% nie korzysta z żadnego dedykowanego narzędzia (aplikacji ani arkusza). Zbudowano działający prototyp obejmujący uwierzytelnianie (bcrypt, JWT w ciasteczku HttpOnly, ochrona CSRF), wielostronicowe paragony jako jeden wpis oraz pulpit z sześcioma typami wizualizacji. Backend pokryto 42 testami jednostkowymi (wszystkie przechodzą), a jakość kodu egzekwuje potok CI (ruff, mypy, pytest). Główny wniosek jest następujący: skanowanie paragonów jest realistycznym scenariuszem dla większości użytkowników, a kluczową barierą okazał się nie wysiłek wpisywania, lecz brak czasu i motywacji. Obserwacja ta wyznacza kierunek dalszego rozwoju.

## KEYWORDS

SpendScan, skanowanie paragonów, OCR, PaddleOCR-VL, llama.cpp, model językowy, Google Gemini, FastAPI, PostgreSQL, analiza wydatków, aplikacja webowa, architektura klient-serwer, walidacja pomysłu

## I. WSTĘP

### A. Obszar / tło działań

Kontrola codziennych wydatków jest powszechnym problemem, którego skala rośnie wraz z dominacją zakupów detalicznych w sieciach dyskontowych. Mimo dostępności aplikacji finansowych (Monefy, YNAB, Wallet) większość osób nie prowadzi systematycznej ewidencji wydatków. Przeprowadzona przez zespół ankieta walidacyjna (55 ważnych odpowiedzi, kwiecień 2026) pokazała, że 78% respondentów nie zna dokładnie kwot wydawanych na poszczególne kategorie, a 82% nigdy nie korzystało z żadnej aplikacji do śledzenia wydatków (pytanie P7). Jednocześnie 64% respondentów ma kontakt z paragonem przynajmniej przez chwilę po zakupach, co czyni paragon naturalnym, powszechnie dostępnym źródłem danych o wydatkach.

Istotną obserwacją jest bariera wejścia. Tradycyjne aplikacje wymagają ręcznego wpisywania każdego zakupu, co, jak wskazują respondenci, którzy porzucili takie narzędzia, zniechęca do regularnego korzystania. Problem nie polega na braku narzędzi, lecz na tym, że istniejące rozwiązania wymagają zbyt dużego, powtarzalnego wysiłku.

### B. Cel Projektu

Celem projektu było zbudowanie wieloużytkownikowej aplikacji webowej, która minimalizuje wysiłek użytkownika do jednej czynności, czyli zrobienia zdjęcia paragonu. Całą resztę, to znaczy rozpoznanie tekstu, wyodrębnienie pozycji i kwot, kategoryzację, zapis i analizę, aplikacja wykonuje automatycznie po stronie serwera. SpendScan realizuje to w architekturze klient-serwer: użytkownik przesyła zdjęcia przez przeglądarkę, a serwer wykonuje rozpoznawanie tekstu (własny model OCR), strukturyzację i zapis do współdzielonej bazy danych z izolacją kont użytkowników. Jedynym zewnętrznym elementem jest model językowy do strukturyzacji danych. Rozwiązanie odpowiada na zidentyfikowaną lukę: brak narzędzia, które działa przy najmniejszym możliwym oporze, prosto i intuicyjnie dla użytkownika.

## II. STAN WIEDZY

### A. Konstruktywna analiza istniejących rozwiązań

Na rynku funkcjonują dwie główne klasy rozwiązań do kontroli wydatków. Pierwsza to manualne aplikacje budżetowe (Monefy, YNAB, Wallet, Spendee), w których użytkownik samodzielnie wprowadza transakcje lub kategoryzuje wydatki. Ich słabością jest wspomniana wysoka bariera wejścia i konieczność systematyczności. Druga klasa to integracje bankowe (agregatory transakcji), które automatycznie pobierają historię z konta. Ich ograniczeniem jest brak danych o pojedynczych pozycjach paragonu (bank widzi kwotę transakcji w sklepie, ale nie wie, że kupiono chleb i kawę) oraz obawy o prywatność związane z dostępem do rachunku bankowego.

Trzecia, węższa kategoria to aplikacje skanujące paragony (np. funkcje OCR w niektórych aplikacjach budżetowych). Większość z nich opiera się na zewnętrznych, chmurowych usługach OCR (np. Google Vision, AWS Textract), co rodzi koszty oraz wątpliwości dotyczące prywatności (zdjęcia paragonów trafiają do usług trzecich stron). SpendScan różni się tym, że rozpoznawanie tekstu realizuje własny model OCR uruchamiany na serwerze aplikacji, bez wysyłania obrazów do zewnętrznej chmury OCR. Dane pozostają w obrębie infrastruktury aplikacji.

Rozwój wielojęzycznych modeli wizyjno-językowych do parsowania dokumentów, takich jak PaddleOCR-VL (Cui i in., 2024), umożliwił rozpoznawanie tekstu o jakości wcześniej dostępnej tylko w usługach chmurowych, lecz przy zachowaniu możliwości uruchomienia lokalnie. Kluczowym czynnikiem jest tu projekt llama.cpp (Gerganov i in., 2023), który pozwala uruchamiać modele w skwantyzowanym formacie GGUF na komputerach z umiarkowanymi zasobami GPU. To właśnie połączenie tych dwóch technologii stanowi techniczną podstawę odróżniającą SpendScan od rozwiązań zależnych od zewnętrznej chmury OCR.

### B. Uzasadnienie i formy rozwiązania

Pytanie badawcze projektu brzmi: *czy możliwe jest zbudowanie narzędzia do kontroli wydatków, które redukuje wysiłek użytkownika do zrobienia zdjęcia?* Luka rynkowa jest wyraźna, ponieważ ankieta wykazała, że 92% respondentów nie używa żadnego dedykowanego narzędzia, mimo że problem jest powszechnie odczuwany. SpendScan wypełnia tę lukę przez połączenie własnego, serwerowego OCR (brak kosztów i zależności od zewnętrznej chmury rozpoznawania) z modelem językowym do inteligentnej strukturyzacji danych (odporność na różne formaty paragonów różnych sieci handlowych). Spodziewaną korzyścią jest narzędzie o minimalnej barierze wejścia, które realnie ma szansę być używane regularnie.

## III. OPIS ROZWIĄZANIA

### A. Opis techniczny rozwiązania

SpendScan to aplikacja webowa o architekturze monolitycznej: backend w języku Python (FastAPI) serwuje zarówno API REST, jak i statyczny frontend, a całość komunikuje się z bazą PostgreSQL i dwoma modelami AI. Kluczową decyzją architektoniczną jest potok przetwarzania paragonu w trzech etapach (rys. 1).

![Rys. 1 - Architektura przepływu danych w SpendScan: przesłanie zdjęć -> OCR (PaddleOCR-VL na llama-server) -> ekstrakcja danych (Gemini) -> zapis (PostgreSQL) -> analiza (pulpit). Diagram do przygotowania na podstawie poniższego opisu.](placeholder-rys-01-architektura.png)

Na rys. 1 przedstawiono pełny przepływ danych. Po przesłaniu zdjęć przez interfejs webowy, każda strona paragonu trafia do modułu OCR, następnie złączony tekst i obrazy przekazywane są do modelu językowego, a ustrukturyzowany wynik zapisywany jest w bazie i udostępniany w warstwie analitycznej.

**Stos technologiczny.** Backend opiera się na Pythonie 3.13, FastAPI, SQLModel (ORM) i Pydantic v2 (walidacja danych). Rozpoznawanie tekstu realizuje model multimodalny PaddleOCR-VL 1.5 w kwantyzacji Q8 (format GGUF, ~1,4 GB), serwowany lokalnie przez `llama-server` z biblioteki llama.cpp. Strukturyzację danych wykonuje Google Gemini. Baza danych to PostgreSQL 18 uruchamiana w kontenerze Docker. Frontend zbudowano w czystym HTML/CSS/JavaScript z biblioteką Chart.js (wykresy) i Lucide (ikony). Narzędziami zarządzania projektem są: `uv` (zależności), `ruff` (linter i formatter), `mypy` (typowanie statyczne) oraz `pytest` (testy).

**Moduł OCR.** Rozpoznawanie tekstu realizuje serwer aplikacji za pomocą własnego modelu, bez korzystania z zewnętrznej usługi OCR. Przy pierwszym uruchomieniu model jest jednorazowo pobierany z biblioteki modeli Hugging Face. Następnie aplikacja uruchamia lokalnie program `llama-server`, który udostępnia model przez wewnętrzny interfejs sieciowy dostępny tylko na serwerze. Komunikacja z tym modelem odbywa się przez zapytania sieciowe: aplikacja wysyła obraz paragonu (zakodowany w formacie tekstowym base64) wraz z poleceniem rozpoznania tekstu, a model odsyła odczytany tekst. Wynik jest następnie oczyszczany ze znaczników technicznych i błędnych powtórzeń. Na wypadek niewystarczającej pamięci karty graficznej zaimplementowano mechanizm ponawiania z automatycznym zmniejszaniem rozdzielczości obrazu (z 1024 do 512 pikseli). Poniższy fragment pokazuje rdzeń wywołania modelu (`backend/spendscan/ocr/paddle.py`):

```python
start = time.perf_counter()
messages = [
    ChatMessage(role="user", content=[
        ContentPart(type="image_url", image_url={"url": self._image_to_data_uri(pil_image)}),
        ContentPart(type="text", text=prompt),
    ]),
]
response = self._client.chat(messages=messages, max_tokens=self.config.max_tokens,
                             temperature=self.config.temperature, repeat_penalty=self.config.repeat_penalty)
elapsed_ms = (time.perf_counter() - start) * 1000
cleaned_text, text_lines = parse_ocr_output(response.content)
```

**Moduł strukturyzacji (model językowy).** Rozpoznany tekst wraz z obrazami paragonu jest wysyłany do modelu językowego Google Gemini. Komunikacja z tym modelem przebiega przez internet, za pośrednictwem oficjalnego interfejsu programistycznego Google. W odpowiedzi model zwraca uporządkowane dane w formacie JSON: nazwę sklepu, datę, pozycje (nazwa, ilość, cena), kwoty, rabaty i kategorie. Aby zwiększyć niezawodność, zaimplementowano łańcuch zapasowy: w razie niepowodzenia aplikacja kolejno próbuje innych modeli (model podstawowy, następnie modele zapasowe) oraz dwóch kluczy dostępowych, ponawiając próby. Otrzymana odpowiedź jest sprawdzana w trzech etapach (odczyt danych, naprawa błędów formatu, walidacja struktury) i uzupełniana ostrzeżeniami o niespójnościach kwotowych (z tolerancją 0,05 PLN). Działanie łańcucha zapasowego ilustruje fragment `backend/spendscan/llm/gemini.py`:

```python
for attempt in range(1, self._settings.gemini_retry_attempts + 1):
    for api_key in api_keys:
        for model_name in models:
            try:
                raw_text = await self._call_api(api_key=api_key, model_name=model_name,
                                                ocr_text=ocr_text, image_paths=resolved_image_paths)
                return self._validator.validate(raw_text, raw_ocr_text=ocr_text)
            except (ExternalServiceError, OutputValidationError) as exc:
                last_error = exc
```

**Potok przetwarzania.** Komponent `ReceiptPipeline` orkiestruje całość według zasady "jeden paragon = wiele stron = jedno wywołanie modelu językowego". Każda strona przechodzi przez OCR osobno, teksty są złączane z nagłówkami stron, a następnie całość trafia w jednym wywołaniu do Gemini. Dzięki temu wielostronicowy paragon jest traktowany jako jeden spójny wpis. Potok jest odporny na częściowe błędy, ponieważ jeśli część stron zawiedzie OCR, przetwarzanie kontynuuje z dostępnym tekstem.

**Baza danych.** Schemat obejmuje 10 tabel (m.in. `users`, `receipts`, `receipt_items`, `receipt_images`, `categories`, `folders`, `budgets`, `subscriptions`). Zastosowano wzorzec Repository, w którym dostęp do bazy enkapsulują dedykowane klasy. Istotną decyzją projektową jest przechowywanie kwot pieniężnych jako liczb całkowitych w groszach, co pozwala uniknąć błędów zaokrągleń charakterystycznych dla liczb zmiennoprzecinkowych. Obrazy paragonów zapisywane są bezpośrednio w bazie jako dane binarne.

**Uwierzytelnianie i bezpieczeństwo.** System realizuje pełny cykl uwierzytelniania. Hasła hashowane są algorytmem bcrypt (biblioteka passlib). Po zalogowaniu wydawany jest token JWT (HS256) przechowywany w ciasteczku HttpOnly, niedostępnym dla JavaScriptu, co chroni przed kradzieżą tokenu w ataku XSS. Ochronę przed atakami CSRF zapewnia wzorzec podwójnego ciasteczka (double-submit) z porównaniem odpornym na ataki czasowe (`secrets.compare_digest`). Każdy użytkownik ma dostęp wyłącznie do własnych paragonów (izolacja przez `user_id`). Fragment `backend/spendscan/auth/dependencies.py` pokazuje weryfikację CSRF:

```python
if bearer_token is None and request.method.upper() not in _SAFE_METHODS:
    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
    csrf_header = request.headers.get(CSRF_HEADER_NAME)
    if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_cookie, csrf_header):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or missing CSRF token")
```

**Interfejs użytkownika.** Frontend składa się z 7 stron (logowanie, rejestracja, skanowanie, edycja, statystyki, kalendarz, informacje), serwowanych przez FastAPI z tego samego procesu (jeden origin, brak problemów z CORS). Aplikacja obsługuje dwa języki (PL/EN) oraz tryb ciemny. Na rys. 2 i rys. 3 przedstawiono kluczowe ekrany aplikacji.

![Rys. 2 - Ekran skanowania paragonu z animowanym wskaźnikiem postępu (4 etapy: przesłanie -> OCR -> ekstrakcja -> gotowe). Zrzut ekranu do wykonania z działającej aplikacji (strona index.html).](placeholder-rys-02-skanowanie.png)

![Rys. 3 - Ekran edycji rozpoznanego paragonu: po lewej oryginalne zdjęcie, po prawej formularz z pozycjami, kwotami i walidacją spójności. Zrzut ekranu do wykonania (strona edit.html).](placeholder-rys-03-edycja.png)

Na rys. 2 pokazano proces skanowania z wizualizacją czterech etapów przetwarzania, a na rys. 3 widnieje ekran korekty, na którym użytkownik może poprawić rozpoznane dane przed zapisem.

### B. Zarządzanie projektem i pracą zespołową

Projekt realizowano w pięcioosobowym zespole w modelu pracy opartym na osobnych gałęziach dla poszczególnych funkcji, scalanych do gałęzi głównej przez Pull Requesty z przeglądem kodu (code review). Repozytorium prowadzono na platformie GitHub. Stosowano konwencję opisowych komunikatów commitów (Conventional Commits, z prefiksami `feat:`, `fix:`, `chore:`) oraz uporządkowane nazewnictwo gałęzi według wzorca `typ/autor-temat`. Taki proces zapewnił przejrzystą historię zmian i kontrolę jakości kodu przed scaleniem.

Jakość kodu egzekwowano na trzech poziomach. Lokalnie odbywało się to przez wyzwalacze pre-commit (automatyczny ruff i mypy przy każdym commicie, blokada bezpośrednich commitów do gałęzi głównej). W repozytorium zdalnym działał potok ciągłej integracji (CI) w usłudze GitHub Actions, który przy każdej zmianie automatycznie uruchamiał trzy zadania: analizę statyczną kodu, sprawdzanie poprawności typów i testy. Dzięki temu kod naruszający przyjęte standardy nie mógł trafić do gałęzi głównej.

![Rys. 4 - Organizacja pracy zespołowej: przykładowy Pull Request z przeglądem kodu na platformie GitHub lub tablica zadań projektu. Zrzut ekranu do wykonania.](placeholder-rys-04-github.png)

Na rys. 4 przedstawiono aktywność zespołu w repozytorium. Linter `ruff` skonfigurowano z 35 zestawami reguł, a `mypy` w trybie ścisłym (`strict`), co wymusza pełne typowanie kodu. W zakresie projektowania uniwersalnego i dostępności zastosowano semantyczny HTML, czytelne wskaźniki fokusu na polach formularzy oraz dwujęzyczny interfejs; ograniczenia w tym obszarze omówiono uczciwie w sekcji VI.

## IV. BADANIA/TESTY/ŚRODOWISKO

Walidację projektu przeprowadzono dwutorowo: badanie potrzeb użytkowników (ankieta) oraz testy techniczne kodu.

**Badanie potrzeb (ankieta walidacyjna).** Przed implementacją zweryfikowano sensowność produktu ankietą złożoną z 13 pytań, zbudowaną wokół 7 hipotez biznesowych z wcześniej zdefiniowanymi progami akceptacji. Ankietę przeprowadzono online w dniach 10–21 kwietnia 2026. Zebrano 57 odpowiedzi, z czego 55 uznano za ważne (2 wykluczono, ponieważ byli to respondenci niedokonujący samodzielnie zakupów). Każda hipoteza miała ustalony z góry próg liczbowy, co pozwoliło na obiektywną ocenę potwierdzenia lub obalenia (metoda zapobiegająca naginaniu wyników do założeń).

**Testy techniczne.** Kluczową logikę aplikacji pokryto zestawem 42 testów automatycznych, które obejmują najważniejsze obszary systemu: uwierzytelnianie (hashowanie haseł, tokeny JWT, ciasteczka, ochrona CSRF), interfejs API (przesyłanie paragonów oraz operacje dodawania, odczytu, edycji i usuwania), potok rozpoznawania i strukturyzacji danych, sprawdzanie poprawności odpowiedzi modelu językowego oraz moduł analityczny. Testy uruchamiane są na odizolowanej bazie danych w pamięci, niezależnej od bazy produkcyjnej, co zapewnia ich powtarzalność. Cały zestaw wykonuje się w około 47 sekund i wszystkie 42 testy przechodzą bez błędów. Środowisko uruchomieniowe wymaga: języka Python w wersji 3.13 lub nowszej, karty graficznej NVIDIA z obsługą CUDA (model OCR zajmuje około 3 GB pamięci karty), systemu Docker (baza PostgreSQL) oraz klucza dostępowego do modelu Google Gemini.

## V. WYNIKI I ANALIZA

### A. Wyniki ankiety walidacyjnej

W Tabeli I zebrano wynik weryfikacji wszystkich 7 hipotez biznesowych wraz z ustalonymi wcześniej progami. Świadomie raportujemy również hipotezy obalone, ponieważ pełen, nieselektywny obraz danych jest istotniejszy niż potwierdzenie wszystkich założeń.

**TABELA I**
**WERYFIKACJA HIPOTEZ BIZNESOWYCH**

| # | Hipoteza | Próg | Wynik | Status |
|---|----------|------|-------|--------|
| H1 | Ludzie nie znają wydatków w kategoriach | ≥50% | 78% | Potwierdzona |
| H2 | Brak dedykowanego śledzenia wydatków | ≥40% | 92% bez narzędzia | Częściowo |
| H3 | Ręczne wpisywanie to główna bariera | ≥40% | 24% (3. miejsce) | Obalona |
| H4 | Dostęp do paragonów | ≥40% | 64% | Potwierdzona |
| H5 | Wizualizacja motywuje do działania | ≥50% | 29% / 57% odpowiadających | Niejednoznaczna |
| H6 | Prywatność nie jest blokerem | ≤30% | 16% | Potwierdzona |
| H7 | Aktywne poszukiwanie rozwiązania | ≥20% | 16% | Obalona (blisko progu) |

Jak pokazano w Tabeli I, trzy hipotezy zostały jednoznacznie potwierdzone (H1, H4, H6), dwie obalone (H3, H7), a dwie pozostały niejednoznaczne (H2, H5). Na rys. 5 przedstawiono rozkład odpowiedzi na pytanie o znajomość własnych wydatków (hipoteza H1).

![Rys. 5 - Wykres kołowy: znajomość własnych wydatków w kategoriach (P5). "Mniej więcej, ale nie dokładnie" 62%, "Tak, mam pod kontrolą" 22%, "Nie mam pojęcia" 16%. Dane sumują się do 100% - wskazany wykres kołowy. Do wygenerowania na podstawie danych w tekście.](placeholder-rys-05-p5-kategorie.png)

Na rys. 5 widać, że łącznie 78% respondentów (62% "mniej więcej" oraz 16% "nie mam pojęcia") nie zna dokładnie swoich wydatków w podziale na kategorie. Wynik ten jest wyraźnie powyżej progu 50% i potwierdza hipotezę H1.

Na rys. 6 przedstawiono sposób, w jaki respondenci kontrolują wydatki (pytanie P4). Tylko 4% używa dedykowanej aplikacji, a 4% arkusza kalkulacyjnego, co oznacza, że zaledwie 8% korzysta z dedykowanego narzędzia. Pozostałe 92% kontroluje wydatki metodami pasywnymi (konto bankowe, pamięć) lub wcale.

![Rys. 6 - Wykres kołowy: sposób kontroli wydatków (P4). Konto bankowe 55%, w pamięci 16%, nie śledzę 15%, kartka 5%, aplikacja 4%, arkusz 4%, inne 2%. Dane sumują się do 100% - wykres kołowy. Do wygenerowania.](placeholder-rys-06-p4-kontrola.png)

Na rys. 7 zestawiono bariery w kontroli wydatków (pytanie P6, wielokrotny wybór). Ten wynik jest najbardziej zaskakujący i zarazem najważniejszy dla pozycjonowania produktu.

![Rys. 7 - Wykres słupkowy: bariery w kontroli wydatków (P6, wielokrotny wybór - procenty nie sumują się do 100%, dlatego wykres słupkowy zamiast kołowego). Brak czasu 44%, brak motywacji 42%, trudność kategoryzacji 27%, nie dotyczy 24%, ręczne wpisywanie 24%, gubienie paragonów 5%. Do wygenerowania.](placeholder-rys-07-p6-bariery.png)

### B. Analiza i dyskusja

Wyniki ankiety potwierdzają istnienie i powszechność problemu (H1, H4, H6), ale wymagają ostrożnej interpretacji. Hipoteza H3, mówiąca że główną barierą jest ręczne wpisywanie, została **obalona**. Ręczne wpisywanie znalazło się dopiero na trzecim miejscu (24%), za brakiem czasu (44%) i brakiem motywacji (42%). To istotny wniosek korygujący pierwotne założenie projektu. Automatyzacja wpisywania jest argumentem wartościowym, ale nie najważniejszym, ponieważ głównym problemem użytkowników jest inercja i niechęć do samego procesu śledzenia. Wynika z tego rekomendacja produktowa: SpendScan powinien komunikować przede wszystkim "zero wysiłku", a nie wyłącznie "automatyzację".

Należy też uczciwie wskazać ograniczenia samego badania. Próba jest mała (55 osób) i silnie zdominowana przez jedną grupę demograficzną, gdyż 71% respondentów to osoby w wieku 18–24 lat, a 58% to uczniowie i studenci. Wyniki są zatem reprezentatywne głównie dla młodych użytkowników i nie należy ich uogólniać na całą populację. Hipoteza H5 (wizualizacja motywuje do działania) pozostała niejednoznaczna, ponieważ aż 29 z 55 osób nie odpowiedziało na pytanie otwarte. Przy tak dużej liczbie braków danych formułowanie mocnych wniosków byłoby nieuprawnione.

Od strony technicznej projekt osiągnął zakładany cel: powstał działający prototyp realizujący pełen przepływ od zdjęcia do analizy. Zestaw 42 przechodzących testów potwierdza poprawność kluczowej logiki aplikacji, obejmując uwierzytelnianie, potok przetwarzania, walidację danych oraz agregacje analityczne. Połączenie pozytywnych wyników walidacji potrzeb (ankieta) z potwierdzoną testami poprawnością implementacji pozwala uznać, że projekt odpowiada na zdefiniowany problem.

## VI. WNIOSKI I PERSPEKTYWY ROZWOJU

Projekt SpendScan zakończył się zbudowaniem działającego prototypu, który realizuje pełną ścieżkę: od zdjęcia paragonu, przez serwerowe rozpoznawanie tekstu i strukturyzację modelem językowym, po zapis w bazie i analizę na pulpicie. Mocne strony rozwiązania to: własny, serwerowy OCR (bez zależności od zewnętrznej chmury rozpoznawania), odporny potok przetwarzania z mechanizmami zapasowymi, solidne uwierzytelnianie (bcrypt, JWT w ciasteczku HttpOnly, ochrona CSRF) oraz dyscyplina inżynierska (42 testy, potok CI, typowanie ścisłe).

Zespół identyfikuje również słabe strony i dług techniczny, a ich świadome nazwanie jest częścią rzetelnej oceny. W obszarze bezpieczeństwa: domyślny klucz podpisujący JWT jest zbyt krótki i wymaga ustawienia mocnego sekretu w środowisku produkcyjnym, ciasteczka nie mają domyślnie flagi `Secure` (wymaga HTTPS), brakuje też ograniczenia liczby prób logowania (brak ograniczania liczby prób) oraz limitu rozmiaru przesyłanych plików. W obszarze danych: brakuje narzędzia do wersjonowania migracji bazy (migracje nakładane są ręcznie), a model OCR nie jest zarządzany przez menedżer zależności. Testami nie objęto warstwy OCR ani frontendu.

Kierunki dalszego rozwoju wynikają zarówno z analizy technicznej, jak i z wyników ankiety:

- **Utwardzanie produkcyjne (hardening)** - wymuszenie mocnego sekretu JWT, włączenie HTTPS i flagi `Secure`, dodanie rate limitingu oraz walidacji rozmiaru i typu przesyłanych plików.
- **Narzędzie do migracji bazy** (np. Alembic) - zastąpienie ręcznego nakładania plików SQL.
- **Systematyczna ewaluacja jakości rozpoznawania** - zebranie większego zbioru paragonów z różnych sieci handlowych i pomiar skuteczności rozpoznawania, co pozwoli dalej dostrajać model i prompty.
- **Komunikat produktowy "zero wysiłku"** - wniosek wprost z obalenia hipotezy H3: aplikacja powinna podkreślać minimalizację wysiłku, a nie tylko automatyzację.
- **Aplikacja mobilna** - naturalne miejsce do robienia zdjęć paragonów to telefon; obecny frontend webowy jest responsywny, ale dedykowana aplikacja obniżyłaby barierę użycia.
- **Poszerzenie badania** - powtórzenie ankiety na większej i bardziej zróżnicowanej demograficznie próbie, aby zweryfikować wnioski poza grupą studentów.

## ZAŁĄCZNIKI

- Repozytorium kodu źródłowego: https://github.com/MattyMroz/SpendScan
- Pełne wyniki ankiety walidacyjnej: `doc/end/raport-dokumentacja/ankieta.md`
- Dane surowe ankiety: `doc/end/raport-dokumentacja/spend-scan.csv`
- Demonstracja działania aplikacji: [link do nagrania / prezentacji - do uzupełnienia]

## PODZIĘKOWANIA

Pragniemy wyrazić wdzięczność opiekun projektu, dr hab. inż. Ewie Korzeniewskiej, prof. PŁ, za możliwość realizacji projektu, poświęcony czas, cenne wskazówki oraz wsparcie merytoryczne na każdym etapie pracy. [Do rozszerzenia o ewentualne dalsze podziękowania.]

## BIBLIOGRAFIA

> Uwaga: przed oddaniem należy zweryfikować i uzupełnić daty dostępu do źródeł internetowych. Warto rozważyć dodanie publikacji naukowych dotyczących rozpoznawania tekstu z dokumentów (OCR) oraz modeli wizyjno-językowych, aby wzmocnić część naukową.

Cui, C., i in. (2024). PaddleOCR-VL: Boosting Multilingual Document Parsing via a 0.9B Vision-Language Model. Baidu / PaddlePaddle. https://github.com/PaddlePaddle/PaddleOCR

Gerganov, G., i in. (2023). llama.cpp: LLM inference in C/C++. https://github.com/ggml-org/llama.cpp

Google. (2024). Gemini API documentation. https://ai.google.dev/

Pydantic. (2024). Pydantic v2 documentation. https://docs.pydantic.dev/

Ramírez, S. (2024). FastAPI documentation. https://fastapi.tiangolo.com/

Ramírez, S. (2024). SQLModel documentation. https://sqlmodel.tiangolo.com/

PostgreSQL Global Development Group. (2025). PostgreSQL 18 documentation. https://www.postgresql.org/docs/18/

Jones, M., Bradley, J., i Sakimura, N. (2015). JSON Web Token (JWT) (RFC 7519). Internet Engineering Task Force. https://datatracker.ietf.org/doc/html/rfc7519

Provos, N., i Mazières, D. (1999). A future-adaptable password scheme. W: Proceedings of the USENIX Annual Technical Conference.

Astral. (2024). uv: An extremely fast Python package and project manager. https://docs.astral.sh/uv/

Chart.js. (2024). Chart.js documentation. https://www.chartjs.org/docs/latest/

## WKŁAD W PRACĘ NAD PROJEKTEM

Podział ról ustalono na podstawie historii repozytorium (gałęzie i treść commitów), a dane osobowe z karty opisowej projektu. Zdjęcia o wymiarach 3,26 cm na 2,56 cm należy dodać przy każdej osobie.

**Mateusz Mróz** (nr albumu 251190, specjalizacja: Eksploracja, Analiza i Bazy Danych), student 6. semestru kierunku Informatyka, pełnił rolę lidera technicznego projektu, odpowiadając za kluczowe elementy systemu. Odpowiadał za najtrudniejszą technicznie część systemu, czyli potok rozpoznawania paragonów: integrację modelu PaddleOCR-VL z serwerem llama.cpp, mechanizm wczytywania modelu i obsługę błędów pamięci GPU. Zaprojektował i wdrożył przepływ przetwarzania OCR do modelu językowego, a następnie do bazy danych, oraz zintegrował model językowy Gemini z łańcuchem zapasowych modeli i kluczy. Wykonał także napisaną od podstaw warstwę frontendu (klient API, montowanie plików statycznych) i warstwę uwierzytelniania (JWT, repozytorium użytkowników). Dbał o spójność całości rozwiązania, jakość kodu i porządkowanie repozytorium po zakończonych etapach.

**Igor Typiński** (nr albumu 251237, specjalizacja: Inżynieria Oprogramowania), student 6. semestru kierunku Informatyka. Odpowiadał za bezpieczeństwo warstwy uwierzytelniania, przenosząc przechowywanie tokenu sesji do ciasteczek HttpOnly wraz z ochroną przed atakami CSRF, co istotnie podniosło poziom zabezpieczeń aplikacji. Zaimplementował przechowywanie obrazów paragonów bezpośrednio w bazie danych oraz zajmował się konfiguracją API i frontendu. Wprowadził pełną wersję językową interfejsu w języku polskim, opcjonalną widoczność wykresów na pulpicie oraz uzupełnił komentarze w kodzie. Dbał o jakość kodu, regularnie poprawiając formatowanie i błędy zgłaszane przez linter.

**Mateusz Słoń** (nr albumu 251221, specjalizacja: Technologie Internetowe), student 6. semestru kierunku Informatyka. Odpowiadał za moduł kalendarza i organizacji paragonów, w tym grupowanie zakupów w foldery oraz zarządzanie nimi. Zaprojektował i wdrożył tryb ciemny interfejsu, dbając o spójność wizualną obu motywów. Wniósł istotny wkład w jakość kodu backendu, naprawiając konwersje typów dziesiętnych, porządkując importy repozytoriów i usuwając ostrzeżenia narzędzi kontroli jakości (linter, sprawdzanie typów). Zajmował się również zagadnieniami dostępności i czytelności interfejsu.

**Jakub Bryła** (nr albumu 251130, specjalizacja: Eksploracja, Analiza i Bazy Danych), student 6. semestru kierunku Informatyka. Odpowiadał za logikę pulpitu analitycznego, czyli serce warstwy prezentacji wyników. Zaprojektował elastyczny mechanizm agregacji wydatków z obsługą wielu okresów (dziennego, tygodniowego, miesięcznego, rocznego), trendów procentowych względem poprzedniego okresu oraz podziału dziennego. Rozszerzył pulpit o obsługę budżetów i subskrypcji wraz z walidacją danych. Skonfigurował także potok ciągłej integracji (CI) i wprowadził bezpieczne zarządzanie sekretem JWT przez zmienne środowiskowe zamiast wartości zapisanej na stałe w kodzie.

**Piotr Marczak** (nr albumu 251184, specjalizacja: Eksploracja, Analiza i Bazy Danych), student 6. semestru kierunku Informatyka. Odpowiadał za fundament warstwy danych aplikacji. Zaprojektował modele danych w technologii SQLModel odwzorowujące cały schemat bazy (paragony, pozycje, obrazy, kategorie, foldery), nawiązał połączenie aplikacji z bazą PostgreSQL oraz przygotował migracje schematu paragonów. Jego praca stworzyła stabilną podstawę, na której budowane były kolejne warstwy systemu (repozytoria, potok przetwarzania, analityka).

**dr hab. inż. Ewa Korzeniewska, prof. PŁ** (Instytut Systemów Inżynierii Elektrycznej I26), opiekun projektu. Odpowiadała za koordynację działań zespołu oraz wsparcie merytoryczne na wszystkich etapach realizacji projektu, od analizy problemu i ankiety walidacyjnej, przez projekt architektury, po fazę implementacji i testów.
