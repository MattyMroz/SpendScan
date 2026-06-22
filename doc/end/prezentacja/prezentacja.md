# SpendScan — konkretna rozpiska do slajdów

> Wersja: 15 slajdów
> Limit: 12 minut + 8 minut pytań
> Cel: gotowa baza do wklejenia do PowerPointa lub Canvy

## Jak z tego korzystać

Przy każdym slajdzie masz:

- gotowy nagłówek,
- konkretne rzeczy do wpisania na slajd,
- krótką wersję tego, co powiedzieć ustnie.

## Slajd 1 — Tytuł

**Nagłówek na slajdzie:**

SpendScan

**Podtytuł na slajdzie:**

Zespół nr 8 — aplikacja analizująca wydatki na podstawie zdjęć paragonów

**Wstaw na slajd:**

- Politechnika Łódzka, WEEIA
- Opiekun: dr hab. inż. Ewa Korzeniewska, prof. PŁ
- Jednostka: Instytut Systemów Inżynierii Elektrycznej I26
- Zespół: Piotr Marczak, Jakub Bryła, Mateusz Mróz, Igor Typiński, Mateusz Słoń

**Powiedz:**

Jesteśmy Zespołem nr 8 i rozwijamy aplikację SpendScan. Naszym celem jest uproszczenie analizy codziennych wydatków na podstawie zdjęć paragonów.

## Slajd 2 — Jaki problem rozwiązujemy

**Nagłówek na slajdzie:**

Problem użytkownika

**Wstaw na slajd:**

- wiele osób nie wie dokładnie, ile wydaje na jedzenie, chemię i codzienne zakupy
- obecne metody kontroli wydatków są ręczne, czasochłonne i niewygodne
- paragony zawierają dane, ale zwykle kończą w koszu bez żadnej analizy

**Powiedz:**

Problem nie polega na samym braku aplikacji finansowych, tylko na tym, że analiza codziennych zakupów dalej wymaga ręcznej pracy. Chcemy zautomatyzować ten etap.

## Slajd 3 — Dla kogo to jest i jaka jest wartość

**Nagłówek na slajdzie:**

Użytkownik i wartość

**Wstaw na slajd:**

- główny użytkownik: student lub młoda osoba samodzielnie robiąca zakupy
- potrzeba: szybki zapis wydatków bez ręcznego wpisywania produktów
- wartość: oszczędność czasu, większa kontrola budżetu, czytelna historia zakupów

**Powiedz:**

Nie budujemy systemu dla księgowości ani dużej firmy. Budujemy narzędzie dla zwykłego użytkownika, który chce lepiej rozumieć swoje wydatki bez dodatkowej pracy.

## Slajd 4 — Co już istnieje na rynku

**Nagłówek na slajdzie:**

Alternatywne rozwiązania

**Wstaw na slajd:**

- Excel, kartka, notatki w telefonie
- aplikacje budżetowe wymagające ręcznego wpisywania
- analiza historii konta bankowego bez szczegółu z paragonu

**Dopisz małym tekstem pod spodem:**

Brak prostego połączenia: zdjęcie paragonu -> odczyt danych -> analiza wydatków.

**Powiedz:**

Alternatywy istnieją, ale zwykle albo są ręczne, albo nie pokazują szczegółów z paragonu, takich jak konkretne produkty, sklep czy promocje.

## Slajd 5 — Walidacja problemu ankietą 📊

**Nagłówek na slajdzie:**

Wyniki ankiety pre

**Wstaw na slajd:**

- [wstaw wasz wynik]% osób nie zna dokładnie wydatków w kategoriach
- [wstaw wasz wynik]% osób wskazało ręczne wpisywanie jako główny problem
- [wstaw wasz wynik]% osób uznało, że taka aplikacja byłaby przydatna

**Wniosek na dole slajdu:**

Problem jest realny, a potrzeba automatyzacji została potwierdzona ankietą.

**Powiedz:**

Tutaj pokazujemy dane, a nie opinię. Wybierzcie tylko trzy najmocniejsze wyniki, które najlepiej bronią sensu projektu.

## Slajd 6 — Na czym polega nasze rozwiązanie

**Nagłówek na slajdzie:**

Proponowane rozwiązanie

**Wstaw na slajd jako prosty flow:**

- użytkownik robi zdjęcie paragonu
- OCR odczytuje tekst i pozycje
- system wykrywa sklep, produkty i ceny
- wydatki trafiają do kategorii i analizy miesięcznej

