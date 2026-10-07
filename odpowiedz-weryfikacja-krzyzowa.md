# ODPOWIEDŹ — Krzyżowa weryfikacja dashboardu „Projekty" (czat budujący back/front)

**Weryfikował:** czat referencyjny (repo `analityka`, eksporty Firmao z 2026-06-11 + aplikacja brygad).
Każdy werdykt policzony na pełnych danych — nie na opinii. Format: POTWIERDZAM / BŁĄD / NIE WIEM.

---

## Decyzje do weryfikacji

### 1. Spółka = tag w jednej instancji — **NIE WIEM na żywym API + ważny trop wstecz**

- W eksporcie `tags`, a także `managers`, `observers`, `teamMembers` = **100% puste** (1 138 projektów).
  Może to być ograniczenie eksportu XLSX — test na żywym API jest właściwym krokiem. Ale jeśli tagi
  są puste też na API, to wymiar spółki działa wyłącznie „od dziś", bez historii.
- **Trop na backfill historyczny:** faktury sprzedaży mają pole `sellerBankAccountNumber`
  z **dwoma głównymi rachunkami**: `…1992 1620` (1 434 faktury po normalizacji „PL", ~22,84 mln)
  i `…7633 7915` (44 faktury, ~2,96 mln) + trzeci śladowy. To niemal na pewno dwie spółki.
  Propozycja: spółka = tag od dziś, wstecz = mapowanie po rachunku sprzedawcy z faktur.
  Uwaga techniczna: ten sam rachunek występuje z prefiksem „PL" i bez — normalizować przed grupowaniem.

### 2. Marża 3-warstwowa — **kierunek POTWIERDZAM, dwie równości to BŁĄD jako prawo uniwersalne**

Koncepcja (odporność na lag rozliczeń) jest słuszna i zbieżna z regułą LAG=30 dni w wersji referencyjnej. Ale:

- **„rozliczona = actualIncomeSummaryNetto − actualCostSummaryNetto = finalProfitSummaryNetto"** —
  równość zachodzi tylko w **67%** projektów ogółem. Per rok zakończenia:
  2021: 91% · **2022: 18% (54/300!)** · 2023: 59% · 2024: 93% · 2025: 100% · 2026: 100%.
  → Wzór jest legalny **od 2024**. Dla 2021–23 używać `finalProfitSummaryNetto` wprost (nie różnicy pól)
  albo oznaczyć erę flagą; inaczej historyczny trend błędu kalkulacji pojedzie na artefaktach.
- **„Δ w toku = saleTransactionNetto − actualIncomeSummaryNetto"** — dla 2026 POTWIERDZAM:
  delta = **+249,8 tys.** na zrzucie z 11.06 (ich ~281k na świeższych danych — spójne co do rzędu
  i kierunku). ALE globalnie `income > sale` w **535 projektach** (stare lata, suma 45,3 vs 20,5 mln) —
  tam „Δ w toku" wychodzi absurdalnie ujemna. Wniosek: Δ w toku liczyć TYLKO dla projektów
  z prowadzonymi transakcjami (sale>0), dla reszty — „n/d", nie zero.
- **Nazewnictwo:** wszystkie trzy warstwy to nadal **marża POKRYCIA** — projekty widzą ~40% kosztów
  firmy (koszty projektowe = 3,4 z 26,1 mln faktur zakupu). Wymóg z raportu spięcia z Budżetem:
  nie nazywać tego „marżą netto".

### 3. Koszt = actualCostSummaryNetto — **wybór POTWIERDZAM, dopisek „(=|purchaseTransactionNetto|)" to BŁĄD**

- `actualIssuedGoodsValueNetto`: >0 tylko w 112/1 138 projektów (10%), suma 224,7 tys. —
  zgadza się z Waszym „puste ~90%". Odrzucenie słuszne.
- Ale `actualCostSummaryNetto == |purchaseTransactionNetto|` tylko w **47%** projektów;
  suma rozjazdów **3,84 mln zł**. Agregat kosztów zawiera coś ponad transakcje zakupu — co dokładnie,
  wyjaśni Wasz endpoint `transactionentries`: przetestujcie `suma pozycji ACTUAL ==? actualCostSummaryNetto`
  per projekt. Do tego czasu nie traktować tych pól zamiennie.

### 4. Rok wg endDate, PLN netto — **POTWIERDZAM** (identycznie w wersji referencyjnej).
Zakres „minus tagi anulowane/wstrzymane" — **NIE WIEM**: w eksporcie nie ma ani tagów, ani statusu
„anulowany" (statusy to tylko Otwarty / Zakończony / Zakończony i ROZLICZONY). Sprawdzić na API,
czym naprawdę oznaczane są anulowane.

### 5. 6 zakładek — **POTWIERDZAM układ** (zatwierdzony przez właściciela). Braki do sprawdzenia u Was:
- kafel **Nierozliczone** na Pulpicie (zakończone z przychodem <80% planu: 769,8 tys. luki na zrzucie
  z 11.06 — największa dźwignia gotówkowa w danych),
- reguła **LAG** (świeżo zakończone poza rankingiem strat przez 30 dni),
- **filtr anomalii czasu brygad** — w opisie Waszego buildu ani słowa, a bez niego 85% godzin
  to śmieci (wpisy >12 h = zapomniany STOP; 0 h przy wykonanej produkcji = zapomniany START;
  do metryk tylko wpisy OK: w pliku referencyjnym 143/326),
- **trwały rejestr PDCA** — patrz uwaga architektoniczna niżej.

## Kontrakt danych

- Klucz = id projektu, aplikacja brygad ma go przed „:" — **POTWIERDZAM** (zweryfikowane 17/19;
  2 brakujące to projekty nowsze niż zrzut).
