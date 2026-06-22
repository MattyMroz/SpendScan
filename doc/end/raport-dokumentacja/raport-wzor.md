# Karty maturalne
Adam Bijacik, Wiktor Ciszewski, Michał Dąbkowski, Joram Mumb Mulaj Kambaj, Prof. Ewa Korzeniewska
Politechnika Łódzka, WEEIA, Informatyka, Łódź, Polska

## STRESZCZENIE

Celem projektu "Karty maturalne" było stworzenie przyjaznej aplikacji mobilnej, która pomoże uczniom szkół średnich w przygotowaniach do egzaminu maturalnego. Aplikacja gromadzi wszystkie niezbędne materiały i tablice maturalne w jednym miejscu, eliminując problemy związane z dostępnością i przestarzałymi rozwiązaniami. Oferuje ona materiały do nauki z matematyki, fizyki, chemii i angielskiego, podzielone na sekcje dla łatwej nawigacji. Zawiera również pomocnicze materiały przygotowane przez nauczycieli. Aplikacja umożliwia działanie w pełni offline zarówno na platformie Android jak i IOS. Analizując dostępne rozwiązania, zdecydowaliśmy, że nasza aplikacja będzie bardziej nowoczesna, atrakcyjna i użyteczna. Implementacja innowacyjnych funkcji, takich jak Pomocnik, kompatybilność z różnymi platformami, funkcjonalność offline i intuicyjny design, wyróżnia nasz projekt. Zapewniliśmy również zgodność z WCAG, aby aplikacja była dostępna dla wszystkich uczniów, w tym osób z niepełnosprawnościami.
## KEYWORDS

Karty maturalne, aplikacja mobilna, przygotowanie do matury, treści edukacyjne, tablice maturalne, offline, React Native, WCAG, zarządzanie projektem, iOS, Android, materiały pomocnicze.

