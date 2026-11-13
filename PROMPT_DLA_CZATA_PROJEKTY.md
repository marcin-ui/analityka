# PROMPT — Dashboard PROJEKTY: zasilenie danymi z Firmao i budowa produkcyjna

Wklej całość do czata, który ma dostęp do danych firmy i do Firmao (backend/API/eksporty).

---

## Rola i twarde zasady

Budujesz produkcyjny dashboard **Projekty** dla dyrektora zarządzającego firmy wykonującej
posadzki/odwodnienia/roboty drogowe. Istnieje już **działająca wersja referencyjna** zbudowana
na eksportach XLSX (repo `marcin-ui/analityka`, gałąź `claude/folder-analysis-overview-b0mvar`) —
jeśli masz do niej dostęp, przeportuj; jeśli nie, ten prompt zawiera komplet specyfikacji.

Zasady architektury (OBOWIĄZKOWE, przetestowane na wersji referencyjnej):

1. Dane płyną tylko w górę: **surowe (read-only) → kanoniczne (Karta Projektu) → metryki → UI**.
   UI niczego nie liczy — czyta gotowe liczby.
2. Progi i słowniki w plikach konfiguracyjnych (`progi.yaml`, `slowniki.yaml`) — edycja bez kodu.
3. Każda liczba audytowalna: klik → karta projektu → rekordy źródłowe.
4. **Zakaz atrap**: brak danych pokazujesz jako „BRAK (kod decyzji)", nigdy nie wymyślasz wartości.
5. Zła dana nie znika — dostaje status i ląduje w rejestrze odrzuconych + zakładce Jakość danych.
6. Nie zgadujesz znaczenia pól — pytania zbiorczo na końcu każdej fazy. Po każdej fazie STOP
   i czekasz na akceptację właściciela.

## Kontekst — co już wiemy o danych (NIE odkrywaj tego od nowa)

Ustalenia z audytu (pełny: `AUDYT_DANYCH.md`, `ZALOZENIA_DASHBOARD.md`, `raport-spiecie-budzet-projekty.md`):