**Powiedz:**

Chcemy, żeby droga od paragonu do analizy była możliwie krótka. Użytkownik nie ma przepisywać danych, tylko dostać gotowy obraz swoich zakupów.

## Slajd 7 — Co dokładnie ma robić aplikacja

**Nagłówek na slajdzie:**

Najważniejsze funkcje

**Wstaw na slajd:**

- grupowanie wydatków po kategoriach, np. żywność, chemia, elektronika
- rozpoznanie sklepu z paragonu i przypisanie zakupu do miejsca
- wykrywanie promocji, przecen i sumowanie oszczędności
- oznaczanie poziomu wydatków: zielony, żółty, czerwony

**Powiedz:**

Te funkcje nie są przypadkowe. Wynikają z realnej wartości dla użytkownika: chce wiedzieć gdzie wydaje, na co wydaje i czy przekracza bezpieczny poziom budżetu.

## Slajd 8 — Tech stack

**Nagłówek na slajdzie:**

Tech stack i uzasadnienie wyboru

**Wstaw na slajd:**

- backend: Python 3.13 + FastAPI
- baza danych: SQLite w środowisku developerskim
- jakość kodu: uv, ruff, mypy, pytest, GitHub Actions
- OCR: osobny pipeline do odczytu danych z paragonu

**Dopisz małym tekstem na dole:**

Plusy: szybki development i dobry ekosystem pod OCR. Minusy: trudna integracja OCR i większa złożoność walidacji danych.

**Powiedz:**

Wybraliśmy stack, który pozwala szybko rozwijać backend, testować rozwiązania i dobrze współpracuje z częścią OCR.

## Slajd 9 — Architektura systemu

**Nagłówek na slajdzie:**

Schemat blokowy działania

**Wstaw na slajd jako bloki:**

- użytkownik
- moduł dodawania paragonu
- OCR i ekstrakcja tekstu
- parser i kategoryzacja danych
- baza danych
- dashboard i analityka wydatków

**Powiedz:**

Ten slajd ma pokazać przepływ danych, a nie kod. Najważniejsze jest to, jak informacja przechodzi od zdjęcia do końcowej analizy dla użytkownika.

## Slajd 10 — Value vs effort

**Nagłówek na slajdzie:**

Priorytety funkcji: value vs effort

**Wstaw na slajd jako macierz:**

- wysokie value / niższy effort: kategorie wydatków, historia zakupów, sklep z paragonu
- wysokie value / wysoki effort: pełna integracja OCR, wykrywanie promocji, automatyczny parser pozycji
- średnie value / niższy effort: status zielony-żółty-czerwony, proste alerty budżetowe

**Dopisz małym tekstem na dole:**

Value = potrzeba użytkownika i wyniki ankiety. Effort = czas, trudność techniczna i złożoność wdrożenia.

**Powiedz:**

To pokazuje, że planujemy projekt świadomie. Najpierw funkcje dające największą wartość, a dopiero później te najbardziej kosztowne technicznie.

## Slajd 11 — Harmonogram

**Nagłówek na slajdzie:**

Plan realizacji i kamienie milowe

**Wstaw na slajd:**

- analiza problemu i ankieta
- analiza wymagań i zakres projektu
- projekt interfejsu i makieta
- architektura systemu i model bazy danych
- implementacja backendu i dodawania paragonów
- integracja OCR, analityka, testy i feedback

**Powiedz:**

Tu pokażcie Gantta, ale w uproszczonej formie. Najważniejsze mają być etapy, kamienie milowe i miejsce, w którym jesteście teraz.

## Slajd 12 — Aktualny stan projektu

**Nagłówek na slajdzie:**

Gdzie jesteśmy teraz

**Wstaw na slajd:**

- analiza i projekt: 100%
- analiza wymagań i zakres projektu: 100%
- projekt interfejsu i koncepcji działania aplikacji: 100%
- projekt architektury i system bazy danych: 100%
- implementacja kluczowych funkcji: 50%
- dodawanie paragonów: 25%
- integracja OCR i odczyt z paragonu: 5%

**Dopisz na dole:**

OCR działa lokalnie, ale nie jest jeszcze zintegrowany z pełnym przepływem aplikacji.

**Powiedz:**

Pokazujemy realny postęp, nie wersję idealną. To ważne, bo panel ma zobaczyć, że znamy stan projektu i wiemy, co jeszcze zostało do zrobienia.