## I. WSTĘP
### A. Obszar / tło działań
Matura to egzamin dojrzałości, który absolwenci szkół średnich muszą zdać, aby uzyskać świadectwo dojrzałości i móc kontynuować naukę na studiach wyższych. Egzamin ten składa się z części obowiązkowej oraz dodatkowej. Wśród przedmiotów obowiązkowych znajdują się matematyka, język polski oraz język obcy nowożytny, najczęściej angielski. Matematyka jako obowiązkowy przedmiot od 2010 roku, budzi wiele kontrowersji ze względu na swój stopień trudności, jednak jest istotna dla rozwijania umiejętności logicznego myślenia i analizy. Poza przedmiotami obowiązkowymi, uczniowie mogą wybierać spośród szerokiej gamy przedmiotów dodatkowych, takich jak fizyka, chemia, biologia, geografia, historia i inne. W 2020 roku najczęściej wybieranymi przedmiotami dodatkowymi były język angielski, matematyka na poziomie rozszerzonym, fizyka oraz chemia. Niestety, badania wskazują, że przyswojenie tych przedmiotów jest wyzwaniem dla wielu uczniów. Często wiąże się to z brakiem odpowiedniego przygotowania na wcześniejszych etapach edukacji oraz z trudnością w zrozumieniu abstrakcyjnych pojęć. Według badań przeprowadzonych przez Fundację Edukacyjną Perspektywy, około 35% uczniów ma problemy z opanowaniem materiału z matematyki na poziomie maturalnym. Badania przeprowadzone przez Scotta (2012) wskazują, że uczniowie mają trudności z wykonywaniem obliczeń w chemii, co często jest związane z ich problemami w matematyce (Scott, 2012). Hoban, Finlayson i Nolan (2013) zauważają, że transfer umiejętności matematycznych do chemii jest wyzwaniem dla uczniów, co dodatkowo komplikuje przyswajanie tych przedmiotów (Hoban, Finlayson, & Nolan, 2013). Ponadto, Bahar i Polat (2007) stwierdzili, że uczniowie postrzegają tematy z nauk ścisłych jako trudniejsze niż humanistyczne, co wskazuje na ogólną tendencję do większych problemów z przedmiotami ścisłymi. Badania te wykazały, że uczniowie często mają problemy z abstrakcyjnymi pojęciami i złożonymi procedurami charakterystycznymi dla przedmiotów ścisłych, co w połączeniu z brakiem solidnych podstaw matematycznych, utrudnia im skuteczne przyswajanie wiedzy z chemii, fizyki czy matematyki. W przeciwieństwie do tego, przedmioty humanistyczne są postrzegane jako bardziej przystępne i zrozumiałe, co może wynikać z ich bardziej narracyjnego i kontekstowego charakteru (Bahar & Polat, 2007). Wszystkie te badania pokazują, że uczniownie mają problemy ze zrozumieniem przedmiotów ścisłych, co później przekłada się na wyniki na egzaminach. W 2023 roku, zdawalność matury z matematyki wyniosła około 79%, podczas gdy zdawalność języka angielskiego, najczęściej wybieranego języka obcego, wyniosła około 92%. Zatem kluczowym elementem jest dobre przygotowanie do matury. Wymaga ono dostępu do odpowiednich materiałów edukacyjnych, które obecnie są często niekompletne i przestarzałe. Strona Centralnej Komisji Egzaminacyjnej (CKE) jest trudna w nawigacji i wymaga stałego dostępu do Internetu, co może być problematyczne dla uczniów z ograniczonym dostępem do sieci. Współczesne metody wsparcia uczniów pod względem informatycznym obejmują szereg narzędzi i platform edukacyjnych. Programy takie jak Khan Academy, platformy MOOC (Massive Open Online Courses) oraz liczne aplikacje mobilne oferują interaktywne lekcje, ćwiczenia i testy, które pomagają uczniom lepiej zrozumieć materiał. Jednak wiele z tych zasobów również wymaga stałego dostępu do Internetu. Nasza aplikacja ma na celu rozwiązanie tych problemów poprzez zebranie wszystkich potrzebnych materiałów w jednym miejscu i zapewnienie dodatkowych narzędzi wspomagających naukę.
### B. Cel Projektu
Celem projektu jest stworzenie przyjaznej aplikacji mobilnej wspierającej uczniów w przygotowaniach do matury. Aplikacja dostarcza materiały z matematyki, fizyki, chemii i angielskiego, podzielone na sekcje dla łatwej nawigacji, oraz pomocnicze materiały przygotowane przez nauczycieli. Działa bez stałego dostępu do Internetu, umożliwiając korzystanie w dowolnym miejscu i czasie.
## II. STAN WIEDZY
### A. Konstruktywna analiza istniejących rozwiązań
Obecne aplikacje edukacyjne często są niekompletne i przestarzałe. Jedyna mobilna aplikacja oparta na oficjalnych dokumentach państwowych została stworzona przez studentów SGGW w 2012 roku, ale jest obecnie niedostępna i nieaktualizowana. Poza tym rozwiązaniem znajduje się jeszcze kilka aplikacji umożliwiających naukę i zdawanie quizów, lecz nie zawierają one oficjalnych oraz pomocniczych materiałów. Zatem na rynku nie ma odpowiedników naszej aplikacji, która łączyłaby wiele przedmiotów maturalnych w jednym miejscu, oferując nowoczesny design oraz funkcję pomocnika z przykładowymi rozwiązaniami.
### B. Uzasadnienie i formy rozwiązania
W ramach naszego projektu poszukiwaliśmy najlepszego rozwiązania technologicznego, które spełniłoby następujące wymagania dla naszej aplikacji mobilnej:
- działać na dwóch głównych platformach mobilnych: iOS i Android
- umożliwiać jak największe dzielenie kodu między platformami
- być aktywnie rozwijana i mieć dobre wsparcie techniczne
- zapewniać wysoką wydajność, nawet na słabszych urządzeniach
- mieć dobrą integrację z natywnymi interfejsami API urządzeń
Podczas wyboru technologii do stworzenia naszej aplikacji mobilnej analizowaliśmy kilka popularnych rozwiązań, takich jak Ionic, React Native i Flutter. Każde z tych narzędzi ma swoje mocne i słabe strony.
Ionic to framework, który wykorzystuje HTML i JavaScript do tworzenia aplikacji, które działają w przeglądarkach mobilnych. Choć może oferować wystarczającą wydajność, ma ograniczenia w zakresie zaawansowanych funkcji i jego popularność maleje, dlatego zdecydowaliśmy się nie brać go pod uwagę.
Flutter to nowoczesne narzędzie od Google, które zyskało popularność dzięki swoim innowacyjnym funkcjom. Mimo że jest to bardzo obiecująca technologia, uznaliśmy, że React Native lepiej spełnia nasze potrzeby.
React Native to framework, który pozwala tworzyć aplikacje na iOS i Androida przy użyciu jednej bazy kodu. Jego popularność wśród dużych firm, dobre wsparcie oraz to, że cały zespół jest już zaznajomiony z tą technologią, sprawiły, że to właśnie React Native wybraliśmy do naszego projektu.
Dzięki React Native możemy pisać kod, który działa na obu głównych systemach operacyjnych, co ułatwia rozwój aplikacji. Dzięki swojemu ekosystemowi, React Native jest frameworkiem, który najlepiej odpowiada naszym wymaganiom, co czyni go idealnym wyborem do realizacji naszego projektu aplikacji maturalnej.