- **Klucz łączący wszystko: `id` projektu Firmao.** Aplikacja brygad (Start/Stop) ma go w nazwie
  projektu przed dwukropkiem („1220 : ATAL odwodnienia…") — zweryfikowane 17/19.
  Oferty mają `project.id` (pokrywa 97,6% projektów).
- **Faktury w standardowym eksporcie NIE mają project.id** (191 kolumn sprawdzonych) — to luka K1.
  Firmao MA transakcje projektowe (agregaty `saleTransactionNetto`/`purchaseTransactionNetto`
  na projektach są niezerowe) — trzeba je wyciągnąć (patrz Zadanie A).
- **Trzy różne „prawdy" o przychodzie** w Firmao: suma faktur SALE = 26,57 mln; suma
  `actualIncomeSummaryNetto` projektów = 45,27 mln; suma `saleTransactionNetto` = 20,46 mln.
  Zanim użyjesz którejkolwiek — ustal z właścicielem definicję (pytanie P-B raportu spięcia).
- **Projekty widzą tylko ~40% kosztów firmy** (koszty ogólne nie są projektowe). Dashboard
  Projekty liczy „czy zarabiamy na robocie" (marża pokrycia), NIE koszty firmy — te należą
  do dashboardu Budżet. Z Projektów do Budżetu idą wyłącznie miary nieksięgowe.
- **Czas pracy brygad jest brudny**: 56% wpisów wadliwych (zapomniany STOP >12 h — 85% wszystkich
  godzin; zapomniany START = 0 h przy wykonanej produkcji). Filtr anomalii jest OBOWIĄZKOWY
  przed jakąkolwiek metryką. Eksport nie ma dat (luka D1).
- Pola niestandardowe projektów: `custom2` = typ projektu, `custom11` = technologia,
  `custom9` = osoba (rola niepotwierdzona). Znaczenia pól kwotowych `customTypes.custom50–65`
  NIEZNANE (luka K2) — nie zgaduj, pobierz słownik pól (Zadanie A.2).
- Statusy: `projectStatus.label` ∈ {Otwarty, Zakończony, Zakończony i ROZLICZONY}; flaga
  `completed` bywa sprzeczna ze statusem — używaj etykiety statusu.

## ZADANIE A — zaciągnięcie danych z Firmao (kolejność wg wartości)

Dla każdego punktu: pobierz → pokaż próbkę 20 rekordów → policz kompletność → STOP przed użyciem w metrykach.

1. **K1 — transakcje/dokumenty per projekt**: eksport lub endpoint dający pozycje kosztów
   i przychodów z przypisaniem do projektu (w UI Firmao: transakcje projektowe / dokumenty
   z kolumną „Projekt"). Cel: koszty real per kategoria per projekt + drill-down do faktur.
2. **K2 — słownik pól niestandardowych**: konfiguracja pól custom (Ustawienia → Pola
   niestandardowe albo endpoint konfiguracji). Cel: nazwy `custom50–65` i pól-dat → rozbicie
   kalkulacji plan per kategoria.
3. **Świeży zrzut podstaw**: projekty (wszystkie pola + custom), oferty (z `project.id`,
   `issuingPerson`, statusem), faktury (z kategoriami `custom14/custom9`). Wersja referencyjna
   stoi na zrzucie z 2026-06-11 — wszystko nowsze jest wartością.
4. **D1 — czas pracy Z DATAMI**: eksport aplikacji Start/Stop na poziomie pojedynczych wpisów
   z timestampami start/stop (aplikacja je ma, bo liczy czas). Cel: run-rate, trendy brygad,
   okna 30-dniowe.
5. RW/wydania magazynowe per projekt, jeśli osiągalne (dziś tylko agregat, 112 projektów).

## ZADANIE B — dashboard: 6 zakładek (szkielet ZATWIERDZONY przez właściciela — nie zmieniaj układu)

### Zakładka 1 — Pulpit (jeden ekran, 10 sekund, max 7 wskaźników)
- Kafel **Marża YTD**: % real vs % plan + delta w zł (projekty zakończone z kompletem plan+real, rok bieżący).
- Kafel **Strefy odchyleń**: liczniki zielona/żółta/czerwona (progi z `progi.yaml`: ≤5% / ≤10% / >10%
  odchylenia kosztów real vs plan).
- Kafel **Zagrożona marża**: suma utraty marży Top 5 + OSOBNO suma ogona (ogon bywa większy niż Top 5!).
- Kafel **Nierozliczone**: zakończone z przychodem <80% planu (liczba + luka w zł) + zakończone
  z zerowym przychodem. W danych z 11.06: 769,8 tys. zł luki — największa dźwignia gotówkowa.
- Wykres **trend błędu kalkulacji** (wskaźnik Deminga): mediana |plan−real|/plan per półrocze,
  od 2024 H1 (wcześniej dane planu niekompletne — błąd >100%).
- **Utylizacja czasu brygad**: % produkcyjny vs nieprodukcyjny (tylko wpisy po filtrze anomalii).
- **Pętla PDCA**: otwarte działania korygujące (rejestr trwały, nie localStorage).
- Nagłówek: data ostatniego zasilenia + plakietka LAG (patrz definicje).

### Zakładka 2 — Dźwignia (systematyka → korekty standardów)
- Per **typ projektu** (custom2): mediana odchylenia kosztów, n, wykres dywergentny.
- Per **kalkulujący**: bias (mediana odchylenia) ODDZIELNIE od rozrzutu (IQR) + recepta
  (bias → korekta standardu; rozrzut → szkolenie).
- **Normy real** per zadanie z aplikacji brygad (mediana tempa, ≥2 projekty) vs norma plan (gdy będzie D2).
- **Marża na roboczogodzinę** per projekt (zakończone, ≥5 h czystych) z flagą „nierozliczony — możliwy lag".

### Zakładka 3 — Plan vs Wykonanie
Pełna lista projektów: sort domyślny utrata marży rosnąco; filtry: rok / status / strefa / typ /
kalkulujący + szukajka (ID albo nazwa); pasek marży real ze znacznikiem planu; paginacja.

### Zakładka 4 — Gdzie tracimy
Top 5 utraty marży w ZŁOTÓWKACH (nie %), okres 2025–26, PO wykluczeniu lagiem + kafel ogona
+ tabela nierozliczonych (sort po luce) + przekroczenia wg przyczyn (custom90) + reklamacje (custom10).

### Zakładka 5 — Jakość danych
Godziny/wpisy odrzucone przez filtr; rzetelność wpisów per pracownik (% poprawnych, cel >90%);
projekty bez kompletu plan+real; żywa lista braków D/K z informacją, którą sekcję blokują.

### Zakładka 6 — Karta projektu (drill-down)
Wyszukiwarka + **routing URL** (`#/projekt/1041`) — wymagany pod przyszły drill z dashboardu
Budżet (lampki 7/8). Zawartość: wynik finansowy plan/real/odchylenie; kategorie kosztów
(z K1/K2 — do tego czasu jawne „BRAK"); czas pracy z normami i WSZYSTKIMI wpisami źródłowymi
(w tym odrzuconymi, z flagami); zakres wykonany vs plan ilości; flagi rozliczeniowe;
notatka Act zapisywana do trwałego rejestru PDCA.

## Definicje metryk (BINDING — identyczne jak w wersji referencyjnej)

```
odchylenie_kosztow_pct = (koszt_real − koszt_plan) / koszt_plan × 100   [tylko koszt_plan > 0]
utrata_marzy           = (przychod_real − koszt_real) − (przychod_plan − koszt_plan)
strefa                 = zielona ≤5 < żółta ≤10 < czerwona               [progi.yaml]
blad_kalkulacji        = mediana( |odchylenie_kosztow_pct| ) per półrocze, zakończone z kompletem
bias kalkulującego     = mediana(odchylenie); rozrzut = IQR(odchylenie); min. n=15
komplet plan+real      = koszt_plan>0 ∧ przychod_plan>0 ∧ koszt_real>0 ∧ przychod_real>0
filtr anomalii czasu   = wpis >12 h → ANOMALIA_STOP; 0 h przy zadaniu z metryką → ANOMALIA_START;
                         do metryk wchodzą wyłącznie wpisy OK; odrzucone → rejestr ODRZUCONE
nieprodukcyjne         = {Dojazd, Przerwa nr 1 i 2, Sprzątanie, Zabezpieczenie}   [slowniki.yaml]
rzetelnosc osoby       = % wpisów OK
niedofakturowany       = zakończony ∧ nierozliczony ∧ 0 < przychod_real < 0.8 × przychod_plan
LAG                    = zakończony nierozliczony wchodzi do rankingu strat dopiero 30 dni
                         po dacie końca [progi.yaml] — chroni przed fałszywką z lagu faktur
norma real             = wykonana ilość (MAX per zadanie-projekt, bo wartość jest na poziomie
                         zadania!) / suma godzin OK — NIGDY nie sumuj wartości po wierszach osób
```

## Spięcie z dashboardem Budżet (z raportu spięcia — przestrzegaj)

- Budżet konsumuje z Projektów WYŁĄCZNIE miary nieksięgowe: marża pokrycia projektów,
  nierozliczone, normy, sygnał utylizacji. Nigdy „koszty firmy".
- Marżę projektową nazywaj **„marżą pokrycia"** dopóki nie ma pełnej robocizny (D3) i kategorii (K1/K2).
- Wystaw jedną tabelę uzgodnienia: przychód/koszty wg faktur vs wg transakcji projektowych
  vs wg agregatów projektów — z wyjaśnieniem różnic (dziś: 26,6 / 20,5 / 45,3 mln!).

## Fazy pracy i STOPy

1. **Faza A**: pobrania z Firmao (Zadanie A) + raport próbek i kompletności → STOP.
2. **Faza B**: warstwa kanoniczna (Karta Projektu per projekt) + rejestr odrzuconych → raport ile
   projektów przeszło czysto → STOP.
3. **Faza C**: metryki + dashboard 6 zakładek zasilony realnymi danymi + instrukcja odświeżania
   (jedna komenda) → STOP.
4. **Faza D**: automatyzacja zasilania (API/cron) + routing pod drill z Budżetu.

Każda faza: raport markdown w repo + pytania zbiorczo na końcu. Wynik bez dowodu
(ścieżka pliku / endpoint / policzalna liczba) nie istnieje.

## Checklist akceptacyjny (właściciel odhacza przed „gotowe")

- [ ] Kafle Pulpitu zgadzają się z wersją referencyjną na tym samym zrzucie danych (±zaokrąglenia).
- [ ] Klik z każdej tabeli prowadzi do karty projektu; karta ma URL.
- [ ] Filtr anomalii działa: suma godzin w metrykach ≪ suma surowa; rejestr odrzuconych istnieje.
- [ ] Braki pokazane jawnie z kodami D/K — zero atrap.
- [ ] Progi zmieniają się w progi.yaml bez dotykania kodu.
- [ ] Tabela uzgodnienia trzech źródeł przychodu opublikowana.
