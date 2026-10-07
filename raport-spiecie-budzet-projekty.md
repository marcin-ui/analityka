# RAPORT — Spięcie koncepcji Budżet (p16) z danymi Projektów
### Audyt od strony repozytorium `analityka` (dashboard Projekty)

**Data:** 2026-07-06 · **Audytor:** Claude (sesja Projekty) · **Tryb:** zakaz implementacji — wyłącznie raport.

## 0. Zakres i uczciwe granice tego audytu

To repozytorium zawiera: eksporty Firmao (XLSX z 2026-06-11), raport czasu pracy brygad,
ETL i pulpit Projekty. **NIE zawiera** kodu budżetu/weryfikatora (backend, endpointy,
`closedThrough`, Excel planu 2026, K1/K2/K3). Dlatego:

- **Sekcje A, B, C, E prompta → NIE ZWERYFIKOWANE TUTAJ** — wymagają uruchomienia audytu
  w repozytorium budżetu/weryfikatora. Poniżej odpowiadam tylko na te ich fragmenty,
  które dotykają danych Projektów.
- **Sekcja D (punkty styku z Projektami) → ZWERYFIKOWANA W PEŁNI**, z dowodami
  (pliki, kolumny, liczby policzone na danych).

Zasada dowodowa zachowana: każda liczba niżej pochodzi z konkretnego pliku i jest
odtwarzalna skryptem na danych z tego repo.

---

## 1. ODKRYCIE NADRZĘDNE — trzy różne „prawdy" o przychodzie i kosztach

Policzono z plików (2026-06-11):

| Miara | Faktury.xlsx (rejestr dokumentów) | Projekty_wszystkie.xlsx (agregaty Firmao) |
|---|---|---|
| Przychód | **26,57 mln** (1 500 faktur SALE, `baseNettoPrice`) | **45,27 mln** (`actualIncomeSummaryNetto`) / **20,46 mln** (`saleTransactionNetto`) |
| Koszty | **26,11 mln** (8 600 faktur PURCHASE) | **10,55 mln** (`actualCostSummaryNetto`) |

Wnioski twarde:

1. **Agregaty projektowe Firmao ≠ rejestr faktur.** Rozjazd przychodu 26,6 vs 45,3 vs 20,5 mln
   (prawdopodobnie: `actualIncomeSummary` zawiera transakcje nie-fakturowe/prognozy, a `saleTransaction`
   tylko transakcje projektowe; bez słownika Firmao — patrz pytania). Rozjazdu NIE wolno ignorować.
2. **Projekty widzą tylko ~40% kosztów firmy** (10,5 z 26,1 mln) — bo koszty ogólne (utrzymanie aut,
   pracownicy, administracja…) nie są przypinane do projektów. Dowód niezależny: na fakturach zakupu
   kategoria `customFields.custom14` = „Koszty projektowe" to tylko **1 979 z 8 600 faktur, 3,41 mln zł**.
3. **Konsekwencja dla p16 §7:** podział „Budżet = agregat wszystkich kosztów, Projekty = tylko projektowe"
   jest ZGODNY z danymi ✅ — ale „budżet konsumuje z Projektów SUMY" wymaga jawnego mostka uzgodnienia,
   inaczej deska budżetu i pulpit Projekty pokażą różne kwoty za ten sam miesiąc i zaufanie do obu spadnie.

---

## 2. Sekcja A prompta (6 lampek) — tylko wkład Projektów

| Lampka | Czy dane z TEGO repo mogą ją zasilić? | Dowód / uwaga |
|---|---|---|
| 1. Zysk netto EoY | ❌ nie stąd — wymaga planu 2026 + pełnych kosztów (repo budżetu) | tu tylko 40% kosztów (pkt 1) |
| 2. Przychód vs plan | ⚠️ częściowo: `Faktury.xlsx` SALE per miesiąc (`documentDate`) — ale to eksport z 11.06, nie live | 1 500 faktur SALE, komplet dat |
| 3. Koszty vs plan | ⚠️ jw.: PURCHASE per miesiąc + słownik `custom14/custom9` (76% pokrycia, 24% faktur bez kategorii) | 8 600 faktur; dwie pisownie „administracyjne" |
| 4. EBITDA | ❌ nie stąd (amortyzacja, księgi — repo budżetu/weryfikator) | — |
| 5. Gotówka operacyjna | ⚠️ sygnał częściowy: `paid`, `paymentStatus`, `actualPaymentDate` w Faktury.xlsx | pola wypełnione ~100% |
| 6. Największa dźwignia | ⚠️ od strony projektowej JUŻ liczona w pulpicie Projekty (typy z medianą przekroczeń, nierozliczone 769,8 tys. luki) | `pulpit/dane.js → metryki.dzwignia` |