## III. OPIS ROZWIĄZANIA

### A. Opis techniczny rozwiązania
Podczas wyboru React Native opieraliśmy się na kilku kluczowych aspektach technicznych, które sprawiają, że jest to najbardziej odpowiednie rozwiązanie dla naszego projektu.
React Native zapewnia doskonałą integrację z natywnymi interfejsami API systemów iOS i Android, co jest możliwe dzięki jego unikalnej architekturze opartej na tzw. bridge architecture. W tej architekturze, kod JavaScript komunikuje się z natywnymi komponentami za pośrednictwem mostu (bridge), co pozwala na wykorzystanie natywnych funkcji z poziomu kodu aplikacji. To podejście nie tylko ułatwia integrację z zaawansowanymi możliwościami urządzeń mobilnych, ale także zapewnia szerokie wsparcie dla różnych funkcji, które są kluczowe dla rozwoju aplikacji.
Wydajność aplikacji stworzonych za pomocą React Native jest bardzo zadowalająca dzięki zastosowaniu Virtual DOM oraz natywnych komponentów UI. Virtual DOM optymalizuje proces renderowania interfejsu użytkownika poprzez minimalizowanie operacji na drzewie DOM i stosowanie efektywnych algorytmów porównawczych, co przyczynia się do wysokiej wydajności aplikacji. Dodatkowo, React Native wspiera Native Modules, co oznacza, że w przypadku potrzeby intensywnego przetwarzania lub skomplikowanych operacji, możliwe jest implementowanie natywnych komponentów w Objective-C/Swift (iOS) lub Java/Kotlin (Android) i ich integracja z aplikacją poprzez most, co pozwala na optymalizację działania aplikacji.
Jednym z głównych atutów React Native jest możliwość współdzielenia kodu między platformami iOS i Android. Dzięki komponentowej architekturze i wspólnej bazie kodu JavaScript, większość kodu może być używana na obu platformach. React Native wspiera także różne techniki zarządzania różnicami między platformami, takie jak Platform API oraz umożliwia używanie warunkowych plików kodu specyficznych dla iOS i Androida. To podejście znacząco upraszcza rozwój aplikacji, zmniejsza koszty i czas potrzebny na jej stworzenie oraz ułatwia późniejsze utrzymanie i aktualizację.
React Native jest aktywnie rozwijanym frameworkiem z silnym wsparciem społeczności oraz dużą bazą zasobów. Regularne aktualizacje dostarczane przez zespół Facebooka oraz ogromna społeczność deweloperów zapewniają dostęp do najnowszych funkcji, poprawek błędów i wsparcia dla najnowszych wersji systemów operacyjnych iOS i Android. Framework ten korzysta z wielu zewnętrznych bibliotek i narzędzi, takich jak Redux do zarządzania stanem aplikacji czy React Navigation do nawigacji, co dodatkowo wspiera rozwój aplikacji.
Kolejnym istotnym czynnikiem była znajomość TypeScript w naszym zespole. React Native wspiera TypeScript, co wprowadza zaawansowane funkcje takie jak statyczne typowanie i klasy, które pomagają w budowie skalowalnych aplikacji. Korzystanie z TypeScript pozwala na wcześniejsze wykrywanie błędów oraz poprawia strukturę i czytelność kodu, co prowadzi do bardziej niezawodnego rozwoju aplikacji.
Wreszcie, React Native dysponuje bogatym ekosystemem narzędzi i bibliotek wspierających cały cykl życia aplikacji, od projektowania, przez rozwój, aż po testowanie i wdrożenie. Narzędzia takie jak Expo ułatwiają rozwój i testowanie aplikacji, a React DevTools i Redux DevTools oferują zaawansowane możliwości debugowania. Dodatkowo, narzędzia do automatyzacji takich jak Fastlane i monitorowania błędów jak Sentry wspierają zarządzanie aplikacją na każdym etapie jej rozwoju.
Podsumowując, React Native okazał się idealnym wyborem dla naszego projektu dzięki swojej zdolności do efektywnej integracji z natywnymi API, wysokiej wydajności, możliwości współdzielenia kodu między platformami, wsparciu ze strony społeczności oraz znajomości TypeScript w naszym zespole. Dzięki tym cechom, React Native pozwala nam stworzyć aplikację, która jest nie tylko funkcjonalna i wydajna, ale także efektywna pod względem rozwoju i utrzymania.

