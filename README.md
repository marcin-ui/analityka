# Pulpit zarządczy — Projekty (Firmao)

Moduł "Projekty" pulpitu dyrektorskiego: plan vs wykonanie, jakość kalkulacji,
anomalie, pętla PDCA. Zasilany eksportami XLSX z Firmao i raportami czasu pracy
z aplikacji brygad. **Wzorzec architektury** dla kolejnych modułów.

## Uruchomienie

```bash
./aktualizuj.sh          # przelicza wszystko (ETL -> metryki -> pulpit/dane.js)
# potem otwórz pulpit/index.html w przeglądarce (działa z pliku, bez serwera)
```

Wymagania: Python 3 + `pandas`, `openpyxl`, `pyyaml` (`pip install pandas openpyxl pyyaml`).

## Architektura — dane płyną tylko w górę

```
SUROWE (read-only)          KANONICZNE                METRYKI              PULPIT
*.xlsx (Firmao)      ->     data/kanoniczne.json  ->  pulpit/dane.js  ->   pulpit/index.html
dane_czas_pracy/*.xlsx      (Karta Projektu           (czyste funkcje,     (tylko wyświetla,
                             per projekt +             progi z              zero liczenia)
                             filtr anomalii)           konfiguracja/)
     etl/kanoniczne.py           etl/metryki.py
```

Zasady: źródła nigdy nie są modyfikowane; każda liczba na pulpicie jest
audytowalna (drill-down do rekordów); braki danych pokazujemy wprost
(zero atrap); progi i słowniki w `konfiguracja/*.yaml` — edycja bez kodu.

## Struktura katalogów

| Ścieżka | Co to |
|---|---|
| `*.xlsx` | eksporty z Firmao (projekty, oferty, faktury, klienci…) — READ ONLY |
| `dane_czas_pracy/` | raporty czasu pracy z aplikacji brygad (Start/Stop) |
| `etl/kanoniczne.py` | moduł 1: surowe → Karty Projektów + filtr anomalii czasu |
| `etl/metryki.py` | moduł 2: karty → metryki pulpitu (strefy, trend, dźwignia…) |
| `konfiguracja/progi.yaml` | progi stref, filtr anomalii, lag — edytowalne |
| `konfiguracja/slowniki.yaml` | zadania nieprodukcyjne, brygady (D5), stawki (D3) |
| `data/kanoniczne.json` | warstwa kanoniczna (generowana) |
| `data/ODRZUCONE.md` | rejestr wpisów czasu odrzuconych przez filtr (generowany) |
| `pulpit/` | dashboard (index.html + dane.js) |
| `makieta/` | zatwierdzona makieta wizualna (referencja) |
| `AUDYT_DANYCH.md` | Faza 0: pełny audyt danych, luki K1–K6, pytania P1–P8 |
| `ZALOZENIA_DASHBOARD.md` | założenia, model JSON, decyzje D1–D7 |
| `INSTRUKCJA_API_FIRMAO.md` | jak podłączyć API Firmao (krok po kroku) |

## Jak dodać nowe źródło danych (wzorzec)

1. Wrzuć eksport do repo (albo do nowego katalogu `dane_*/`).
2. W `etl/kanoniczne.py` dopisz funkcję `wczytaj_<zrodlo>()` i doklej pola
   do Karty Projektu (klucz: `id` projektu Firmao).
3. Jeśli potrzebna nowa metryka — dopisz ją w `etl/metryki.py` (czysta funkcja).
4. Sekcję UI dodaj w `pulpit/index.html` (renderer czyta gotowe liczby z `dane.js`).
5. `./aktualizuj.sh`. Nic poniżej warstwy, którą zmieniasz, nie wymaga dotykania.

## Braki blokujące kolejne sekcje (stan: patrz zakładka „Jakość danych")

D1 daty w eksporcie aplikacji · D2 plan ilości+godzin w Firmao · D3 stawki
(slowniki.yaml) · D5 mapowanie brygad (slowniki.yaml) · K1 faktury→projekt ·
K2 słownik pól custom · D7 API Firmao (INSTRUKCJA_API_FIRMAO.md).
