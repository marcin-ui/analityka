# ZAŁOŻENIA — CEO Dashboard z trzema filarami danych
### Analiza raportu czasu pracy brygad (Filar C) + weryfikacja koncepcji + architektura

**Data:** 2026-07-06 · **Wejście:** plik `Projekt_1232_...xlsx` (aplikacja Start/Stop brygad) + koncepcja z równoległego czatu + wyniki Fazy 0 (`AUDYT_DANYCH.md`).

---

## 1. Co jest w pliku z aplikacji brygad (Filar C) — fakty

Struktura: raport hierarchiczny **Projekt → Zadanie → Osoba**, 326 wierszy:

| Cecha | Wartość |
|---|---|
| Projektów | **19** (nie 1 — plik obejmuje ID 1205–1232) |
| Osób | 10 (m.in. Denis Przyklenk, Jakub Młynarczyk, Mateusz Świerzy…) |
| Typów zadań | 26 (produkcyjne: nacinanie, frezowanie, szlifowanie…; nieprodukcyjne: dojazd, przerwy, sprzątanie, zabezpieczenie) |
| Metryki produkcyjne | „Pozycja zadania" + „Wartość": **metry bieżące, metry kwadratowe, kilometry** |
| Suma zarejestrowanych godzin | 3 680,5 h |

### 1a. KLUCZOWE ODKRYCIE — mamy twardy klucz łączący 🔑