**Status zbiorczy A z perspektywy Projektów: ⚠️** — eksporty mogłyby awaryjnie zasilić lampki 2/3/5,
ale to byłaby RÓWNOLEGŁA ścieżka do weryfikatora → dokładnie ryzyko, przed którym prompt ostrzega w E1.
Nie rekomenduję; właściwe źródło lampek 1–6 to backend budżetu.

## 3. Sekcja B–C prompta — NIE ZWERYFIKOWANE TUTAJ

Plan 2026 (Excel), sezonalizacja, K1 header vs rows ~147k, „sierota Koszty projektowe", wymiar
spółek SPK/sp. z o.o. — **brak tych artefaktów w tym repo**. Jedno powiązanie mogę potwierdzić:
firmowy słownik kategorii kosztów żyje na fakturach zakupu w `customFields.custom14` (11 kategorii K1-podobnych)
i `custom9` (115 podkategorii) — jeśli budżetowe K1/K2/K3 budowane jest z tego samego słownika, to
„sierota Koszty projektowe" niemal na pewno pochodzi z faktur oznaczonych `custom14='Koszty projektowe'`
(3,41 mln zł), które w logice budżetu ogólnego nie mają rodzica — bo ich rodzicem jest PROJEKT, nie dział.
To wspiera decyzję z §7: te koszty powinny drillować do dashboardu Projekty, nie wisieć w drzewie budżetu.

Magiczne liczby PO STRONIE PROJEKTÓW (analogia do B4, uczciwie zgłaszam własne):
`etl/metryki.py`: `ROK_BIEZACY = 2026`, `DATA_ZRZUTU = "2026-06-11"` — zaszyte w kodzie (do przeniesienia
do konfiguracji przy automatyzacji zasilania); parsowanie planu ilości z NAZWY projektu (przejściowe, D2).

## 4. Sekcja D prompta — punkty styku z Projektami (PEŁNA ODPOWIEDŹ)

### D1–D2. Co per projekt istnieje dziś, gdzie żyje, jaka jakość

| Dane per projekt | Status | Gdzie żyje | Kompletność (próbka z pełnych danych) |
|---|---|---|---|
| Przychód per projekt | ✅ | `Projekty_wszystkie.xlsx: actualIncomeSummaryNetto`; kanonicznie: `data/kanoniczne.json → real.przychod` | 1 055/1 138 projektów >0 (93%) |
| Koszt per projekt (suma) | ✅ | jw. `actualCostSummaryNetto` | 985/1 138 >0 (87%); ale to tylko koszty projektowe — pkt 1 |
| Marża per projekt | ✅ | liczona w `etl/kanoniczne.py → real.marza` | 685 projektów z kompletem plan+real (pilotaż) |
| Podział FAKTUR na projekty | ❌ | brak kolumny `project.*` w `Faktury.xlsx` (191 kolumn sprawdzonych, jest tylko `task.id` 3,5%) | luka K1; transakcje projektowe ISTNIEJĄ w Firmao (agregaty niezerowe), brak w eksporcie |
| RW / zużycia materiałów per projekt | ⚠️ suma bez pozycji | `actualIssuedGoodsValueNetto` w projektach | tylko 112/1 138 projektów >0, suma 224,7 tys. — śladowe; pozycji RW brak w żadnym eksporcie |
| Czasy pracy per projekt (Firmao) | ⚠️ | `actualWorkHours` | 713/1 138 >0 (63%); bez rozbicia na osoby/zadania |
| Czasy pracy per projekt (aplikacja Start/Stop) | ⚠️ | `dane_czas_pracy/*.xlsx`, po filtrze: `data/kanoniczne.json → czas_pracy` | 19 projektów, 1 plik; 143/326 wpisów poprawnych (44%); **zero dat** w eksporcie (D1); klucz = ID Firmao w nazwie ✅ zweryfikowany 17/19 |
| Przychód/koszt per USŁUGA (technologia) | ⚠️ | `customFields.custom11` (19 wartości: powłoki, impregnacje…) | 69% projektów ma technologię; grupowanie możliwe od dziś |
| Od kiedy prowadzone | — | projekty od 04.2021; aplikacja czasu: brak dat w eksporcie → nieznane | — |