### B. Zarządzanie projektem i pracą zespołową
Zarządzanie projektem obejmowało wykorzystanie narzędzi takich jak Trello do planowania zadań (rys. 1), oraz GitHub do współpracy nad kodem (rys. 2). Pracowaliśmy w metodyce Scrum. Do pogłębiania wiedzy o projekcie oraz synchronizacji wspólnej wizji używaliśmy Event Stormingu przy pomocy aplikacji webowej Miro (rys. 3). Sprinty planowane były przy użyciu procesu User Story Mapping. Tworzenie historyjek pozwalało na priorytetyzowanie funkcjonalności skupiając się na tych najważniejszych dla użytkownika. By usprawnić działanie naszego zespołu, wybraliśmy spośród nas jedną osobę, która została liderem naszego zespołu. Podzieliliśmy się również na role by każdy z nas mógł jak najlepiej wykorzystać swoje umiejętności. Do sprawniejszej i systematyczniejszej pracy wykorzystaliśmy wykres Gantta, by określić przedział czasowy każdego zadania (rys. 4). Podczas tworzenia naszej aplikacji szczególną uwagę poświęciliśmy zapewnieniu jej dostępności zgodnie z wytycznymi WCAG 2.1. Naszym celem było stworzenie narzędzia przydatnego dla wszystkich uczniów, w tym osób z niepełnosprawnościami. Zapewniliśmy, że aplikacja jest łatwa w obsłudze i zrozumiała dzięki dostosowaniu treści, takich jak ikony przedmiotów oraz brak limitów czasowych. Dzięki funkcjom takim jak wysoki kontrast, skalowalne strony i intuicyjne gesty, zapewnia ona spójną i przewidywalną nawigację, spełniając potrzeby użytkowników na platformach iOS i Android. Podczas projektowania uwzględniliśmy wpływ środowiskowy związany z pozyskiwaniem surowców, produkcją urządzeń i eksploatacją serwerów. Stosowaliśmy React Native, co pozwoliło na zmniejszenie zasobów potrzebnych do rozwoju. Nasza aplikacja działa w trybie offline, co zmniejsza zużycie energii przez urządzenia użytkowników, a optymalizacja kodu minimalizuje zużycie zasobów.

Rysunek 1.  Rysunek przedstawia przykładowe planowanie zadań na platformie Trello.

Rysunek 2.  Rysunek przedstawia przykładową współpracę nad kodem na platformie GitHub.

Rysunek 3.  Rysunek przedstawia zastosowanie Event Stormingu i User Story Mappingu przy użyciu platformy Miro.