Numer przed dwukropkiem w nazwie projektu w aplikacji (**„1220 : ATAL odwodnienia…"**) to
**`id` projektu z Firmao**. Zweryfikowane: 17/19 projektów z raportu istnieje w zrzucie Firmao
pod dokładnie tym ID (1230 i 1232 są nowsze niż zrzut z 11.06). Filar C łączy się z Filarem B
bez żadnej fuzzy-logiki. To zamyka pytanie „jak powiążesz jednostki z Excela z założeniami z Firmao".

### 1b. Skala szumu — twarde liczby (potwierdzam diagnozę z drugiego czatu, jest GORZEJ niż opisał)

| Problem | Skala | Wniosek |
|---|---|---|
| Wpisy > 12 h (zapomniany STOP) | 32/326 wpisów (10%), ale zawierają **3 144 z 3 680 h = 85% wszystkich godzin!** | Bez filtra anomalii KAŻDA metryka czasu jest śmieciem. Rekordzista: 423,5 h (Obróbka ręczna). |
| Wpisy = 0 h (zapomniany START lub nieużywanie) | **151/326 wpisów (46%)** | Druga strona tego samego problemu — czas jest też ZANIŻANY. Filtr tylko „ucinający górę" da fałszywie dobre normy. |
| Kolumny „Zakładany czas" | puste/0 w 100% | Normy nie są wpisywane w aplikacji — plan musi przyjść z Firmao (Filar B). |
| Brak dat/timestampów w eksporcie | 0 kolumn z datą | **BLOKER dla „codziennej dawki"**: bez znaczników czasu nie ma dziennego przyrostu, trendu tempa ani run-rate w czasie. Aplikacja te dane MA (liczy start/stop) — trzeba zmienić format eksportu. |
| „Wartość" (metry/km) na poziomie zadania, powielona w wierszach osób | 100% zadań | Sumowanie po wierszach podwoi/potroi produkcję. Liczyć: wartość MAX per (projekt, zadanie), czas SUM per (projekt, zadanie). |
| Brak pojęcia „brygada" | tylko osoby | Utylizację per brygada trzeba zbudować przez słownik osoba→brygada (konfiguracja). |

### 1c. Dowód, że po oczyszczeniu dane niosą sygnał

Na wpisach ≤ 12 h (536 h „czystych"):
- **Utylizacja:** dojazd + przerwy + sprzątanie + zabezpieczenie = **48% czasu czystego** (sam dojazd ~213 h brutto). To jest realna dźwignia — połowa opłaconego czasu nie wytwarza metrów.
- **Normy real są policzalne i mają rozrzut**, np. „Nacinanie odwodnień": 16,3 mb/h (proj. 1226), 16,5 (1228), 19,6 (1227), 60,1 (1205 — podejrzane). Dojazdy: 15–180 km/h (auta — sensowne 60–100, reszta to artefakty braku STOP/START).
- Wniosek: filtr anomalii musi mieć TRZY warstwy (patrz §3), bo samo „utnij >12h" przepuszcza normy zawyżone przez zaniżony czas.

---

## 2. Weryfikacja koncepcji z równoległego czatu — co zostaje, co koryguję

| Element koncepcji | Werdykt | Uzasadnienie na danych |
|---|---|---|
| Układ: Marża Portfela / Pas Projektów / Top 5 / Brygady / PDCA | ✅ zostaje | Spójny z Fazą 2–3 z naszej specyfikacji. |
| Filtr anomalii jako warstwa pośrednia | ✅ zostaje, rozszerzam | Musi łapać też zera (46% wpisów) i normy-outliery, nie tylko >12 h. Patrz §3. |
| „Błąd rzetelności brygady" | ✅ + doprecyzowanie | Liczymy per OSOBA (bo tak są dane), agregujemy do brygady po słowniku. Wskaźnik: % wpisów poprawnych. |
| Run-Rate / prognozowana strata | ✅ zostaje, z 2 warunkami | Wymaga: (a) planu ilości — dziś tylko w NAZWIE projektu („220mb", „1000mb" — parsowalne, docelowo pole custom w Firmao); (b) planu godzin — `estimatedHours` w Firmao jest PUSTE dla wszystkich 17 dopasowanych projektów. Bez wymuszenia tych 2 pól run-rate nie ruszy. → „minimalny standard danych" (Faza 4) staje się warunkiem, nie opcją. |
| „Główny widok twardo ucina do Top 5" | ⚠️ korekta | Top 5 na Warstwie 1 TAK, ale obok kafel „pozostałe N projektów: −X zł łącznie". Przy 150+ projektach ogon poza Top 5 potrafi krwawić więcej niż Top 5 — ucięcie bez sumy ogona to ślepa plamka. Pełna lista na Warstwie 2. |
| Routing czerwony projekt → analityka z filtrem ID | ✅ zostaje | Klucz = `firmao_id` (potwierdzony w §1a). Trasa `/projekt/:firmaoId`. |
| PDCA związane z ID projektu Firmao | ✅ zostaje | j.w. |
| Model JSON + komponenty React | ✅ z korektą architektury | Zgodnie z zasadami: metryki liczy silnik (Faza 2, czyste funkcje), frontend TYLKO wyświetla. Żadnej logiki liczącej w komponentach. |

**Czego koncepcja z drugiego czatu nie widziała (bo nie zna Fazy 0):**
1. Koszty real per kategoria per projekt są dziś niepoliczalne z eksportów (luka K1: faktury bez `project.id`) — run-rate policzy zagrożenie na ROBOCIŹNIE, ale „pełna prognoza straty projektu" potrzebuje jeszcze K1/K2.
2. Stawki rbh i km nie istnieją w danych (K3) — bez nich prognoza straty będzie w GODZINACH, nie w PLN. Potrzebny cennik (1 tabelka konfiguracyjna).
3. Zrzut Firmao jest z 11.06 i ma tylko 8 projektów otwartych — pulpit „na dziś" wymaga świeżego zasilania (API albo cykliczny eksport).

---

## 3. Warstwa czyszcząca (Filar C → dane kanoniczne) — koncepcja

Zasada: **niczego nie kasujemy** — każdy wpis dostaje status i trafia albo do metryk, albo do rejestru
odrzuconych (`ODRZUCONE.md` + tabela `wpisy_odrzucone`). Progi w `progi.yaml`.

```python
# progi.yaml (fragment):
#   max_godzin_wpisu: 12         # dłuższy wpis = zapomniany STOP
#   min_godzin_przy_produkcji: 0.1  # 0h przy wykonanych metrach = zapomniany START
#   norma_outlier_mnoznik: 3     # tempo > 3x mediana firmowa = podejrzane
#   polityka_anomalii: "odrzuc"  # odrzuc | imputuj_mediane | przytnij

def czysc_wpisy_czasu(wpisy, progi, normy_firmowe):
    for w in wpisy:                          # w: projekt_id, zadanie, osoba, godziny
        if w.godziny > progi.max_godzin_wpisu:
            w.status = "ANOMALIA_STOP"       # zapomniany stop → do rejestru rzetelności
        elif w.godziny <= progi.min_godzin_przy_produkcji and w.zadanie.ma_metryke:
            w.status = "ANOMALIA_START"      # 0h a metry wykonane → czas zaniżony
        else:
            w.status = "OK"

    # 2. przelicz normy TYLKO na wpisach OK, per (projekt, zadanie):
    #    czas = SUM(godziny osób OK), produkcja = MAX(wartość)  # wartość jest na poziomie zadania!
    # 3. sito norm: tempo > mnoznik * mediana_firmowa(zadanie) → status "NORMA_PODEJRZANA"
    #    (łapie przypadki typu Trasowanie 415 mb/h — czas zaniżony, nie ucięty)
    # 4. polityka wg progi.yaml:
    #    odrzuc          → anomalie poza metrykami, do rejestru
    #    imputuj_mediane → zastąp medianą czasu tej osoby na tym typie zadania
    #    przytnij        → cap na max_godzin_wpisu (NIE zalecane — fałszuje normy)
    # 5. wskaźnik rzetelności: per osoba i per brygada = % wpisów OK
    #    → osobny kafel jakości danych, NIE do budżetu projektu
```

Efekt na przykładowym pliku: do metryk wchodzi ~536 h z 3 680 h; 32 wpisy „STOP" i ~40–60
podejrzanych zer idzie do raportu rzetelności zamiast niszczyć marże na pulpicie.

---

## 4. Kanoniczny model danych — Karta Projektu (JSON)

Jeden obiekt per projekt, budowany przez ETL z trzech filarów; frontend niczego nie dolicza.

```jsonc
{
  "projekt": {
    "firmao_id": 1220,                        // KLUCZ wszędzie (routing, PDCA, drill-down)
    "nazwa": "ATAL odwodnienia 1000mb Atal Sky Etap 2 Katowice",
    "klient": {"firmao_id": 812, "nazwa": "ATAL S.A."},
    "typ": "odwodnienia",                     // słownik z customFields.custom2 (po potwierdzeniu P4)
    "kalkulujacy": "Damian Przyklenk",        // decyzja P2 (oferta.issuingPerson)
    "status": "w_realizacji",                 // oferta | w_realizacji | zakonczony | rozliczony
    "daty": {"oferta": "…", "umowa": "…", "start": "…", "koniec_plan": "…", "koniec_real": null}
  },
  "plan": {                                    // FILAR B (Firmao)
    "ilosc": {"jednostka": "mb", "wartosc": 1000},
    "godziny": 120,
    "koszty": {"materialy": 0, "towary": 0, "narzedzia": 0, "robocizna": 0,
               "transport": 0, "podwykonawcy": 0, "inne": 0, "suma": 0},
    "cena_sprzedazy": 0,
    "marza": {"pln": 0, "pct": 0}
  },
  "real": {                                    // FILAR A (księgi/weryfikator) + C (czas)
    "koszty": { "...": "te same kategorie; do czasu K1 tylko suma z Firmao" },
    "przychod": 0,
    "godziny": {"produkcyjne": 41.0, "nieprodukcyjne": 12.3, "odrzucone_anomalie": 827.7},
    "marza": {"pln": 0, "pct": 0}
  },
  "progres": {                                 // FILAR C (aplikacja brygad)
    "ilosc_wykonana": 510, "pct": 0.51,
    "stan_na": "2026-07-05",                   // wymaga eksportu z datami!
    "zrodlo": "aplikacja_brygad"
  },
  "run_rate": {                                // silnik metryk (Faza 2), nie wpisywane
    "spalanie_czasu_pct": 0.50,                // zużyte_h / plan_h
    "spalanie_zakresu_pct": 0.20,              // wykonane_mb / plan_mb
    "indeks_tempa": 0.40,                      // zakres/czas; <1 = wolniej niż plan → ALARM
    "eac_godziny": 300,                        // prognoza godzin na koniec = zużyte_h / pct_zakresu
    "prognoza_straty_pln": -14400,             // (eac_h − plan_h) × stawka_rbh (wymaga K3)
    "strefa": "czerwona"
  },
  "normy": [                                   // per zadanie, tylko wpisy OK
    {"zadanie": "Nacinanie odwodnień", "jednostka": "mb/h",
     "plan": 10.0, "real": 16.5, "n_wpisow": 12, "wiarygodnosc": "OK"}
  ],
  "utylizacja": {"produkcyjne_pct": 0.52, "dojazd_pct": 0.31, "przerwy_pct": 0.06, "inne_pct": 0.11},
  "alerty": [
    {"id": "A-1220-03", "regula": "indeks_tempa<0.6", "wartosc": 0.40, "prog": 0.6,
     "wykryto": "2026-07-05", "status": "nowy"}                     // nowy|w_analizie|skorygowany|zaakceptowany
  ],
  "pdca": [
    {"id": "PDCA-17", "projekt_firmao_id": 1220, "faza": "Act",
     "opis": "Korekta normy nacinania z 10 na 15 mb/h w standardzie kalkulacji",
     "wlasciciel": "…", "termin": "…", "status": "otwarte"}
  ],
  "jakosc_danych": {"wpisy_czasu": 14, "odrzucone": 3, "rzetelnosc_pct": 78.6,
                    "braki": ["estimatedHours", "stawka_rbh"]}      // audytowalność braków
}
```

Słowniki w konfiguracji (nie w kodzie): kategorie kosztów, zadania→{produkcyjne|nieprodukcyjne},
osoba→brygada, stawki (rbh, km, per rok), progi stref i alertów (`progi.yaml`).

---

## 5. Struktura komponentów UI (React) — trzy warstwy, zero logiki liczącej

```text
<App>  (router: "/" | "/projekty" | "/projekt/:firmaoId")
│
├── W1  <PulpitCEO>                      // max 7 wskaźników, mobile-first
│   ├── <KafelMarzaYTD  plan real deltaPP/>
│   ├── <PasStref  zielone zolte czerwone onClick→W2(filtr:strefa)/>
│   ├── <KafelZagrozonaMarza  sumaPrognozStrat top5={true} ogon={suma poza Top5}/>
│   ├── <Top5Krwawiacych  rows[5] onRowClick→ /projekt/:id />
│   │      └── <MiniRunRate  spalanieCzasu spalanieZakresu strefa/>   // pasek podwójny
│   ├── <TrendBleduKalkulacji  serieMiesieczne/>                      // wskaźnik Deminga
│   ├── <KafelUtylizacjaTygodnia  produkcyjnePct dojazdPct/>          // NOWE (Filar C)
│   └── <PetlaPDCA  otwarteDzialania[] przeterminowane[]/>            // domykanie Act
│
├── W2  <ListaProjektow>
│   ├── <FiltryBar  status typ kalkulujacy okres strefa/>             // stan w URL (query params)
│   ├── <TabelaProjektow  sort=utracona_marza_desc>
│   │      └── <WierszProjektu>: nazwa | kalkulujący | pasek plan/real |
│   │           indeks tempa | rzetelność danych % | strefa | → /projekt/:id
│   └── <PodsumowanieOgona  liczba suma/>                             // to, czego Top5 nie pokazuje
│
└── W3  <KartaProjektu :firmaoId>                                     // drill-down = audytowalność
    ├── <NaglowekProjektu  metryczka statusBadge/>
    ├── <PlanVsRealKategorie  tabela+paski per kategoria kosztu/>
    ├── <PanelRunRate  eac prognozaStraty wykresTempa/>               // wykres wymaga dat z aplikacji
    ├── <NormyRealVsPlan  perZadanie  podswietlWaskieGardlo/>         // "5 mb/h zamiast 10 mb/h"
    ├── <UtylizacjaBrygad  perOsoba perBrygada  + rzetelnoscWpisow/>
    ├── <HistoriaAlertow  timeline statusy/>
    ├── <NotatkiPDCA  editable  →zapis do pdca[]/>                    // jedyne pole zapisu na UI
    └── <ZrodlaDanych>                                                // klik w liczbę → rekordy
         ├── <WpisyCzasu  wTymOdrzucone flagi/>
         ├── <OfertyZlecenia/>  └── <Faktury/>  // faktury po domknięciu K1
```

Kontrakt: frontend czyta wyłącznie gotowe JSON-y z silnika metryk (statyczne pliki albo cienkie API).
Stack proponowany: Python ETL (już mamy początki) → JSON → React+Vite, bez bazy na starcie
(pliki wystarczą do 150+ projektów), łatwa migracja do SQLite gdy urośnie.

---

## 6. Decyzje potrzebne, żeby ruszyć (w kolejności blokowania)

| # | Decyzja / działanie | Blokuje | Kto |
|---|---|---|---|
| D1 | **Eksport z aplikacji brygad z datami** (start/stop lub choćby dzień) + nazwa eksportu per tydzień | run-rate w czasie, „codzienna dawka", wykres tempa | Ty / dostawca aplikacji |
| D2 | **Plan ilości i plan godzin per projekt w Firmao** (2 pola obowiązkowe przy starcie projektu; ilość jest już w nazwie — można parsować przejściowo) | cały run-rate | standard firmowy (Faza 4, ale trzeba zacząć wpisywać JUŻ) |
| D3 | **Cennik stawek**: rbh (per rok) + km | prognoza straty w PLN, wycena robocizny | Ty (1 tabelka) |
| D4 | **Słownik zadań**: które produkcyjne, które nie (sprzątanie = konieczne czy strata?) | utylizacja | Ty (15 min, jednorazowo) |
| D5 | **Mapowanie osoba→brygada** | widok Brygad | Ty (jednorazowo + aktualizacje) |
| D6 | Odpowiedzi P1–P8 z `AUDYT_DANYCH.md` (zwłaszcza znaczenia pól custom) | rozbicie kosztów plan/real na kategorie | Ty / zrzut ekranu z Firmao |
| D7 | Dostęp API Firmao (`INSTRUKCJA_API_FIRMAO.md`) | świeżość danych, luka K1 | Ty (10 min) |

**Co mogę zbudować od razu, bez czekania na D1–D7:** warstwa czyszcząca + kanoniczny model +
silnik metryk na tym, co jest (marże plan/real na 685 zakończonych, normy real i utylizacja
na 19 projektach z pliku brygad, run-rate z ilością parsowaną z nazw projektów) — z polami
oznaczonymi „brak danych" tam, gdzie czekamy na D-ki. Zgodnie z zasadą: nie budujemy atrap,
ale budujemy szkielet, który D-ki tylko zasilą.

---

## 7. Wizja docelowa: „Claude wpięty do systemu"

Realna ścieżka (Faza 4+): cykliczne zasilanie (API Firmao + eksporty aplikacji brygad) →
warstwa kanoniczna w repo → ja w sesji czytam te same JSON-y co pulpit → omawiamy anomalie,
koryguję normy w konfiguracji, generuję wpisy PDCA, przygotowuję zmiany standardów.
Pulpit pokazuje, ja pomagam decydować — obie rzeczy jedzą z tej samej warstwy danych,
więc nigdy się nie rozjadą.