### D3. Czego brakuje do utylizacji kadry i marży per projekt/usługa

**Utylizacja kadry (lampka 7):**
- brak danych U ŹRÓDŁA (proces): dostępna pojemność (etaty × kalendarz) — nigdzie; daty wpisów czasu (D1);
  mapowanie osoba→brygada (D5 — plik `konfiguracja/slowniki.yaml` czeka pusty); dyscyplina Start/Stop
  (56% wpisów wadliwych — szkolenie, PDCA-03);
- dane SĄ, brak agregacji (kod): rozbicie produkcyjne/nieprodukcyjne per osoba — JUŻ policzone
  (`pulpit/dane.js → dzwignia.utylizacja`, rzetelność per osoba w zakładce Jakość danych).
- Werdykt: **lampka 7 w p16 słusznie jest tylko SYGNAŁEM** — pełna utylizacja wymaga D1+D5+pojemności,
  czyli decyzji procesowych, nie kodu.

**Marża per projekt/usługa (lampka 8):**
- dane SĄ, brak agregacji: marża per projekt ✅ już liczona (685 szt.); per technologia — do policzenia
  z `custom11` od ręki;
- brak U ŹRÓDŁA: koszt robocizny w PLN (stawki D3), koszty per kategoria (K1/K2), przez co „marża"
  per projekt NIE zawiera dziś pełnej robocizny i kosztów ogólnych → to marża I stopnia (pokrycia),
  nie netto. Lampka 8 może na tym działać, jeśli tak zostanie NAZWANA.

### D4. Czy budżet może JUŻ brać SUMY z Projektów?

**Technicznie tak, z trzema warunkami** (bez nich to fikcja):
1. Sumy istnieją i są policzone: `data/kanoniczne.json` / `pulpit/dane.js` (marże, koszty, przychody,
   nierozliczone 769,8 tys., strefy). Format JSON — łatwy do konsumpcji.
2. ⚠️ Świeżość: eksport ręczny z 2026-06-11, odświeżany komendą `./aktualizuj.sh` — brak automatu (D7/API).
3. ⚠️ Uzgodnienie: sumy projektowe ≠ księgi (pkt 1: 10,5 vs 26,1 mln kosztów). Budżet może brać
   z Projektów WYŁĄCZNIE miary, których weryfikator nie ma (marża projektowa, nierozliczone, normy),
   a nie „koszty firmy" — te musi brać z własnej ścieżki.

## 5. Sekcja E prompta — zgodność źródeł (część weryfikowalna tutaj)

- **E1: ścieżki RÓWNOLEGŁE — potwierdzone ryzyko.** Budżet czyta Firmao live (backend), Projekty czytają
  ręczne eksporty XLSX. Ta sama wielkość (np. przychód czerwca) będzie się różnić o (a) moment zrzutu,
  (b) definicję (faktury vs transakcje vs agregaty — pkt 1). Wymagany „mostek uzgodnienia": jedna tabela
  różnic publikowana na obu pulpitach albo wspólna warstwa pobrań.
- **E2 `closedThrough`:** w Projektach nie istnieje; jest odpowiednik koncepcyjny — `lag.dni_wykluczenia_ze_strat: 30`
  w `konfiguracja/progi.yaml` (świeżo zakończone poza rankingiem strat). Semantyka INNA niż closedThrough
  (księgowe zamknięcie vs ochrona przed lagiem faktur) — nie mylić i nie sklejać bez decyzji.
- **E3 data importu:** w Projektach `DATA_ZRZUTU` zaszyta w `etl/metryki.py` (wyświetlana w nagłówku pulpitu).
  Do paska stanu danych p16 nadaje się dopiero po przeniesieniu do konfiguracji/automatu.

## 6. Werdykt