## Slajd 13 — Wpływ na środowisko i dostępność ♻️

**Nagłówek na slajdzie:**

Wpływ na środowisko, normalizacja i WCAG

**Wstaw na slajd:**

- aplikacja może wspierać bardziej świadome zakupy i ograniczanie niepotrzebnych wydatków
- lepsza analiza zakupów może pośrednio ograniczać marnowanie żywności
- interfejs powinien być czytelny, prosty i zgodny z podstawami WCAG

**Dopisz małym tekstem na dole:**

Koszt środowiskowy OCR istnieje, ale chcemy go równoważyć realną wartością użytkową i prostotą rozwiązania.

**Powiedz:**

Nie twierdzimy, że sama aplikacja rozwiązuje problem ekologii. Pokazujemy raczej, że może wspierać bardziej świadome decyzje zakupowe i jednocześnie być dostępna dla użytkownika.

## Slajd 14 — Problemy i obejścia 🚧

**Nagłówek na slajdzie:**

Problemy w realizacji projektu

**Wstaw na slajd:**

- różne formaty i jakość paragonów utrudniają odczyt danych
- OCR działa, ale pełna integracja z aplikacją jest jeszcze przed nami
- część końcowych funkcji została tymczasowo zastąpiona makietą i planem wdrożenia

**Dopisz pod spodem:**

Obejścia: etapowanie MVP, modularna architektura, testy lokalne OCR, makieta dla funkcji jeszcze niewdrożonych.

**Powiedz:**

Ten slajd ma pokazać dojrzałość projektu. Nie tylko co zrobiliście, ale też jakie były przeszkody i jak sobie z nimi poradziliście.

## Slajd 15 — Co dalej

**Nagłówek na slajdzie:**

Dalsze kroki i prezentacja końcowa

**Wstaw na slajd:**

- dokończenie integracji OCR z aplikacją
- rozwój analityki wydatków i historii zakupów
- testy, feedback i dopracowanie działania aplikacji
- na prezentację końcową: film z działania, ankieta satysfakcji i test użyteczności

**Powiedz:**

Na finał chcemy pokazać nie tylko samą aplikację, ale też dowód, że działa i że jest użyteczna dla użytkownika.

## Jeśli będzie za dużo, skróć do 12 slajdów

Scal:

- slajd 2 i 3,
- slajd 8 i 9,
- slajd 14 i 15.

## Przed robieniem finalnych slajdów przygotuj

- 3 najmocniejsze liczby z ankiety,
- wykres Gantta w czytelnej wersji,
- macierz value vs effort,
- prosty schemat blokowy,
- 2-3 ekrany makiety.

































# SpendScan — plan prezentacji śródokresowej

> 15 slajdów · 12 minut · Zespół nr 8

---

## Slajd 1 — Zdjęcie paragonu zamiast godzin w Excelu

- **SpendScan** — aplikacja analizująca wydatki na podstawie zdjęć paragonów
- Zespół nr 8: Piotr Marczak, Jakub Bryła, Mateusz Mróz, Igor Typiński, Mateusz Słoń
- Opiekun: dr hab. inż. Ewa Korzeniewska, prof. PŁ · I26
- Politechnika Łódzka, WEEIA · Projekt kompetencyjny [02 96 6174 01] · Semestr VI

---

## Slajd 2 — Brak prostego sposobu na automatyczną analizę codziennych wydatków

- brak kontroli nad wydatkami
- ręczne wpisywanie to strata czasu
- paragony trafiają do kosza
- brak automatycznej analizy

Nie istnieje proste narzędzie, które automatycznie zamienia paragon w gotową analizę wydatków.

Czyli przepaść między:
- **potrzebą** (kontrola wydatków)
- **brakiem rozwiązania** (ręczne wpisywanie)
- **brakiem motywacji** (za dużo wysiłku)

---

## Slajd 3 — Dla kogo i co zyskuje

- **kto:** student lub młoda osoba samodzielnie robiąca zakupy
- **potrzeba:** szybki zapis wydatków bez przepisywania
- **zysk:** kontrola budżetu, historia zakupów, oszczędność czasu

---

## Slajd 4 — Każdy coś już ma, ale to nie działa

- Excel i kartka — ręczna robota
- aplikacje finansowe — wymagają ręcznego wpisywania każdej pozycji
- historia konta — brak szczegółów z paragonu, sklepu i kategorii

