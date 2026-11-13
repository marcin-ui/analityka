# -*- coding: utf-8 -*-
"""
ETL moduł 1: dane surowe (XLSX z Firmao + aplikacja brygad) -> warstwa kanoniczna.

Zasady:
- pliki źródłowe są TYLKO DO ODCZYTU,
- każdy projekt dostaje jedną Kartę Projektu (data/kanoniczne.json),
- wpisy czasu odrzucone przez filtr anomalii NIE znikają — dostają status
  i trafiają do karty oraz do data/ODRZUCONE.md,
- brak danych zapisujemy jako null + wpis w "braki" (nie budujemy atrap).

Nowe źródło z Firmao w przyszłości = nowa funkcja wczytaj_*() i doklejenie
pól do karty. Nic poniżej warstwy kanonicznej nie trzeba zmieniać.
"""
import json, re, glob, os, sys
import pandas as pd
import yaml

BAZA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def wczytaj_konfiguracje():
    with open(f"{BAZA}/konfiguracja/progi.yaml", encoding="utf-8") as f:
        progi = yaml.safe_load(f)
    with open(f"{BAZA}/konfiguracja/slowniki.yaml", encoding="utf-8") as f:
        slowniki = yaml.safe_load(f)
    return progi, slowniki


def wczytaj_projekty():
    """Filar B: projekty z Firmao z agregatami plan/real."""
    p = pd.read_excel(f"{BAZA}/Projekty_wszystkie.xlsx")
    p["start"] = pd.to_datetime(p["startDate"], errors="coerce", utc=True, format="mixed")
    p["koniec"] = pd.to_datetime(p["endDate"], errors="coerce")
    return p


def wczytaj_oferty():
    """Filar B: oferty/zlecenia — łącznik project.id + osoba wystawiająca."""
    o = pd.read_excel(f"{BAZA}/Oferty.xlsx", usecols=[
        "id", "project.id", "offerStatus.label", "issuingPerson",
        "baseNettoPrice", "type", "mode", "offerDate", "number"])
    return o[o["project.id"].notna()].copy()


def wczytaj_notatki():
    n = pd.read_excel(f"{BAZA}/Notatki.xlsx", usecols=["id", "project.id"])
    return n[n["project.id"].notna()]


def wczytaj_czas_pracy(progi, slowniki):
    """Filar C: wszystkie pliki z dane_czas_pracy/ + filtr anomalii."""
    wpisy = []
    for plik in sorted(glob.glob(f"{BAZA}/dane_czas_pracy/*.xlsx")):
        df = pd.read_excel(plik)
        df.columns = ["projekt", "zc_proj", "zadanie", "zc_zad",
                      "osoba", "czas_h", "pozycja", "wartosc"]
        df["projekt"] = df["projekt"].ffill()
        df["zadanie"] = df["zadanie"].ffill()
        df["pid"] = df["projekt"].str.extract(r"^\s*(\d+)")[0].astype("Int64")
        df["wartosc"] = pd.to_numeric(
            df["wartosc"].astype(str).str.replace(",", ".").str.replace(" ", ""),
            errors="coerce")
        df["zrodlo"] = os.path.basename(plik)
        wpisy.append(df)
    if not wpisy:
        return pd.DataFrame()
    w = pd.concat(wpisy, ignore_index=True)
    w["osoba"] = w["osoba"].str.replace(r"\s+", " ", regex=True).str.strip()

    maxh = progi["czas_pracy"]["max_godzin_wpisu"]
    ma_metryke = w["zadanie"].isin(
        w.loc[w["pozycja"].notna(), "zadanie"].unique())
    w["status"] = "OK"
    w.loc[w["czas_h"] > maxh, "status"] = "ANOMALIA_STOP"      # zapomniany stop
    w.loc[(w["czas_h"] <= 0) & ma_metryke, "status"] = "ANOMALIA_START"  # zapomniany start
    w.loc[(w["czas_h"] <= 0) & ~ma_metryke, "status"] = "PUSTY"
    w["nieprodukcyjne"] = w["zadanie"].isin(slowniki["zadania_nieprodukcyjne"])
    return w


def ilosc_z_nazwy(nazwa):
    """Przejściowe (do decyzji D2): plan ilości parsowany z nazwy projektu."""
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(mb|m2|m²)", str(nazwa), re.I)
    if not m:
        return None
    return {"wartosc": float(m.group(1).replace(",", ".")),
            "jednostka": m.group(2).lower().replace("²", "2"),
            "zrodlo": "nazwa projektu (przejściowo, docelowo pole Firmao — D2)"}