| Obszar | Status | Dowód | Ryzyko / brak |
|---|---|---|---|
| Granica budżet↔Projekty (§7 p16) | ✅ zgodna z danymi | koszty projektowe = 3,4 mln z 26,1 mln faktur; 40% kosztów w projektach | — |
| Lampka 7 (kadra) jako sygnał + drill | ⚠️ | utylizacja/rzetelność już liczone; pełna utylizacja wymaga D1+D5+pojemności | drill istnieje (pulpit Projekty), ale bez routingu URL per projekt |
| Lampka 8 (marża) jako sygnał + drill | ⚠️ | marża per projekt liczona (685 szt.), per technologia możliwa | to marża pokrycia, nie netto (D3, K1/K2) — nazwać uczciwie |
| „Budżet bierze SUMY z Projektów" | ⚠️ | JSON gotowy (`data/kanoniczne.json`) | ręczna świeżość; zakaz brania „kosztów firmy" z Projektów |
| Zgodność źródeł budżet vs Projekty | ❌ dziś brak uzgodnienia | 26,6 vs 45,3 vs 20,5 mln przychodu w trzech miejscach | mostek uzgodnienia do zaprojektowania |
| Sekcje A/B/C/E-backend prompta | NIE ZWERYFIKOWANE | brak repo budżetu tutaj | uruchomić ten prompt w repo budżetu |

### Propozycje do koncepcji p16 (propozycje — koncepcji nie zmieniam)

1. **§7, wiersz „Projekty":** doprecyzować, że budżet konsumuje z Projektów wyłącznie miary nieksięgowe
   (marża projektowa I stopnia, nierozliczone, normy, utylizacja-sygnał) — bo w danych koszty projektowe
   to tylko ~40% kosztów firmy i suma z Projektów nigdy nie uzgodni się z K1/K2/K3.
2. **Lampka 8:** nazwać „marża pokrycia projektów vs założenia" do czasu domknięcia D3+K1/K2 —
   bo w danych nie ma dziś pełnego kosztu robocizny w projektach.
3. **Dodać do §9 (otwarte):** „mostek uzgodnienia" — jedna publikowana tabelka: przychód/koszty wg
   weryfikatora vs wg Firmao-live vs wg Projektów + wyjaśnione różnice. Sygnał nie ginie ↔ liczby się nie rozjeżdżają.
4. **Punkt styku technicznie:** drill z lampek 7/8 wymaga w pulpicie Projekty routingu URL
   (`#/projekt/1041`) — dziś karta otwiera się klikiem, bez adresu. Jedno-godzinna zmiana, zapisać
   jako wymaganie na Fazę 4 p16, nie robić teraz.
5. **Nierozliczone (769,8 tys. luki przychodu na zakończonych)** — rozważyć jako 9. lampkę deski
   albo składnik lampki „Gotówka": to największa pojedyncza dźwignia gotówkowa widoczna w danych,
   a nie łapie jej ani budżet (patrzy na agregat), ani weryfikator (patrzy wstecz).

### Minimalna lista PRZED Fazą 1 deski (od strony styku z Projektami, wg blokowania)

1. Uruchomić ten sam prompt audytowy w **repo budżetu** (sekcje A/B/C/E — tu niewykonalne).
2. Decyzja właściciela: skąd lampki 2/3 biorą wykonanie (backend budżetu — rekomendowane) i zapis
   w koncepcji zakazu drugiej ścieżki przez eksporty Projektów.
3. Słownik Firmao (K2/P4): co dokładnie zawiera `actualIncomeSummaryNetto` vs `saleTransactionNetto` —
   bez tego rozjazd 45,3 vs 20,5 mln pozostaje niewyjaśniony (pytanie do Firmao/supportu).
4. Ujednolicenie kategorii na fakturach: 24% faktur PURCHASE bez `custom14`, dwie pisownie
   „administracyjne" — psuje K1/K2/K3 budżetu niezależnie od Projektów.

### Pytania do właściciela

- P-A: Czy budżetowe drzewo K1/K2/K3 jest budowane ze słownika `custom14/custom9` z faktur Firmao,
  czy z niezależnego planu kont biura? (rozstrzyga naturę „sieroty Koszty projektowe")
- P-B: Który agregat Firmao jest dla Ciebie „przychodem projektu": faktury sprzedaży przypięte do projektu,
  transakcje projektowe (`saleTransaction`), czy `actualIncomeSummary`? (dziś trzy różne liczby)
- P-C: Czy marża pokrycia (bez pełnej robocizny) wystarcza dla lampki 8 na start?
- P-D: Czy „Nierozliczone" ma wejść na deskę budżetu (propozycja 5), czy zostaje tylko w Projektach?
