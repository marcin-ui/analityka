#!/usr/bin/env bash
# Jedna komenda odświeżenia pulpitu:
#   1. podmień/dograj eksporty XLSX z Firmao w katalogu głównym,
#   2. dograj nowe raporty czasu pracy do dane_czas_pracy/,
#   3. uruchom: ./aktualizuj.sh
# Wynik: pulpit/index.html + pulpit/dane.js (otwórz index.html w przeglądarce).
set -e
cd "$(dirname "$0")"
python3 etl/kanoniczne.py
python3 etl/metryki.py
echo "OK — otwórz pulpit/index.html"