Rysunek 4.  Rysunek przedstawia wykorzystanie przez nas wykresu Gantta oraz przedziały czasowe każdego z zadań.

## IV. BADANIA/TESTY
W ramach procesu rozwoju naszej aplikacji przeprowadziliśmy wywiady, w których uczestniczyło 15 tegorocznych maturzystów. Celem badania było zebranie opinii na temat użyteczności aplikacji oraz zidentyfikowanie mocnych i słabych stron projektu. Jednocześnie w trakcie rozwoju aplikacji udostępnialiśmy ją maturzystom, aby mogli ją przetestować, a następnie udzielić informacji zwrotnej. W trakcie badania zadaliśmy uczestnikom trzy kluczowe pytania:
Jak bardzo aplikacja jest przydatna w przygotowaniach do matury? (Uczestnicy mogli odpowiedzieć na to pytanie według trzystopniowej skali: mało przydatna, przydatna, bardzo przydatna).
Z jakich przedmiotów korzystałbyś w trakcie przygotowań do matury? (Uczestnicy mogli wskazać przedmioty, z których chcieliby korzystać w aplikacji: matematyka, angielski, fizyka, chemia).
Które działy były dla Ciebie najprzydatniejsze? (Uczestnicy oceniali przydatność poszczególnych działów dostępnych w aplikacji).
Oprócz przeprowadzonych ankiet z maturzystami nasza aplikacja testowna była przez nauczycieli którzy zapewniali nam materiały edukacyjne do pomocnika.
## V. WYNIKI I ANALIZA
Wyniki ankiet z maturzystami
Odpowiedzi do pytania 1 (rys. 5):
Mało przydatna: 0 osób (0%)
Przydatna:  osób: 5 (33%)
Bardzo przydatna: 10 osób (67%)

Rysunek 5.  Rysunek przedstawia wykres z udzielonymi odpowiedziami do pytania pierwszego.

Analiza: Wyniki pokazują, że większość maturzystów uznała aplikację za bardzo przydatną (67%), co wskazuje na pozytywne postrzeganie funkcjonalności aplikacji i jej potencjalną wartość w kontekście przygotowań do egzaminu maturalnego.
Odpowiedzi do pytania 2 (rys. 6):
Matematyka: 12 osób (80%)
Angielski: 8 osób (53%)
Fizyka: 5 osób (33%)
Chemia: 5 osoby (33%)

Rysunek 6.  Rysunek przedstawia wykres kołowy z udzielonymi odpowiedziami do pytania drugiego.

Analiza: Największe zainteresowanie wzbudziła matematyka, z której chciałoby korzystać 80% uczestników badania. Angielski był także popularnym przedmiotem, który interesował 53% maturzystów. Fizyka i chemia były mniej preferowane, co sugeruje, że przyszłe aktualizacje aplikacji mogłyby skoncentrować się na rozszerzeniu zawartości z matematyki i angielskiego.
Odpowiedzi do pytania 3 (rys. 7):
Funkcja kwadratowa (matematyka): 10 osób (67%)
Czasy (angielski): 7 osób (47%)
Planimetria (matematyka): 8 osób (53%)
Trygonometria (matematyka): 5 osób (33%)
Ciągi (matematyka): 3 osoby (20%)
Dynamika (fizyka): 2 osoby (13%)

Rysunek 7.  Rysunek przedstawia wykres słupkowy z udzielonymi odpowiedziami do pytania trzeciego.
Analiza: Funkcja kwadratowa okazała się najbardziej przydatnym działem w opinii 67% uczestników badania, co wskazuje na silne zainteresowanie tym zagadnieniem. Planimetria również była ważnym działem dla 53% maturzystów. W zakresie angielskiego, czasy były oceniane jako najbardziej przydatna przez 47% respondentów, podczas gdy w fizyce i chemii większą uwagę można poświęcić innym zagadnieniom w przyszłych wersjach aplikacji.
Wyniki przeprowadzonego badania pokazują, że nasza aplikacja jest postrzegana jako bardzo przydatne narzędzie do przygotowań do matury, z funkcją pomocnika uznawaną za szczególnie wartościową. Zebrane dane wskazują, że matematyka i angielski są najczęściej wybieranymi przedmiotami. Te informacje pozwolą nam na dalsze udoskonalanie aplikacji, w tym na rozwój treści w najbardziej potrzebnych obszarach oraz dostosowanie jej funkcjonalności do oczekiwań użytkowników.
Informacje zwrotne od nauczycieli
Z informacji zwrotnych udzielonych przez nauczycieli wynika, że w aplikacji pojawiają się błędy związane z poprawnym działaniem przycisku “Zamknij” oraz nachodzeniem tekstu na siebie w dziale matematycznym “Parametry danych statystycznych”.