> Nikt nie łączy: zdjęcie → odczyt danych → analiza. My tak robimy.

---

## Slajd 5 — Liczby z ankiety mówią same za siebie 📊

- **[X]%** osób nie zna swoich wydatków w kategoriach
- **[X]%** wskazało ręczne wpisywanie jako główną barierę
- **[X]%** chciałoby korzystać z takiej aplikacji

> Problem potwierdzony danymi, nie opinią.

---

## Slajd 6 — Od zdjęcia do analizy w jednym kroku

1. zdjęcie paragonu
2. OCR odczytuje tekst i pozycje
3. system wykrywa sklep, produkty i ceny
4. wydatki trafiają do kategorii i analizy miesięcznej

---

## Slajd 7 — Co konkretnie robi aplikacja

- grupowanie wydatków: żywność, chemia, elektronika i inne
- rozpoznanie sklepu z paragonu (Biedronka, Lidl, Dino…)
- sumowanie promocji i wykrytych upustów
- status wydatku: 🟢 zielony / 🟡 żółty / 🔴 czerwony

---

## Slajd 8 — Tech stack i dlaczego akurat ten

| Warstwa | Technologia |
|---------|-------------|
| Backend | Python 3.13 + FastAPI |
| Baza danych | SQLite (dev) |
| Jakość kodu | uv, ruff, mypy, pytest, GitHub Actions |
| OCR | osobny pipeline |

- ✅ szybki development, dobry ekosystem pod OCR
- ❌ trudna integracja OCR, złożona walidacja danych wejściowych

---

## Slajd 9 — Jak to działa w środku

```
Użytkownik
  → moduł dodawania paragonu
  → OCR i ekstrakcja tekstu
  → parser i kategoryzacja danych
  → baza danych
  → dashboard i analityka wydatków
```

> Schemat blokowy — od zdjęcia do analizy.

---

## Slajd 10 — Co robimy najpierw, a co później

| Priorytet | Funkcje |
|-----------|---------|
| 🔴 wysoka wartość / niski effort | kategorie, historia, sklep z paragonu |
| 🟡 wysoka wartość / wysoki effort | pełna integracja OCR, wykrywanie promocji, parser pozycji |
| 🟢 średnia wartość / niski effort | status zielony-żółty-czerwony, alerty budżetowe |

> Value = potrzeba z ankiety. Effort = czas + złożoność techniczna.

---

## Slajd 11 — Plan pracy (Gantt)

- analiza problemu i ankieta
- analiza wymagań i zakres projektu
- projekt interfejsu i makieta
- architektura systemu i model bazy danych
- implementacja kluczowych funkcji
- integracja OCR, analityka, testy i feedback

> ← wstawić wykres Gantta →

---

## Slajd 12 — Gdzie jesteśmy teraz

| Etap | Postęp |
|------|--------|
| Analiza i projekt | 100% |
| Analiza wymagań | 100% |
| Projekt interfejsu i koncepcja | 100% |
| Architektura i baza danych | 100% |
| Implementacja kluczowych funkcji | 50% |
| Dodawanie paragonów | 25% |
| Integracja OCR | 5% |

> OCR działa lokalnie — nie jest jeszcze zintegrowany z aplikacją.

---

## Slajd 13 — Aplikacja, która uczy świadomiej kupować ♻️

- lepsza kontrola wydatków → mniej impulsywnych i niepotrzebnych zakupów
- analiza zakupów spożywczych → potencjalne ograniczenie marnowania żywności
- interfejs zgodny z WCAG — czytelny, prosty, dostępny

> Koszt OCR istnieje. Równoważymy go realną wartością dla użytkownika.

---

## Slajd 14 — Co nas zatrzymało i jak to obeszliśmy 🚧

- różne formaty paragonów → modularne parsery per sklep
- trudna walidacja danych OCR → testy lokalne przed integracją
- ograniczony czas (53 h/miesiąc) → etapowanie MVP, makieta zamiast niewdrożonych funkcji

---

## Slajd 15 — Co zostało i co pokażemy na finale

**Zostało:**
- pełna integracja OCR
- analityka wydatków i historia zakupów
- testy i dopracowanie UX

**Na prezentację końcową:**
- film z działania aplikacji
- ankieta satysfakcji użytkowników
- test użyteczności i dostępności

---

## Opcja: skróć do 12 slajdów

