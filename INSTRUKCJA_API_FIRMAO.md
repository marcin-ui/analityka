# Instrukcja: podłączenie API Firmao do pulpitu

Cel: zamiast ręcznych eksportów XLSX — automatyczne pobieranie danych z Firmao,
w tym **transakcji projektowych** (luka K1 z audytu: powiązanie faktur/kosztów z projektem).

Do działania potrzebne są 3 rzeczy. Kroki 1 i 2 są po Twojej stronie (ok. 10 minut),
krok 3 wykonuję ja.

---

## Krok 1 — Włącz API w Firmao i wygeneruj dane logowania

1. Zaloguj się do Firmao jako administrator.
2. Wejdź w **Ustawienia** → sekcja integracji / **API** (nazwa pozycji menu może się
   różnić zależnie od wersji; szukaj „API" lub „Integracje").
3. Włącz dostęp API i **wygeneruj login oraz hasło API** (Firmao używa Basic Auth —
   to osobne hasło, nie Twoje hasło do konta).
4. Zanotuj też **identyfikator organizacji** (widoczny w adresie po zalogowaniu).

Uwagi:
- Dostępność API zależy od planu taryfowego Firmao — jeśli nie widzisz opcji API
  w ustawieniach, sprawdź plan lub zapytaj suport Firmao (support@firmao.pl).
- Dokumentacja API: szukaj „Firmao API" w pomocy Firmao lub poproś suport o link
  do aktualnej dokumentacji REST.

## Krok 2 — Odblokuj domenę i podaj dane w środowisku Claude Code

Środowisko, w którym pracuję, blokuje obecnie ruch do `system.firmao.pl`
(polityka sieciowa — sprawdziłem, proxy zwraca 403).

1. Wejdź na **claude.ai/code** → ustawienia środowiska (Environments) dla tego repo.
2. W sekcji **Network policy** dodaj dozwolone domeny:
   - `system.firmao.pl`
   - `firmao.pl`
3. W sekcji **zmiennych środowiskowych** środowiska dodaj (NIE wpisuj ich do repo!):
   - `FIRMAO_LOGIN` = login API z kroku 1
   - `FIRMAO_API_PASSWORD` = hasło API z kroku 1
   - `FIRMAO_ORG` = identyfikator organizacji
4. Zapisz i uruchom nową sesję (zmiany środowiska działają od nowej sesji).

Dokumentacja środowisk i polityk sieciowych:
https://code.claude.com/docs/en/claude-code-on-the-web

## Krok 3 — Test połączenia (wykonuję ja)

Po kroku 1–2 napisz w czacie „API gotowe". Wtedy:
1. Przetestuję połączenie i autoryzację (1 zapytanie o listę projektów).
2. Sprawdzę, które zasoby są dostępne: projekty, transakcje projektowe, dokumenty,
   czas pracy — i czy da się nimi domknąć luki K1 (faktura→projekt) i K3 (godziny).
3. Zbuduję skrypt zasilania: API → walidacja → warstwa kanoniczna → pulpit
   (jedna komenda, zgodnie z Fazą 4).

## Bezpieczeństwo

- Dane logowania trzymamy WYŁĄCZNIE w zmiennych środowiskowych — nigdy w repozytorium.
- Skrypt zasilania będzie działał w trybie tylko-do-odczytu (GET) — niczego w Firmao
  nie zmienia.
- Jeśli wolisz nie otwierać ruchu z chmury do Firmao: alternatywnie skrypt zasilania
  może działać na Twoim komputerze i wrzucać do repo tylko wyniki eksportu.