## VI. WNIOSKI I PERSPEKTYWY ROZWOJU
Podsumowując naszą pracę, projekt przyniósł zarówno sukcesy, jak i wyzwania. Udało się stworzyć aplikację, która efektywnie odpowiada na potrzeby użytkowników dzięki zastosowaniu nowoczesnych technologii i skutecznej współpracy zespołowej. Implementacja nowych rozwiązań nie tylko zwiększyła funkcjonalność aplikacji, ale także przyczyniła się do rozwoju umiejętności technicznych i współpracy zespołowej. Napotkaliśmy jednak pewne trudności. Optymalizacja rozmiaru aplikacji była wyzwaniem, wymagającym ciągłej uwagi i doskonalenia. Szczególnie istotnym ograniczeniem okazał się brak licencji deweloperskiej Apple, który uniemożliwia nam zbudowanie aplikacji na iOS. Możliwe kierunki rozwoju naszej aplikacji obejmują poszerzenie współpracy z nauczycielami, co umożliwi lepsze dostosowanie materiałów edukacyjnych do potrzeb uczniów. Planujemy również rozszerzenie oferty o nowe przedmioty oraz interaktywne quizy, które pozwolą użytkownikom pogłębiać swoją wiedzę w sposób bardziej angażujący. Kolejnym kierunkiem rozwoju jest implementacja czytnika PDF, co szczególnie pomoże osobom niewidomym i niedowidzącym w korzystaniu z naszej aplikacji. Ponadto rozważamy dodanie wsparcia dla międzynarodowych matur, co umożliwi użytkownikom spoza Polski również korzystać z naszej aplikacji.
## ZAŁĄCZNIKI
https://github.com/Verionn/karty-maturalne
## PODZIĘKOWANIA
Pragniemy wyrazić naszą głęboką wdzięczność Prof. Ewie Korzeniewskiej za możliwość udziału w projekcie oraz za wiedzę, doświadczenie i wsparcie, które było dla nas niezwykle cenne. Dzięki pomocy Prof. Ewy Korzeniewskiej mogliśmy zdobyć nowe umiejętności, rozwijać nasze kompetencje oraz zrealizować projekt z sukcesem. Jesteśmy wdzięczni za poświęcony czas, cenne wskazówki oraz nieocenioną pomoc merytoryczną.
Dziękujemy również za udostępnienie profesjonalnych materiałów, które mogliśmy wykorzystać w naszym pomocniku.

Za pomoc w tworzeniu pomocnika do matematyki podziękowania dla:
Prof. Ewy Korzeniewskiej
Dr inż. Anny Goździewicz-Smejdy
Dr inż. Gertrudy Gwóźdź-Łukawskiej
Dr inż. Elżbiety Kotlickiej-Dwurznik
Dr Agnieszki Kubiś-Lipowskiej
Dr inż Adama Lipowskiego
Dr Joanny Peredko
Dr Moniki Potyrały
Dr inż. Witolda Walasa

Za pomoc w tworzeniu pomocnika do fizyki podziękowania dla:
Prof. Ewy Korzeniewskiej
Dr Cezarego Konecznego