- `custom2`=typ, `custom11`=usługa — **POTWIERDZAM**. `custom9`=handlowiec — **PRAWDOPODOBNE,
  NIEPOTWIERDZONE**: wypełnione 77%, wartości to osoby (Miedzak, Michalski, Zimnowłodzki…) INNE niż
  wystawiający oferty (Przyklenk, Adamczyk…) — rola wymaga potwierdzenia właściciela, nie przyjmujcie
  etykiety „handlowiec" bez tego. Uwaga na kolizję: `custom9` na FAKTURACH to podkategoria kosztów —
  to samo id pola, inny obiekt.
- `managers`=zespół — **NIE WIEM**: w eksporcie 100% NULL. Nie budować sekcji Brygady na tym polu
  bez próbki z API.
- **`/svc/v1/transactionentries` — najcenniejsze odkrycie Waszej pracy**: domyka lukę K1
  (pozycje plan/real per projekt, used/remains/overdraft). Ale rekoncyliacja na JEDNYM projekcie (1211)
  to za mało na „POTWIERDZAM": wymagamy **≥20 projektów z różnych lat, koniecznie z 2022–23**
  (tam agregaty pękają — patrz pkt 2) + test zgodności sum pozycji z agregatami projektu.
- Trzy „prawdy" o przychodzie — rozjazd potwierdzony niezależnie. Rekomendacja: przychód liczyć
  z POZYCJI (`transactionentries`), agregaty `*Summary*` trzymać jako sumy kontrolne; która definicja
  jest „przychodem projektu" — decyzja właściciela (pytanie P-B z raportu spięcia, wciąż otwarte).

## Ryzyka przy podłączaniu żywego Firmao (uzupełnienie Waszej listy)

1. **Era danych**: wzory pól działają od 2024, wcześniej rozjazdy (pkt 2–3). Dashboard musi mieć
   flagę wiarygodności per projekt/rok, inaczej trend Deminga i Dźwignia pokażą artefakty.
2. **Brudny czas brygad**: filtr anomalii OBOWIĄZKOWY + rejestr odrzuconych z nazwiskami
   (wskaźnik rzetelności per osoba — jest w referencji, zakładka Jakość danych).
3. **custom50–65 nadal NIEZNANE** (luka K2) — nie mapować bez słownika pól z konfiguracji Firmao.
4. **Stub→żywe dane**: checklist akceptacyjny z prompta obowiązuje — w szczególności zgodność kafli
   z wersją referencyjną NA TYM SAMYM ZRZUCIE (inaczej nie odróżnicie błędu kodu od świeżości danych).

## Architektura

- Front nic nie liczy — **POTWIERDZAM, zdrowe** (identyczna zasada w referencji).
- Serwis per zakładka — OK pod warunkiem **wspólnego modułu definicji metryk** (strefy, bias/IQR,
  utrata marży, LAG) — jedna implementacja, sześć konsumentów; inaczej zakładki się rozjadą.
- Spółka jako parametr — OK (z zastrzeżeniem z pkt 1).
- **„Liczy w pamięci, brak bazy" — największa uwaga.** Bez jakiejkolwiek trwałości nie istnieją:
  rejestr PDCA (wymóg właściciela: trwały, to serce pętli Deminga), rejestr odrzuconych wpisów czasu,
  historia alertów, ani odtwarzalność („co widziałem wczoraj na desce?" — liczby zmienią się pod ręką).
  Nie potrzeba dużej bazy: wystarczy dzienny snapshot JSON + trwały plik/SQLite na PDCA i alerty.
  Bez tego dashboard jest kalkulatorem, nie systemem zarządczym.

## Pytania do właściciela (zbiorczo, do jednej rozmowy)

1. P-B (nadal otwarte): która liczba jest „przychodem projektu" — pozycje transakcji, faktury SALE,
   czy `actualIncomeSummaryNetto`?
2. Czy `custom9` na projekcie to handlowiec/opiekun? (77% wypełnień, osoby ≠ wystawiający oferty)
3. Dwa rachunki sprzedawcy na fakturach (…1620 ~22,8 mln i …7915 ~3,0 mln) — czy to SPK i sp. z o.o.?
4. Czym oznaczane są projekty anulowane/wstrzymane (tagi w eksporcie puste)?
5. Zgoda na minimalną trwałość (snapshot + PDCA w pliku/SQLite) mimo decyzji „brak bazy"?
