# AUDYT DANYCH — Faza 0
### Pulpit Zarządczy: Projekty (Firmao)

**Data audytu:** 2026-07-02
**Zakres:** 9 plików XLSX w katalogu roboczym (eksporty z Firmao, commit „Dane Firmao").
**Zasada:** dane źródłowe nie zostały zmodyfikowane — audyt wykonany wyłącznie na odczycie.

---

## A) INWENTARYZACJA

| Plik | Rozmiar | Wierszy | Kolumn | Zakres dat | Co zawiera (1 zdanie) |
|---|---|---|---|---|---|
| `Projekty_wszystkie.xlsx` | 759 KB | 1 138 | 170 | start 04.2021 – 06.2026 | Wszystkie projekty z agregatami plan/real (koszty, przychody, zysk) liczonymi przez Firmao + ~60 pól niestandardowych. |
| `Projekty_nieZerowe.xlsx` | 260 KB | 375 | 171 | j.w. | **Ścisły podzbiór** powyższego (każde ID występuje w „wszystkie") — do potwierdzenia kryterium selekcji, prawdopodobnie zbędny. |
| `Oferty.xlsx` | 5,9 MB | 9 673 | 140 | 04.2021 – 06.2026 | Oferty (5 187) i zlecenia (4 486), sprzedażowe i zakupowe, z **kluczem `project.id`**, statusem, osobą wystawiającą i wartościami. |
| `Faktury.xlsx` | 5,1 MB | 10 100 | 191 | 04.2021 – 12.2026* | Dokumenty księgowe: **8 600 zakupowych** (26,1 mln netto) i 1 500 sprzedażowych (26,6 mln netto), z firmowym słownikiem kategorii kosztów w polach custom. |
| `Klienci.xlsx` | 2,8 MB | 5 728 | 141 | 04.2021 – 06.2026 | Kartoteka firm z obrotami, saldami i datami ostatniego kontaktu/zamówienia. |
| `Kontakty.xlsx` | 1,0 MB | 5 606 | 65 | 04.2021 – 06.2026 | Osoby kontaktowe (telefony, maile, liczniki aktywności); 1 zduplikowane ID. |
| `Notatki.xlsx` | 1,1 MB | 4 558 | 73 | 04.2021 – 06.2026 | Notatki handlowe/projektowe; 629 powiązanych z projektem (`project.id`). |
| `Maile.xlsx` | 9,6 MB | 63 265 | 67 | 04.2021 – 06.2026 | Korespondencja (56 tys. odebranych / 7 tys. wysłanych), powiązana z klientem; bez powiązania z projektem. |
| `Produkty_magazyn.xlsx` | 814 KB | 2 161 | 118 | 04.2021 – 06.2026 | Katalog produktów ze stanami magazynowymi i cennikami; bez powiązania z projektami. |

\* Faktury z datami do grudnia 2026 to zaplanowane płatności podatkowe wpisane z wyprzedzeniem (dokumenty wewnętrzne, `name` = „podatek grudzień 2026" itp.).

**Świeżość danych:** zrzut z ~11.06.2026. W eksporcie jest tylko **8 projektów o statusie „Otwarty"** — dane są niemal w całości historyczne. Alerty „interweniuj TERAZ" wymagają świeżego zasilania (Faza 4).

---

## B) OCENA STRUKTURY

### B1. `Projekty_wszystkie.xlsx` — plik centralny ⭐

- **Klucz:** `id` (unikalny, 0 duplikatów). Klucze obce: `customer.id` (99,6%), `contact.id` (96%), `createdBy.id` (100%).
- **Agregaty finansowe Firmao (wypełnione w 100%, typ float):**
  - PLAN: `plannedCostSummaryNetto/Brutto`, `plannedIncomeSummaryNetto`, `plannedProfitSummaryNetto`
  - REAL: `actualCostSummaryNetto`, `actualIncomeSummaryNetto`, `actualProfitSummaryNetto`, `purchaseTransactionNetto`, `saleTransactionNetto`
  - pomocnicze: `costRealizationPercent`, `incomeRealizationPercent`, `transactionsBalanceNetto`
  - Uwaga: „wypełnione w 100%" ≠ „niezerowe" — patrz sekcja E.
- **Czas pracy:** `actualWorkHours` (65,5% wypełnione), `estimatedHours` (64,8%), ale `hourlyRate` **pusty w 99,8%** → robocizny nie da się wycenić bez cennika stawek.
- **Daty:** `startDate` 98,4%, `endDate` 99,4%, `creationDate` 100%.
- **Status:** `projectStatus.label`: Zakończony 930, Zakończony i ROZLICZONY 200, Otwarty 8. **Niespójność:** wszystkie 200 „Zakończony i ROZLICZONY" ma `completed=False` — status tekstowy jest wiarygodniejszy niż flaga.
- **Osoby:** `createdBy.label` — 7 kont (KP- D P: 782, KP- S A: 231, wsparcie - Marta: 109, Marcin: 13, inne: 3).
- **Pola niestandardowe (~60 kolumn) — tu prawdopodobnie siedzi kalkulacja, ale eksport nie zawiera ich nazw** (tylko `custom1`…`custom97`). Ustalenia z próbkowania i testów numerycznych:

| Pole | Wypełnienie | Zawartość (obserwacja) | Hipoteza |
|---|---|---|---|
| `customFields.custom2` | 85% | „KUBATUROWE - Garaże i parkingi", „PRZEMYSŁ - Hala produkcyjna"… (15 wartości) | **Typ/kategoria projektu** ✓ |
| `customFields.custom11` | 69% | „Powłoka żywiczna do 2,0 mm", „Impregnacja bezpowłokowa"… (19 wartości) | **Technologia / zakres prac** ✓ |
| `customFields.custom9` | 77% | obiekty osób: „Jakub Siedlecki", „Kamil Geborys"… | Kierownik/brygadzista? **kalkulujący?** — DO POTWIERDZENIA |
| `customFields.custom12` / `customTypes.custom50` | 86% / 61% | kwoty; custom12 == custom50 w 542/589; custom50 ≈ `saleTransactionNetto` (±5% w 555/586 przypadków) | **Wartość sprzedaży/umowy netto** (prawie pewne) |
| `customTypes.custom52` | 48% | kwoty, mediana 4 260 zł | Koszt łączny z rozliczenia? — suma pól poniżej NIE zgadza się z nim (mediana ilorazu 1,24) |
| `customTypes.custom56–61, 64, 65` | ~45% | kwoty o różnych skalach (np. c57 mediana 220 zł, c56 mediana 1 974 zł) | **Rozbicie kosztów per kategoria** (materiały? robocizna? dojazd? noclegi?) — ZNACZENIA NIEZNANE |
| `customTypes.custom62` | 45% | liczby 21–79 | Nie jest to marża % (test: zgodność tylko 12/508); godziny? dni? — NIEZNANE |
| `customTypes.custom90` | 9% | „Przekroczenie DOJAZD; Przekroczenie CZAS; Przekroczenie KOSZTY MAT;…" | **Ręczna klasyfikacja przekroczeń** — cenne dla PDCA ✓ |
| `customTypes.custom92` | 4% | „OK", „zysk PONIŻEJ minimum", „KRYTYCZNE - STRATA na proj" | Ręczna ocena wyniku ✓ |
| `customTypes.custom88` | 5% | „OK - zakończone w terminie", „NOK - przeciągnięte: złe założenia"… | Ocena terminowości ✓ |
| `customFields.custom5/14/15/16`, `custom3/6/7`, `customTypes.custom89/96` | różne | daty ISO | Daty procesowe (umowa? odbiór? rozliczenie?) — NIEZNANE |
| `rok`, `rok_miesiąc` | 99% | 2021–2026 | **Kolumny dopisane ręcznie do eksportu** (nie ma ich w Firmao) — dowód, że plik był już obrabiany |

- **Braki jakościowe:** wartości testowe/śmieciowe w polach opisowych („asjohdns…", „bgfb jcbiohdb…"), niespójne booleany (`true` / `'true'` / `false` jako tekst), `tags`/`managers`/`teamMembers` puste w 100%.

### B2. `Oferty.xlsx`

- **Klucz:** `id` unikalny. **`project.id` wypełnione w 57,3%** (5 543 wierszy) i pokrywa **1 111 z 1 138 projektów (97,6%)** — to najlepszy łącznik oferta→projekt.
- `type`: OFFER 5 187 / ORDER 4 486; `mode`: SALE 7 422 / **PURCHASE 2 251** (zamówienia zakupowe też tu są).
- `offerStatus.label`: Zrealizowana 5 351, Odrzucona 2 921, Robocza 462, Nowa 393, Wysłana 392, pozostałe <100.
- `issuingPerson` (100%): Damian Przyklenk 5 490, Sebastian Adamczyk 2 589, Marta Kasperoszek 899, pozostali <300 — **kandydat na „kto kalkulował"**.
- Wartości: `baseNettoPrice`, `profit` (wypełnione w 100%). Braki: `contact.id` 35%, `mail.id` 58%.

### B3. `Faktury.xlsx`

- **Klucz:** `id` unikalny; `customer.id` 90%.
- **`mode`: PURCHASE 8 600 (26,1 mln netto) / SALE 1 500 (26,6 mln netto)** — to głównie rejestr KOSZTÓW.
- `type`: INVOICE 8 004, INTERNAL_EVIDENCE 1 438, BILL 261, RECEIPT 214, ADVANCE_INVOICE 82, CORRECTION 81, PROFORMA 14.
- **KRYTYCZNE: brak jakiejkolwiek kolumny `project.*`** — faktur nie da się z tego eksportu przypisać do projektów (jest tylko `task.id` w 3,5%).
- **Jest firmowy słownik kategorii kosztów** (pola custom, wypełnione dla 76% faktur zakupowych):
  - `customFields.custom14` (kategoria główna): Koszty projektowe 1 979, Koszty pracowników 991, Koszty utrzymania samochodów 972, Koszty administracyjne 732+92 (dwie pisownie!), Koszty utrzymania 678, Zakupy magazynowe 440, Utrzymanie maszyn i narzędzi 315, inne 151, Marketing 116, Podatki 58.
  - `customFields.custom9` (podkategoria, 115 wartości): „…noclegi/hotele" 601, „…diety/delegacje" 363, „…opłaty drogowe" 283, „…drobne mat. pomocnicze" 197, „…usługi PODWYKONAWCÓW" 26, „…usługi transportowe" 6, itd.
  - 2 076 faktur zakupowych (24%) **bez kategorii**.
- Płatności: `paid`, `paymentStatus`, `actualPaymentDate` — komplet do analizy płynności (poza zakresem tego modułu, przyda się w kontrolingu).

### B4. Pliki wspierające

| Plik | Klucz | Łączniki | Ocena |
|---|---|---|---|
| `Klienci.xlsx` | `id` unikalny | — | OK; do metryczki klienta (nazwa, grupa). |
| `Kontakty.xlsx` | `id` (1 duplikat) | `customer` przez pola relacji | Drugorzędny dla pulpitu. |
| `Notatki.xlsx` | `id` unikalny | `project.id` 629/4 558, `customer.id`, `offer.id` | Przyda się do drill-down (historia decyzji na karcie projektu). |
| `Maile.xlsx` | `id` unikalny | `customer.id` 43% | Bez powiązania z projektem — nieużyteczny dla tego modułu. |
| `Produkty_magazyn.xlsx` | `id` unikalny | brak łącznika do projektów | Nieużyteczny bez pozycji dokumentów (RW/WZ per projekt). |

### B5. Mapa kluczy łączących (co z czym się spina)

```
Projekt (id) ←── Oferta/Zlecenie (project.id)      97,6% projektów ma ofertę ✓
Projekt (id) ←── Notatka (project.id)              629 notatek ✓
Projekt (customer.id) ──→ Klient (id)              99,6% ✓
Oferta (customer.id) ──→ Klient (id)               99,5% ✓
Faktura ──→ Projekt                                ✗ BRAK (luka krytyczna K1)
Faktura (customer.id) ──→ Klient (id)              90% ✓ (łączenie przez klienta
                                                    jest niejednoznaczne przy >1 projekcie klienta)
Produkt/magazyn ──→ Projekt                        ✗ BRAK
```

---

## C) MAPA POKRYCIA względem modelu „Karta Projektu"

Jakość: **OK** = jest i nadaje się wprost; **CZĘŚCIOWE** = jest, ale z lukami/do potwierdzenia; **BRAK** = nie ma w danych.

### Metryczka

| Pole modelu | Mamy? | Gdzie | Jakość |
|---|---|---|---|
| ID projektu | TAK | Projekty: `id` | OK |
| ID oferty źródłowej | TAK | Oferty: `project.id` (odwrotna relacja) | OK (97,6%; bywa >1 oferta na projekt — trzeba wybrać zrealizowaną) |
| Klient | TAK | Projekty: `customer.id/label` | OK (99,6%) |
| Rodzaj obiektu / kategoria | TAK | Projekty: `customFields.custom2` | CZĘŚCIOWE (85%, wymaga potwierdzenia nazwy pola) |
| Zakres prac / technologia | TAK | Projekty: `customFields.custom11` | CZĘŚCIOWE (69%) |
| Kto kalkulował | NIEJASNE | Oferty: `issuingPerson` (100%) lub Projekty: `createdBy` / `custom9` | CZĘŚCIOWE — decyzja słownikowa (pytanie P2) |
| Data oferty | TAK | Oferty: `offerDate` | OK |
| Data umowy | NIEJASNE | prawdopodobnie któraś z dat custom (custom5/14?) | CZĘŚCIOWE — pytanie P6 |
| Data startu | TAK | Projekty: `startDate` | OK (98,4%) |
| Planowana data końca | NIEJASNE | któraś z dat custom (custom7/16?) | CZĘŚCIOWE — pytanie P6 |
| Rzeczywista data końca | TAK | Projekty: `endDate` | OK (99,4%) |
| Status | TAK | Projekty: `projectStatus.label` | OK (uwaga na niespójność z `completed`) |

### Budżet PLAN

| Pole modelu | Mamy? | Gdzie | Jakość |
|---|---|---|---|
| Suma kosztów plan | TAK | Projekty: `plannedCostSummaryNetto` | OK — niezerowe w 790/1 138 (69%) |
| Plan: materiały | ? | prawdopodobnie `customTypes.custom5x` | CZĘŚCIOWE — znaczenie pól nieznane (P4) |
| Plan: towary | ? | j.w. | j.w. |
| Plan: narzędzia/sprzęt | ? | j.w. | j.w. |
| Plan: robocizna (rbh × stawka) | CZĘŚCIOWO | `estimatedHours` (65%); **stawka: BRAK** (`hourlyRate` pusty) | CZĘŚCIOWE → K3 |
| Plan: transport (km × stawka) | NIE | nigdzie nie ma pól km | **BRAK** → K3 |
| Plan: podwykonawcy | ? | `customTypes.custom5x`? | CZĘŚCIOWE (P4) |
| Cena sprzedaży | TAK | `plannedIncomeSummaryNetto` (66% niezerowe) + `custom50/custom12` ≈ wartość umowy | OK/CZĘŚCIOWE |
| Marża plan (PLN, %) | TAK | `plannedProfitSummaryNetto` lub wyliczalna | OK |

### Wykonanie REAL

| Pole modelu | Mamy? | Gdzie | Jakość |
|---|---|---|---|
| Suma kosztów real | TAK | Projekty: `actualCostSummaryNetto` | OK — niezerowe w 985/1 138 (87%) |
| Koszty real per kategoria | NIE wprost | agregat bez rozbicia; kategorie są na fakturach zakupu (`custom14/custom9`), ale **faktury nie mają project.id** | **BRAK** → K1/K2 |
| Robocizna real | CZĘŚCIOWO | `actualWorkHours` (65%); wycena: brak stawek | CZĘŚCIOWE → K3 |
| Przychód real (faktury, korekty) | TAK | Projekty: `actualIncomeSummaryNetto` / `saleTransactionNetto` | OK (93% niezerowe) |
| Marża real (PLN, %) | TAK | `actualProfitSummaryNetto` lub wyliczalna | OK |

### Pochodne

| Pole modelu | Wyliczalne? | Warunek |
|---|---|---|
| CV łączne (PLN, % planu) | TAK | na projektach z plan>0 i real>0 → **685 szt.** |
| CV per kategoria | NIE dziś | wymaga K1 (link faktura→projekt) lub K2 (słownik pól custom) |
| Odchylenie marży (p.p., PLN) | TAK | j.w. 685 szt. |
| CPI | CZĘŚCIOWO | `costRealizationPercent`/`incomeRealizationPercent` istnieją, ale brak fizycznego % zaawansowania → **CPI tylko na projektach zakończonych** (zgodnie z zapisem w specyfikacji); na otwartych — oznaczyć jako brak |

---

## D) BRAKI KRYTYCZNE

| # | Czego brakuje | Skutek dla pulpitu | Skąd wziąć | Wstecz? |
|---|---|---|---|---|
| **K1** | **Powiązanie faktur (zwłaszcza zakupowych) z projektem** | Brak drill-down „koszt real → rekordy źródłowe" (łamie zasadę audytowalności nr 6); brak kosztów real per kategoria z dokumentów | Firmao liczy `purchaseTransactionNetto`/`saleTransactionNetto` per projekt, więc **transakcje projektowe istnieją w systemie** — potrzebny eksport modułu *Transakcje/Dokumenty z kolumną Projekt* albo API (`/transactions` z filtrem projektu) | **TAK** — dane są w Firmao, to wada eksportu, nie procesu |
| **K2** | **Słownik pól niestandardowych** (nazwy `custom50–custom97`, `custom1–custom20`) | Bez niego rozbicie kosztów na kategorie i daty procesowe to zgadywanie — a zasada brzmi: nie zgadujemy | Zrzut z Firmao: *Ustawienia → Pola niestandardowe* (lista: numer pola → etykieta), albo odpowiedź na pytania P4–P6 | **TAK** — natychmiast, to tylko metadane |
| **K3** | **Stawki robocizny i transportu (km)** | Nie da się policzyć planu/realu robocizny i transportu w PLN; godziny są (65%), km nie ma wcale | Cennik wewnętrzny (stawka rbh per rok, stawka km) — plik konfiguracyjny; km: moduł delegacji/pojazdów Firmao albo nowy proces wpisywania | Stawki: **TAK** (jeśli podasz historyczne); km: **tylko od teraz** |
| **K4** | **Fizyczny % zaawansowania projektów otwartych** | CPI i alert „koszt >90% limitu przy <70% zaawansowania" niedostępne dla projektów w toku | Nowe pole w Firmao aktualizowane przez kierowników (proces, Faza 4) | **tylko od teraz** |
| **K5** | **Świeżość danych** — zrzut z 11.06.2026, tylko 8 projektów otwartych | Alerty „interweniuj TERAZ" nie mają na czym pracować | Cykliczny eksport lub API Firmao (Faza 4); **uwaga:** obecne środowisko ma zablokowany ruch do `system.firmao.pl` (proxy 403) — do odblokowania w polityce sieciowej lub uruchamianie skryptu zasilania lokalnie | n/d |
| **K6** | **Kategoryzacja 24% faktur zakupowych** (2 076 szt. bez `custom14`) | Zaniżone koszty w kategoriach nawet po rozwiązaniu K1 | Proces: uzupełnienie wstecz w Firmao lub reguły mapowania po kontrahencie | **TAK, ręcznie** (do wyceny nakładu) |

**Braki niekrytyczne (odnotowane):** duplikat ID w Kontaktach; podwójna pisownia „Koszty administracyjne"/„Koszty adminstracyjne"; niespójne booleany tekstowe; `completed` sprzeczne ze statusem dla 200 projektów; wartości testowe w polach opisowych; kolumny `rok`/`rok_miesiac` dopisane do eksportu ręcznie (przy automatyzacji zasilania wypadną — pochodne będziemy liczyć sami w warstwie kanonicznej).

---

## E) WERDYKT — na czym budujemy pilotaż

**Kohorta pilotażowa: 685 projektów zakończonych z kompletem plan+real** (planowane i rzeczywiste koszty ORAZ przychody > 0; wszystkie mają status Zakończony/Rozliczony):

| Cecha kohorty | Liczba |
|---|---|
| Projekty z kompletem plan+real (koszty i przychody) | **685** |
| — z powiązaną ofertą (`project.id`) | 684 (99,9%) |
| — z typem projektu (`custom2`) | 594 (87%) |
| — z godzinami rzeczywistymi | 352 (51%) |
| — z pełnym rozbiciem kwot custom (potencjalne kategorie kosztów) | 278 (41%) |
| Rozkład wg roku startu | 2021: 5 · 2022: 228 · 2023: 89 · 2024: 87 · 2025: 201 · 2026: 74 |

Sanity-check na kohorcie (dowód, że dane niosą sygnał): odchylenie kosztów real vs plan — mediana **−4,0%**, ale rozstęp międzykwartylowy od **−17,9% do +43,4%** → jest i systematyka, i gruby ogon przekroczeń, czyli dokładnie to, co pulpit ma wyławiać.

**Co działa od razu (bez uzupełniania braków):**
- poziom portfela: marża plan vs real, strefy zielona/żółta/czerwona, top utraconej marży, trend błędu kalkulacji (miesięcznie, na zakończonych) — **685 projektów, lata 2021–2026**;
- poziom kalkulującego: per `issuingPerson` oferty lub `createdBy` projektu (po decyzji P2);
- per typ projektu: na 594 projektach z `custom2`.

**Co wymaga decyzji/braków przed budową:**
- rozbicie plan/real na kategorie kosztów → K1 + K2 (potencjalnie 278 projektów od razu, jeśli pola custom okażą się rozbiciem kosztów);
- robocizna i transport w PLN → K3;
- alerty na projektach żywych → K4 + K5.

**Rekomendacja:** budować Fazę 1–3 na kohorcie 685 projektów z metrykami na poziomie sum (plan/real/marża), z architekturą gotową na doklejenie kategorii kosztów, gdy dostaniemy K1/K2. Drill-down w pierwszej wersji: projekt → oferta/zlecenia + notatki (bez faktur, do czasu K1).

---

## PYTANIA (zbiorczo — do akceptacji Fazy 0)

**P1.** `Projekty_nieZerowe.xlsx` to podzbiór `Projekty_wszystkie.xlsx` (375/375 ID się pokrywa). Jakie było kryterium selekcji i czy mogę ten plik pominąć?

**P2.** Kto jest **„osobą kalkulującą"** w rozumieniu pulpitu: (a) `issuingPerson` z oferty/zlecenia, (b) `createdBy` projektu, (c) osoba z pola `customFields.custom9` projektu (np. „Jakub Siedlecki", „Kamil Geborys")?

**P3.** Czy `customTypes.custom50` (≈ `customFields.custom12`) to **wartość umowy/cena sprzedaży netto**? Test numeryczny: równa się wartości transakcji sprzedaży w 95% przypadków.

**P4.** Co oznaczają pola kwotowe `customTypes.custom52, 56, 57, 58, 59, 60, 61, 64, 65` oraz liczbowe `custom62`? Czy to rozbicie kosztów (plan czy real?) na kategorie: materiały / towary / narzędzia / robocizna / dojazd / noclegi / podwykonawcy / inne? Najszybciej: zrzut ekranu karty dowolnego projektu z widocznymi etykietami pól albo eksport konfiguracji pól niestandardowych.

**P5.** Jakie są **stawki**: roboczogodziny (per rok? per zespół?) i kilometra transportu? Od kiedy obowiązują i czy były zmieniane?

**P6.** Które pola-daty custom w projektach to: data umowy, planowana data końca, data odbioru, data rozliczenia? (kandydaci: `custom3, custom5, custom6, custom7, custom14, custom15, custom16`, `customTypes.custom89/95/96`).

**P7.** Progi stref na start: zielona ≤5%, żółta 5–10%, czerwona >10% odchylenia kosztów — potwierdzasz, czy chcesz inne wartości w `progi.yaml`? Jaka jest minimalna akceptowalna marża projektu (do alertu „marża real < X%")?

**P8.** Czy w Firmao da się wyeksportować **transakcje projektowe / dokumenty z kolumną „Projekt"** (rozwiązanie K1)? Jeśli nie wiesz — mogę przygotować instrukcję sprawdzenia krok po kroku na początku Fazy 1.

---
*Faza 0 zakończona. Nic nie zbudowano, dane źródłowe nietknięte. Czekam na akceptację i odpowiedzi na pytania P1–P8.*