Za pomoc w tworzeniu pomocnika do języka angielskiego podziękowania dla:
Prof. Ewy Korzeniewskiej
Mgr Marzeny Stawickiej
## BIBLIOGRAFIA
Centralna Komisja Egzaminacyjna. (2020). Raporty z egzaminów maturalnych, https://www.cke.gov.pl/egzamin-maturalny/raporty/
Fundacja Edukacyjna Perspektywy. (2020). Analiza wyników matury 2020. https://www.perspektywy.pl/portal/index.php?option=com_content&view=category&layout=blog&id=24&Itemid=119
Ministerstwo Edukacji i Nauki. (2023). Publikacje dotyczące egzaminów maturalnych. https://www.gov.pl/web/edukacja-i-nauka/publikacje
Khan Academy. (2020). Platforma edukacyjna Khan Academy. Pobrane z https://www.khanacademy.org/
Coursera. (2020). Platforma MOOC Coursera. https://www.coursera.org/
edX. (2020). Platforma MOOC edX.  https://www.edx.org/
Okręgowa Komisja Egzaminacyjna w Krakowie. (2020). Analiza wyników matury 2020. https://www.oke.krakow.pl/inf/filedata/files/R2020.pdf
Perspektywy. (2020). Matura 2020 - Analiza. https://www.perspektywy.pl/portal/index.php?option=com_content&view=article&id=5801:matura-2020-analiza&catid=24&Itemid=119
Portal edukacyjny. (2020). Narzędzia wspomagające naukę. https://www.edukacja.org.pl/narzedzia-wspomagajace-nauke
Scott, F. (2012). Is mathematics to blame? An investigation into high school students' difficulty in performing calculations in chemistry. Chemistry Education Research and Practice, 13, 330-336. https://doi.org/10.1039/C2RP00001F.
Hoban, R., Finlayson, O., & Nolan, B. (2013). Transfer in chemistry: a study of students’ abilities in transferring mathematical knowledge to chemistry. International Journal of Mathematical Education in Science and Technology, 44, 14-35. https://doi.org/10.1080/0020739X.2012.690895.
Bahar, M., & Polat, M. (2007). The Science Topics Perceived Difficult by Pupils at Primary 6-8 Classes: Diagnosing the Problems and Remedy Suggestions. Kuram Ve Uygulamada Egitim Bilimleri, 7, 1113-1129.
Dabit, Nader (2019). React Native in Action, Manning
Meta Open Source (2024), React Reference, https://react.dev/reference/react
React Native Documentation. (n.d.). Retrieved from https://reactnative.dev/docs/getting-started
TypeScript for React Native. (n.d.). Retrieved from https://www.typescriptlang.org/docs/
React Native Ecosystem. (n.d.). Retrieved from https://reactnative.dev/community
## WKŁAD W PRACĘ NAD PROJEKTEM
Adam Bijacik, Student 6. semestru kierunku Informatyka. koncentrując się na implementacji kart maturalnych oraz stworzeniu pomocnika. Był odpowiedzialny za opracowywanie i organizowanie materiałów do kart maturalnych oraz pomocnika, dbając o ich zgodność z konkretnymi działami tematycznymi. Ponadto, pisał dokumentację projektową, zapewniając jej klarowność i szczegółowość. Jego wkład w projekt był kluczowy dla zapewnienia wysokiej jakości merytorycznej i funkcjonalnej zarówno kart maturalnych, jak i pomocnika, co znacząco przyczyniło się do sukcesu projektu.
Wiktor Ciszewski, Student 6. semestru kierunku Informatyka pełnił kluczową rolę w projekcie, koncentrując się na tworzeniu interfejsu graficznego użytkownika. Projektował i implementował i estetyczne interfejsy oraz intuicyjną nawigacje po nich, dbając o spójność wizualną i funkcjonalność aplikacji. Był odpowiedzialny za tworzenie i utrzymanie dokumentacji projektowej, zapewniając jej klarowność i kompletność. Dokumentacja zawierała szczegółowe opisy funkcji, instrukcje obsługi oraz informacje techniczne. Dodatkowo, aktywnie pomagał w tworzeniu materiałów do kart maturalnych oraz pomocnika, opracowując i edytując treści, co zapewniło ich wysoką jakość merytoryczną.

