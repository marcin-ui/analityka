# -*- coding: utf-8 -*-
"""
ETL moduł 2: warstwa kanoniczna -> metryki pulpitu (pulpit/dane.js).

Czyste funkcje na kartach projektów. Frontend niczego nie dolicza —
każda liczba na pulpicie powstaje tutaj i jest audytowalna (drill-down
prowadzi do kart, karty do rekordów źródłowych).
"""
import json, os, statistics, datetime
import yaml

BAZA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROK_BIEZACY = 2026          # rok "YTD" pulpitu (ostatni rok w danych)
DATA_ZRZUTU = "2026-06-11"  # data eksportów z Firmao


def polrocze(data):
    if not data:
        return None
    r, m = int(data[:4]), int(data[5:7])
    return f"{r} H{1 if m <= 6 else 2}"


def mediana(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 1) if xs else None


def licz(karty, progi):
    zakonczone = [k for k in karty if k["status"] in ("zakonczony", "rozliczony")]
    komplet = [k for k in zakonczone if k["pochodne"]["komplet_plan_real"]]
    rok = lambda k: (k["daty"]["koniec"] or "")[:4]

    # ---- kafle W1 ----
    ytd = [k for k in komplet if rok(k) == str(ROK_BIEZACY)]
    mp, mr = sum(k["plan"]["marza"] for k in ytd), sum(k["real"]["marza"] for k in ytd)
    pp, pr = sum(k["plan"]["przychod"] for k in ytd), sum(k["real"]["przychod"] for k in ytd)
    marza_ytd = {"n": len(ytd), "plan": round(mp), "real": round(mr),
                 "plan_pct": round(100 * mp / pp, 1) if pp else None,
                 "real_pct": round(100 * mr / pr, 1) if pr else None,
                 "delta": round(mr - mp)}

    def strefy(zbior):
        s = {"zielona": 0, "zolta": 0, "czerwona": 0}
        for k in zbior:
            if k["pochodne"]["strefa"]:
                s[k["pochodne"]["strefa"]] += 1
        return s

    # ranking strat 2025-26, bez świeżo zakończonych nierozliczonych (lag)
    limit_lagu = (datetime.date.fromisoformat(DATA_ZRZUTU)
                  - datetime.timedelta(days=progi["lag"]["dni_wykluczenia_ze_strat"])).isoformat()
    swieze = [k for k in komplet if rok(k) in ("2025", "2026")]
    ranking = [k for k in swieze
               if k["status"] == "rozliczony" or (k["daty"]["koniec"] or "") <= limit_lagu]
    wykluczone_lagiem = len(swieze) - len(ranking)
    straty = sorted(ranking, key=lambda k: k["pochodne"]["utrata_marzy"])
    top5 = straty[:5]
    ogon = [k for k in straty[5:] if k["pochodne"]["utrata_marzy"] < 0]

    # kafel Nierozliczone (dźwignia gotówkowa)
    bez_prz = [k for k in karty if k["rozliczenia"]["bez_przychodu"]]
    niedof = [k for k in karty if k["rozliczenia"]["niedofakturowany"]]
    nierozliczone = {
        "bez_przychodu_n": len(bez_prz),
        "bez_przychodu_koszty": round(sum(k["real"]["koszty"] for k in bez_prz)),
        "niedofakturowane_n": len(niedof),
        "luka_przychodu": round(sum(k["rozliczenia"]["luka_przychodu"] for k in niedof)),
        "zakonczone_nierozliczone_n": sum(1 for k in karty if k["status"] == "zakonczony"),
    }

    # trend błędu kalkulacji (wskaźnik Deminga)
    trend = {}
    for k in komplet:
        o = polrocze(k["daty"]["koniec"])
        if o:
            trend.setdefault(o, []).append(abs(k["pochodne"]["odchylenie_kosztow_pct"]))
    od = progi["trend"]["od_okresu"]
    trend = [{"okres": o, "blad_pct": mediana(v)}
             for o, v in sorted(trend.items()) if o >= od]

    # ---- dźwignia ----
    def grupuj(zbior, klucz):
        g = {}
        for k in zbior:
            g.setdefault(klucz(k), []).append(k["pochodne"]["odchylenie_kosztow_pct"])
        wyn = []
        for nazwa, xs in g.items():
            if nazwa and len(xs) >= 15:
                xs = sorted(x for x in xs if x is not None)
                q1, q3 = xs[len(xs) // 4], xs[3 * len(xs) // 4]
                wyn.append({"nazwa": nazwa, "n": len(xs),
                            "mediana_pct": mediana(xs), "iqr": round(q3 - q1, 1)})
        return sorted(wyn, key=lambda x: -(x["mediana_pct"] or 0))

    typy = grupuj(komplet, lambda k: k["typ"])
    kalkulujacy = grupuj(komplet, lambda k: k["kalkulujacy"])

    # normy firmowe: mediana tempa per zadanie ze wszystkich projektów
    normy_zb = {}
    for k in karty:
        if k["czas_pracy"]:
            for nrm in k["czas_pracy"]["normy"]:
                normy_zb.setdefault((nrm["zadanie"], nrm["jednostka"]), []).append(nrm["tempo_na_h"])
    normy_firmowe = [{"zadanie": z, "jednostka": j, "mediana": mediana(t), "n_projektow": len(t)}
                     for (z, j), t in sorted(normy_zb.items()) if len(t) >= 2]

    # utylizacja globalna + marża na rbh (tylko rozliczone/zakończone, uwaga na lag)
    hp = sum(k["czas_pracy"]["h_produkcyjne"] for k in karty if k["czas_pracy"])
    hn = sum(k["czas_pracy"]["h_nieprodukcyjne"] for k in karty if k["czas_pracy"])
    utylizacja = {"produkcyjne_h": round(hp, 1), "nieprodukcyjne_h": round(hn, 1),
                  "produkcyjne_pct": round(100 * hp / (hp + hn)) if hp + hn else None}
    marza_rbh = []
    for k in karty:
        cz = k["czas_pracy"]
        if cz and k["status"] in ("zakonczony", "rozliczony"):
            h = cz["h_produkcyjne"] + cz["h_nieprodukcyjne"]
            if h >= 5:
                marza_rbh.append({"id": k["id"], "nazwa": k["nazwa"][:48], "h": round(h, 1),
                                  "marza": round(k["real"]["marza"]),
                                  "marza_na_h": round(k["real"]["marza"] / h),
                                  "lag_ryzyko": k["status"] != "rozliczony"})
    marza_rbh.sort(key=lambda x: x["marza_na_h"])

    return {
        "meta": {"data_zrzutu": DATA_ZRZUTU, "rok_ytd": ROK_BIEZACY,
                 "wygenerowano": datetime.date.today().isoformat(),
                 "projekty_razem": len(karty), "pilotaz_n": len(komplet),
                 "lag_dni": progi["lag"]["dni_wykluczenia_ze_strat"],
                 "wykluczone_lagiem": wykluczone_lagiem},
        "kafle": {"marza_ytd": marza_ytd, "strefy_ytd": strefy(ytd), "strefy_total": strefy(komplet),
                  "zagrozona": {"top5": round(sum(k["pochodne"]["utrata_marzy"] for k in top5)),
                                "ogon": round(sum(k["pochodne"]["utrata_marzy"] for k in ogon)),
                                "ogon_n": len(ogon)},
                  "nierozliczone": nierozliczone},
        "trend_bledu": trend,
        "dzwignia": {"typy": typy, "kalkulujacy": kalkulujacy,
                     "normy_firmowe": normy_firmowe, "utylizacja": utylizacja,
                     "marza_rbh": marza_rbh},
        "top5_ids": [k["id"] for k in top5],
    }


def main():
    with open(f"{BAZA}/konfiguracja/progi.yaml", encoding="utf-8") as f:
        progi = yaml.safe_load(f)
    with open(f"{BAZA}/data/kanoniczne.json", encoding="utf-8") as f:
        kan = json.load(f)

    metryki = licz(kan["karty"], progi)

    # kompaktowa lista do tabeli + pełne karty do drill-down
    lista = [{"id": k["id"], "nazwa": k["nazwa"], "status": k["status"],
              "typ": k["typ"], "kalkulujacy": k["kalkulujacy"],
              "rok": (k["daty"]["koniec"] or "")[:4] or None,
              "marza_plan": round(k["plan"]["marza"]), "marza_real": round(k["real"]["marza"]),
              "utrata": round(k["pochodne"]["utrata_marzy"]),
              "odch": k["pochodne"]["odchylenie_kosztow_pct"],
              "strefa": k["pochodne"]["strefa"],
              "komplet": k["pochodne"]["komplet_plan_real"],
              "ma_czas": k["czas_pracy"] is not None}
             for k in kan["karty"]]

    dane = {"metryki": metryki, "lista": lista,
            "karty": {str(k["id"]): k for k in kan["karty"]},
            "rzetelnosc_osob": kan["rzetelnosc_osob"],
            "progi": progi}
    js = "window.DANE = " + json.dumps(dane, ensure_ascii=False) + ";"
    with open(f"{BAZA}/pulpit/dane.js", "w", encoding="utf-8") as f:
        f.write(js)
    print(f"pulpit/dane.js: {len(js)//1024} KB | projektów: {len(lista)} "
          f"| pilotaż: {metryki['meta']['pilotaz_n']}")


if __name__ == "__main__":
    main()