Scal: 2+3 · 8+9 · 14+15

---
---
---

# 🚀 v3 — wersja minimalistyczna (bez lania wody)

> 15 slajdów · 12 minut · Zespół nr 8
> Każdy slajd: 1 nagłówek + 3-5 haseł. Reszta idzie ustnie.

---

## 1 — SpendScan

Aplikacja analizująca wydatki na podstawie zdjęć paragonów

- Zespół nr 8 · WEEIA PŁ · Semestr VI
- Marczak · Bryła · Mróz · Typiński · Słoń
- Opiekun: dr hab. inż. Ewa Korzeniewska, prof. PŁ · I26

---

## 2 — Problem

Brak prostego sposobu na automatyczną analizę codziennych wydatków

- brak kontroli nad wydatkami
- ręczne wpisywanie to strata czasu
- paragony trafiają do kosza
- brak automatycznej analizy

---

## 3 — Użytkownik

Każdy, kto ma smartfon, paragony i chce kontroli wydatków

- nie zna dokładnie swoich wydatków
- ma telefon zawsze przy sobie
- nie ma czasu na ręczne wpisywanie
- chce wiedzieć na co wydaje, nie tylko ile

---

## 4 — Konkurencja

Każdy coś używa, ale nic nie działa dobrze

- Excel i kartka — ręcznie
- aplikacje budżetowe — ręcznie
- historia konta — brak szczegółu z paragonu

---

## 5 — Walidacja ankietą 📊

Problem potwierdzony danymi (55 odpowiedzi)

- **78%** nie zna swoich wydatków w kategoriach
- **93%** nie używa żadnej aplikacji do wydatków
- **64%** trzyma paragon choć przez chwilę

---

## 6 — Rozwiązanie

Od zdjęcia do analizy w czterech krokach

1. zdjęcie paragonu
2. OCR czyta tekst
3. system wykrywa sklep i produkty
4. analiza w kategoriach

---

## 7 — Funkcje

Co aplikacja będzie robić

- kategorie: żywność, chemia, elektronika
- rozpoznanie sklepu (Biedronka, Lidl, Dino)
- wykrywanie promocji i upustów
- status budżetu: 🟢 / 🟡 / 🔴

---

## 8 — Tech stack

Stack pod szybki development z OCR

| Warstwa | Tech |
|---------|------|
| Backend | Python 3.13 + FastAPI |
| Baza | SQLite (dev) |
| Quality | uv · ruff · mypy · pytest · GH Actions |
| OCR | osobny pipeline |

---

## 9 — Architektura

Schemat blokowy działania

```
zdjęcie → OCR → parser → DB → dashboard
```

- modularne parsery per sklep
- pipeline OCR osobno od backendu

---

## 10 — Priorytety

Value vs effort

| | Funkcje |
|---|---|
| 🔴 high value / low effort | kategorie · historia · sklep |
| 🟡 high value / high effort | OCR · promocje · parser |
| 🟢 mid value / low effort | status 🟢🟡🔴 · alerty |

---

## 11 — Harmonogram

Plan realizacji w czasie

- analiza + ankieta ✅
- wymagania + zakres ✅
- UI + makieta ✅
- architektura + DB ✅
- backend + paragony ⏳
- OCR + testy ⏳

> ← wykres Gantta →

---

## 12 — Stan projektu

Gdzie jesteśmy teraz

| Etap | % |
|------|---|
| Analiza, wymagania, UI, architektura | 100 |
| Implementacja funkcji | 50 |
| Dodawanie paragonów | 25 |
| Integracja OCR | 5 |

> OCR działa lokalnie, nie jest jeszcze podpięty.

---

## 13 — Wpływ ♻️

Świadome zakupy i dostępność

- mniej impulsywnych wydatków
- mniej marnowania żywności
- interfejs zgodny z WCAG

---

## 14 — Przeszkody 🚧

Co nas zatrzymało i jak to obeszliśmy

- różne formaty paragonów → modularne parsery
- walidacja OCR → testy lokalne
- 53 h/miesiąc → etapowanie MVP

---

## 15 — Co dalej

Następne kroki i prezentacja końcowa

**Zostało:**
- integracja OCR
- analityka + historia
- testy + UX

**Na finał:**
- 🎬 film z działania
- 📊 ankieta satysfakcji
- 🧪 test użyteczności

---

## Skrót do 12 slajdów

Scal: 2+3 · 8+9 · 14+15