Michał Dąbkowski, Student 6. semestru kierunku Informatyka. Pełnił rolę lidera projektu. W ramach projektu koncentrował się na organizacji pracy zespołu, stosując nowoczesne metodyki zarządzania projektami takie jak Scrum, Event Storming oraz User Story Mapping. Dzięki tym technikom praca zespołu była bardziej efektywna i zorganizowana. Ponadto, brał aktywny udział w projektowaniu warstwy wizualnej, dbając o intuicyjność i estetykę interfejsu użytkownika. Jego zaangażowanie obejmowało również programowanie frontendu, gdzie wykorzystywał najnowsze technologie, aby zapewnić responsywność i interaktywność aplikacji. Współpracował ściśle z resztą zespołu, co pozwalało na szybkie rozwiązywanie problemów i wprowadzanie innowacyjnych rozwiązań. Dodatkowo, koordynował regularne spotkania zespołu, co przyczyniło się do ciągłego doskonalenia procesów projektowych. Dzięki jego umiejętnościom zarządzania oraz technicznemu doświadczeniu, projekt został zrealizowany terminowo i zgodnie z założeniami jakościowymi.

Joram Mumb Mulaj Kambaj Student 6. semestru kierunku Informatyka, odpowiedzialny za stworzenie interfejsu graficznego aplikacji. Jego główne zadania obejmowały zaprojektowanie ekranów, dodanie ikon SVG oraz animacji, a także opracowanie systemu nawigacji. Pracował nad projektowaniem i implementacją wizualnych elementów interfejsu, dbając o estetykę i intuicyjność użytkowania. Współpracował ściśle z zespołem, aby zapewnić spójność i funkcjonalność aplikacji, korzystając z narzędzi takich jak Figma, Trello i GitHub. Dzięki temu projektowi zdobył cenne doświadczenie w tworzeniu i wdrażaniu interfejsów graficznych, co przyczyniło się do rozwoju jego umiejętności zawodowych. Jego praca nad projektem pozwoliła mu tworzyć rozwiązania estetyczne i funkcjonalne, co znacząco rozwinęło jego umiejętności projektowania, implementacji i pracy zespołowej.
prof. Ewa Korzeniewska, Opiekun grupy, odpowiedzialna za koordynację działań, odegrała kluczową rolę w projekcie. Zajmowała się nie tylko organizacją pracy zespołu, ale także aktywnie wspierała tworzenie oraz komunikację z innymi nauczycielami w celu opracowania materiałów do pomocnika. Jej zaangażowanie w proces twórczy oraz efektywna współpraca z innymi nauczycielami miała istotny wpływ na jakość i kompleksowość przygotowywanych materiałów edukacyjnych. Dzięki jej działaniom projekt zyskał solidne wsparcie merytoryczne i pedagogiczne, co przyczyniło się do jego sukcesu i przydatności dla uczniów.



WADY:
Tylko do Waszej wiadomości przesyłam raport i uwagi do niego:
- rys. 1 i 2 nie są widoczne, trzeba sprawdzić jak są osadzone w pliku
- nie widzę odwołań do rysunków
- wyniki pokazujemy albo na wykresie – tu lepiej wykres kołowy, jeśli całość spina się 100%. Studenci opisują w tekście i dokładają wykres.
- może jakiś fragment kodu umocniłbym informatykę w tym projekcie
- podobnie brak jakiegoś zrzutu ekranu powoduje, że mając w ręce sam raport nie bardzo wiadomo co było zrobione ii jak wygląda…
Co do opinii na temat wniosków – tu trochę podszedłem krytycznie
- wnioski z tych danych są wyciąganie chyba zbyt pochopnie, nie bardzo wiadomo, co takiego przydatnego było bardziej/mniej w poszczególnych działach, a czy matematyka nie jest z reguły kluczowym przedmiotem dla uczniów, stąd bez aplikacji uważają wszelkie rozwiązania za bardzo przydatne?
- nie przekonujemy mnie, ze jak uczniowie wybrali matematykę i angielski za najbardziej interesujące to „przyszłe aktualizacje aplikacji mogłyby skoncentrować się na rozszerzeniu zawartości z matematyki i angielskiego”

Duzy plus za literaturę!!! I całą formę raportu oraz dokumentacje.