def buduj_karty():
    progi, slowniki = wczytaj_konfiguracje()
    p = wczytaj_projekty()
    o = wczytaj_oferty()
    n = wczytaj_notatki()
    czas = wczytaj_czas_pracy(progi, slowniki)
    osoby = slowniki.get("osoby", {})

    oferty_proj = o.groupby("project.id")
    notatki_cnt = n.groupby("project.id").size()

    karty = []
    for _, r in p.iterrows():
        pid = int(r["id"])
        plan_koszt = float(r["plannedCostSummaryNetto"])
        plan_przych = float(r["plannedIncomeSummaryNetto"])
        real_koszt = float(r["actualCostSummaryNetto"])
        real_przych = float(r["actualIncomeSummaryNetto"])

        # oferty powiązane: preferuj sprzedażową zrealizowaną jako źródłową
        of = oferty_proj.get_group(pid) if pid in oferty_proj.groups else None
        oferta = None
        kalk_oferta = None
        if of is not None and len(of):
            sprz = of[of["mode"] == "SALE"]
            wyb = sprz[sprz["offerStatus.label"] == "Zrealizowana"]
            wyb = wyb if len(wyb) else sprz
            if len(wyb):
                w0 = wyb.iloc[0]
                oferta = {"id": int(w0["id"]), "numer": str(w0["number"]),
                          "status": str(w0["offerStatus.label"]),
                          "data": str(w0["offerDate"])[:10],
                          "wartosc_netto": float(w0["baseNettoPrice"])}
                kalk_oferta = str(w0["issuingPerson"])

        odch = (real_koszt - plan_koszt) / plan_koszt * 100 if plan_koszt > 0 else None
        marza_plan = plan_przych - plan_koszt
        marza_real = real_przych - real_koszt
        status = str(r["projectStatus.label"])
        zakonczony = status.startswith("Zakończ")
        rozliczony = status == "Zakończony i ROZLICZONY"

        strefa = None
        if odch is not None:
            strefa = ("zielona" if odch <= progi["strefy"]["zielona_max_pct"]
                      else "zolta" if odch <= progi["strefy"]["zolta_max_pct"]
                      else "czerwona")

        # flagi rozliczeń (kafel "Nierozliczone")
        bez_przychodu = zakonczony and not rozliczony and real_przych <= 0
        niedofakturowany = (zakonczony and not rozliczony and plan_przych > 0
                            and real_przych < progi["rozliczenia"]["prog_niedofakturowania"] * plan_przych
                            and real_przych > 0)

        # Filar C: czas pracy tego projektu
        czas_proj = None
        if len(czas) and pid in set(czas["pid"].dropna().astype(int)):
            cw = czas[czas["pid"] == pid]
            ok = cw[cw["status"] == "OK"]
            normy = []
            for zad, g in ok.groupby("zadanie"):
                wart = g["wartosc"].max()
                poz = g["pozycja"].dropna()
                if pd.notna(wart) and wart > 0 and g["czas_h"].sum() > 0 and len(poz):
                    normy.append({"zadanie": zad,
                                  "jednostka": str(poz.iloc[0]),
                                  "wykonano": round(float(wart), 1),
                                  "godziny": round(float(g["czas_h"].sum()), 2),
                                  "tempo_na_h": round(float(wart) / float(g["czas_h"].sum()), 1)})
            hp = float(ok.loc[~ok["nieprodukcyjne"], "czas_h"].sum())
            hn = float(ok.loc[ok["nieprodukcyjne"], "czas_h"].sum())
            czas_proj = {
                "h_produkcyjne": round(hp, 2),
                "h_nieprodukcyjne": round(hn, 2),
                "h_odrzucone_anomalie": round(float(cw.loc[cw["status"] != "OK", "czas_h"].sum()), 2),
                "wpisy_ok": int((cw["status"] == "OK").sum()),
                "wpisy_odrzucone": int((cw["status"] != "OK").sum()),
                "normy": normy,
                "wpisy": [{"zadanie": x["zadanie"], "osoba": x["osoba"],
                           "h": round(float(x["czas_h"]), 2), "status": x["status"]}
                          for _, x in cw.iterrows()],
            }

        braki = []
        if plan_koszt <= 0: braki.append("plan kosztów (Firmao)")
        if plan_przych <= 0: braki.append("plan przychodu (Firmao)")
        if czas_proj is None: braki.append("czas pracy brygad (aplikacja)")
        braki += ["koszty per kategoria (K1/K2)", "plan godzin (D2)"]

        karty.append({
            "id": pid,
            "nazwa": str(r["name"]),
            "status": ("rozliczony" if rozliczony else
                       "zakonczony" if zakonczony else "w_realizacji"),
            "klient": None if pd.isna(r["customer.label"]) else str(r["customer.label"]),
            "typ": None if pd.isna(r["customFields.custom2"]) else str(r["customFields.custom2"]),
            "technologia": None if pd.isna(r["customFields.custom11"]) else str(r["customFields.custom11"]),
            "kalkulujacy": osoby.get(str(r["createdBy.label"]), str(r["createdBy.label"])),
            "kalkulujacy_oferta": kalk_oferta,
            "daty": {"start": None if pd.isna(r["start"]) else str(r["start"])[:10],
                     "koniec": None if pd.isna(r["koniec"]) else str(r["koniec"])[:10]},
            "plan": {"koszty": round(plan_koszt, 2), "przychod": round(plan_przych, 2),
                     "marza": round(marza_plan, 2),
                     "marza_pct": round(100 * marza_plan / plan_przych, 1) if plan_przych > 0 else None,
                     "ilosc": ilosc_z_nazwy(r["name"]),
                     "godziny": None if pd.isna(r["estimatedHours"]) else float(r["estimatedHours"])},
            "real": {"koszty": round(real_koszt, 2), "przychod": round(real_przych, 2),
                     "marza": round(marza_real, 2),
                     "marza_pct": round(100 * marza_real / real_przych, 1) if real_przych > 0 else None,
                     "godziny_firmao": None if pd.isna(r["actualWorkHours"]) else float(r["actualWorkHours"])},
            "pochodne": {"odchylenie_kosztow_pct": None if odch is None else round(odch, 1),
                         "utrata_marzy": round(marza_real - marza_plan, 2),
                         "strefa": strefa,
                         "komplet_plan_real": bool(plan_koszt > 0 and plan_przych > 0
                                                   and real_koszt > 0 and real_przych > 0)},
            "rozliczenia": {"bez_przychodu": bool(bez_przychodu),
                            "niedofakturowany": bool(niedofakturowany),
                            "luka_przychodu": round(plan_przych - real_przych, 2)
                            if (bez_przychodu or niedofakturowany) else 0},
            "czas_pracy": czas_proj,
            "zrodla": {"oferty": 0 if of is None else int(len(of)),
                       "notatki": int(notatki_cnt.get(pid, 0))},
            "braki": braki,
        })

    # rzetelność wpisów per osoba (globalnie, do zakładki Jakość danych)
    rzetelnosc = []
    if len(czas):
        for os_, g in czas.groupby("osoba"):
            rzetelnosc.append({"osoba": os_, "wpisy": int(len(g)),
                               "ok": int((g["status"] == "OK").sum()),
                               "rzetelnosc_pct": round(100 * (g["status"] == "OK").mean())})
        rzetelnosc.sort(key=lambda x: x["rzetelnosc_pct"])

    wynik = {"karty": karty, "rzetelnosc_osob": rzetelnosc,
             "zrodla_czasu": sorted(set(czas["zrodlo"])) if len(czas) else []}
    os.makedirs(f"{BAZA}/data", exist_ok=True)
    with open(f"{BAZA}/data/kanoniczne.json", "w", encoding="utf-8") as f:
        json.dump(wynik, f, ensure_ascii=False)

    # raport odrzuconych — lista do poprawek dyscypliny wpisów
    if len(czas):
        odr = czas[czas["status"].isin(["ANOMALIA_STOP", "ANOMALIA_START"])]
        with open(f"{BAZA}/data/ODRZUCONE.md", "w", encoding="utf-8") as f:
            f.write("# Wpisy czasu odrzucone przez filtr anomalii\n\n")
            f.write(f"Razem: {len(odr)} wpisów, {odr['czas_h'].sum():.0f} h "
                    f"(próg: {progi['czas_pracy']['max_godzin_wpisu']} h/wpis)\n\n")
            f.write("| Projekt | Zadanie | Osoba | Godziny | Powód |\n|---|---|---|---|---|\n")
            for _, x in odr.sort_values("czas_h", ascending=False).iterrows():
                powod = ("zapomniany STOP" if x["status"] == "ANOMALIA_STOP"
                         else "zapomniany START (0 h przy wykonanej produkcji)")
                f.write(f"| {x['pid']} | {x['zadanie']} | {x['osoba']} | {x['czas_h']:.1f} | {powod} |\n")

    print(f"Kart projektów: {len(karty)} | wpisy czasu: {len(czas)} "
          f"(OK: {int((czas['status']=='OK').sum()) if len(czas) else 0})")
    return wynik


if __name__ == "__main__":
    buduj_karty()
