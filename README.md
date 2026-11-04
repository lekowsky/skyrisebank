# SkyRiseBank

Plugin bankowy na **Purpur 1.21.10** — gromadzenie waluty serwerowej na kontach graczy.
Autor: **SkyRise**.

> Ten etap to **przygotowanie miejsca pod plugin** (szkielet + kompletna struktura).
> Kolejne szczegóły funkcjonalne dopisujemy w oznaczonych miejscach — patrz sekcja
> „Gdzie dopisywać dalsze funkcje”.

---

## 1. Stan projektu

| Element | Status |
|---|---|
| Struktura projektu Maven | ✅ gotowa |
| `plugin.yml` (komenda `/bank`, `/bankadmin`, permisje) | ✅ gotowa |
| `config.yml` + `messages.yml` (MiniMessage) | ✅ gotowe |
| Klasa główna, cykl życia pluginu | ✅ gotowa |
| Magazyn danych MySQL (HikariCP + `mysql-connector-j`, shadow) | ✅ gotowy |
| Konta, salda (BigDecimal), pamięć podręczna, zapis cykliczny | ✅ gotowe |
| Operacje: wpłata, wypłata, przelew, give/take/set | ✅ gotowe |
| Historia operacji, ranking (top) | ✅ gotowe (zapis + odczyt) |
| Publiczne API + eventy dla innych pluginów | ✅ gotowe (`pl.skyrise.bank.api`) |
| Test na żywym serwerze Purpur 1.21.10 + MySQL | ✅ zaliczony (szczegóły w sekcji 10) |
| **Cicha konsola sterowana jednym ustawieniem** (`settings.console-messages`) | ✅ gotowe (sekcja 8.1) |
| **Bankomaty Nexo + karta bankomatowa (modele z configu, rejestr pozycji)** | ✅ gotowe (sekcja 11) |
| **NPC „Bankier” (FancyNpcs) → GUI skrzynkowe → konto osobiste + PIN przez Dialogi** | ✅ gotowe (sekcja 12) |
| **Karta bankomatowa z danymi konta + logowanie w bankomacie kartą i PIN-em** | ✅ gotowe (sekcja 12.7) |
| **Krótkie, losowe numery kont + namierzanie właściciela** (numer **i nick**: `/bankadmin konto ...`) | ✅ gotowe (sekcja 12.8) |
| **Ekonomia Vault / EssentialsX** (saldo widoczne dla `/balance`, `/pay`, `/eco`, sklepów) | ✅ gotowe (sekcja 13) |
| Mostek Vault (pełna implementacja `Economy`) | ✅ gotowe (sekcja 13) |
| PlaceholderAPI | ⏳ do zaimplementowania wg dalszych szczegółów |
| Logika biznesowa (odsetki, limity dzienne, karty itp.) | ⏳ czeka na szczegóły |

Wersja pluginu: **1.0.0** · Java **21** · artefakt: `release/SkyRiseBank.jar` (nazwa pliku bez numeru wersji)

---

## 2. Budowanie

Wymagania do **kompilacji**: **JDK 25** (API FancyNpcs jest zbudowane dla Javy 25)
oraz **Maven 3.9+**. Wynikowy jar jest zgodny z **Javą 21+** (`--release 21`).

```bash
cd SkyRiseBank
mvn clean package
```

Wynik: `target/SkyRiseBank.jar` (gotowy do wrzucenia do `plugins/`) — nazwa pliku **bez numeru wersji**.
Gotowy jar jest też odłożony w `release/`.

Skrypt pomocniczy:

```bash
./build.sh          # mvn clean package + kopiowanie jara do release/
```

### Uwaga o środowisku budowania

Purpur 1.21.10 wymaga **Javy 21** — plugin jest kompilowany z `--release 21`
(class file 65), więc działa na Javie 21 i nowszych.

Do **kompilacji** potrzebny jest jednak **JDK 25**, ponieważ API FancyNpcs
(artefakt `de.oliver:FancyNpcs`) jest zbudowane dla Javy 25 (class file 69)
i starszy `javac` odmawia czytania takich klas. Ustaw zatem `JAVA_HOME` na JDK 25:

```bash
export JAVA_HOME=/usr/lib/jvm/java-25-openjdk-amd64
mvn clean package
```

(Na serwerze FancyNpcs 2.11+ i tak wymaga Javy 25; bez tego pluginu NPC
„Bankier” nie powstanie, a reszta banku działa normalnie.)

---

## 3. Instalacja na serwerze

1. Wrzuć `SkyRiseBank.jar` do katalogu `plugins/`.
2. Uruchom serwer raz — plugin wygeneruje `plugins/SkyRiseBank/config.yml` i `messages.yml`.
3. Uzupełnij dane bazy w `config.yml` (`storage.mysql`) i wykonaj `/bankadmin reload`.
4. Tabele tworzą się automatycznie przy starcie (`storage.auto-migrate: true`).

### Tabele w bazie (prefiks `srb_`)

```sql
srb_accounts       -- portfele graczy: uuid, player_name, balance DECIMAL(20,2), frozen, created_at, updated_at
srb_transactions   -- historia: account_uuid, counterparty_uuid, type, amount, balance_after, note, created_at
srb_bank_accounts  -- konta bankowe (karty): number, owner_name, owner_uuid, type, balance, pin_hash, ...
srb_atms           -- zarejestrowane bankomaty
```

### Szybki test bez bazy

W `config.yml` ustaw:

```yaml
storage:
  type: IN_MEMORY
```

Konta będą trzymane w pamięci (dane przepadają po restarcie) — wygodne do sprawdzenia
komend i komunikatów bez stawiania MySQL.

---

## 4. Komendy i uprawnienia

| Komenda | Opis | Uprawnienie | Domyślnie |
|---|---|---|---|
| `/bank` | pomoc / saldo własne | `bank.command.bank` | wszyscy |
| `/bank saldo [gracz]` | saldo swoje lub innego gracza | `bank.command.bank.others` (dla innych) | OP |
| `/bank przelew <gracz> <kwota>` | przelew między kontami | `bank.command.bank` | wszyscy |
| `/bank top` | ranking kont | `bank.command.bank` | wszyscy |
| `/bank historia [strona]` | historia operacji | `bank.command.bank` | wszyscy |
| `/bankadmin reload` | przeładowanie configu i wiadomości | `bank.admin.reload` | OP |
| `/bankadmin info <gracz>` | szczegóły konta | `bank.admin.balance` | OP |
| `/bankadmin give\|take\|set <gracz> <kwota>` | zmiana salda | `bank.admin.balance` | OP |
| `/bankadmin konto <numer>` | namierzenie właściciela konta po numerze z karty | `bank.admin.balance` | OP |

Aliasy: `/bank` → `konto`, `kasa`; `/bankadmin` → `srb`, `sbadmin`.

---

## 5. Publiczne API dla innych pluginów

```java
import pl.skyrise.bank.api.SkyRiseBankProvider;
import pl.skyrise.bank.bank.SkyRiseBankAPI;

Optional<SkyRiseBankAPI> api = SkyRiseBankProvider.getOptional();
api.ifPresent(bank -> {
    bank.getBalance(player.getUniqueId())
        .thenAccept(balance -> getLogger().info("Saldo: " + balance));

    bank.deposit(player.getUniqueId(), new BigDecimal("250.00"), "nagroda za event")
        .thenAccept(result -> {
            if (!result.success()) {
                getLogger().warning("Operacja odrzucona: " + result.status());
            }
        });
});
```

### Eventy

| Event | Kiedy | Anulowalny |
|---|---|---|
| `BankTransactionEvent` | przed operacją (walidacja/limity innych pluginów) | ✅ `setCancelled(true)` |
| `BankBalanceChangeEvent` | po zmianie salda (osiągnięcia, logi, statystyki) | ❌ |

---

## 6. Architektura (gdzie co się znajduje)

```
pl.skyrise.bank
├── SkyRiseBankPlugin      klasa główna: cykl życia, komendy, zadania cykliczne
├── api
│   ├── SkyRiseBankProvider  rejestr publicznego API
│   └── event/               BankTransactionEvent, BankBalanceChangeEvent
├── bank
│   ├── SkyRiseBankAPI       interfejs dla innych pluginów
│   ├── BankService          wszystkie operacje na saldach (walidacja → event → baza → event)
│   ├── AccountManager       pamięć podręczna, wczytywanie/zapis, flush, eviction
│   ├── BankResult           wynik operacji (status + ścieżka komunikatu)
│   └── EconomyBridge        mostek Vault (dynamiczne proxy, bez zależności kompilacyjnej)
├── atm                      bankomaty: rozpoznawanie modeli, rejestr pozycji, komunikaty
├── bank
│   └── BankAccountService   konta bankowe: zakładanie z PIN-em, odczyt, zmiana PIN-u, saldo
├── command                  /bank, /bankadmin + wspólne pomocniki
├── card                     karta bankomatowa: budowa przedmiotu, dane konta (PDC)
├── config                   PluginConfig (rekordy), Messages (messages.yml)
├── dialog                   PinDialog (Paper Dialogs) - ustawianie PIN-u karty
├── gui                      BankGui (skrzynkowe GUI banku) + GuiListener (kliknięcia)
├── hook                     integracje: NexoHook/NexoListener (Nexo),
│                            VaultEconomy (ekonomia Vault / EssentialsX)
├── listeners                PlayerJoinListener, AtmListener (bloki/bankomaty)
├── model                    Account, Transaction, TransactionType, BankAccount, BankAccountType
├── npc                      NpcHook (FancyNpcs API) + NpcListener (kliknięcie NPC)
├── storage
│   ├── StorageProvider/Factory  wybór magazynu (MYSQL, IN_MEMORY)
│   ├── MySqlStorageProvider     HikariCP, test połączenia, auto-migracja
│   ├── SqlAccountDao            zapytania SQL + DDL
│   ├── SqlBankAccountDao        konta bankowe (tabela bank_accounts)
│   └── InMemoryAccountDao       magazyn do testów
└── util                     Text (MiniMessage), Amounts (BigDecimal), Scheduler (async/sync),
                             Items (przedmioty do GUI), Pins (PBKDF2), LogSilencer
```

### Zasady, których warto się trzymać

- **Kwoty zawsze `BigDecimal`** (`Amounts.parse`, `Amounts.format`) — nigdy `double`.
- **Baza tylko asynchronicznie** — `Scheduler.supplyAsync(...)`, powrót na wątek serwera przez `Scheduler.sync(...)`.
- **Teksty w `messages.yml`**, format MiniMessage — nie wpisujemy kolorów w kod.
- **Nowe funkcje konfiguracji** dodajemy w `PluginConfig` jako kolejny rekord + sekcja w `config.yml`.

---

## 7. Gdzie dopisywać dalsze funkcje (miejsca pod szczegóły)

Kod zawiera znaczniki, które ułatwią dokończenie projektu:

| Temat | Miejsce |
|---|---|
| Obsługa kliknięcia bankomatu (karta + PIN) | `atm/AtmAccess#use` (wołane z `hook/NexoListener#onFurnitureInteract` i `listeners/AtmListener#onInteract`) |
| Wydanie karty bankomatowej, dane na karcie | `card/BankCard` (+ teksty w sekcji `card` w `config.yml`) |
| Kolejne rodzaje kont (biznesowe, organizacyjne, frakcyjne) | `model/BankAccountType` (już są) + `bank/BankAccountService` + `gui/GuiListener#handleSelectClick` (gałąź dla danego typu) |
| Operacje konta (wpłata, wypłata, przelew, historia) | `gui/GuiListener#handlePersonalClick` — akcje z `gui.personal.actions` w `config.yml` |
| Zmiana PIN-u, blokada karty | `bank/BankAccountService#changePin` / `verifyPin` (gotowe) + nowy dialog w `dialog/` |
| Kolejne dialogi (np. kwota przelewu) | `dialog/` — wzór: `PinDialog` (`Dialog.create` + `DialogInput.text` + `DialogAction.customClick`) |
| Nowe podkomendy gracza | `command/BankCommand` (switch na `args[0]` + `SUBCOMMANDS`) |
| Nowe podkomendy admina | `command/BankAdminCommand` |
| Nowe operacje na saldzie (np. odsetki) | `bank/BankService` — `Operation` + `apply(...)` |
| Nowe typy wpisów historii | `model/TransactionType` |
| Kolejne magazyny (SQLite/PostgreSQL) | `config/PluginConfig.StorageType` + `storage/StorageFactory` |
| Ustawienia | `config/PluginConfig` (rekord) + sekcja w `config.yml` |
| Komunikaty | `messages.yml` |
| PlaceholderAPI | `bank/` (nowa klasa rejestrująca expansion) — `integrations.placeholderapi` |
| Ekonomia Vault / EssentialsX | `hook/VaultEconomy` (implementacja `Economy`) + `bank/EconomyBridge` (rejestracja) |

Dziedziczone TODO w kodzie:
- `EconomyBridge` — pozostałe metody interfejsu Vault (banki, nazwane konta),
- `CommandSupport.onlineNames()` — podpowiedzi Tab dla graczy offline z bazy,
- obsługa PlaceholderAPI (`integrations.placeholderapi`).

---

## 8. Uwagi techniczne

- **Threading**: operacje I/O wyłącznie w wątkach asynchronicznych (schedulery globalne Paper/Purpur),
  dzięki czemu plugin działa też na serwerach z region-threadami (Folia-like).
- **Shade**: HikariCP jest przenoszony do `pl.skyrise.bank.libs.hikari`, sterownik MySQL pozostaje
  w `com.mysql.cj.*` (rejestracja przez `java.sql.Driver` / `META-INF/services`).
- **Eventy** wołane są na głównym wątku — nie należy w nich wykonywać operacji blokujących.
- **Reload**: `/bankadmin reload` wczytuje `config.yml` i `messages.yml`.
  Zmiana typu magazynu danych wymaga restartu serwera.

---

### 8.1a. Prefiks wiadomości (`settings.prefix`)

Prefiks wiadomości ustawia się w **config.yml** — ma pierwszeństwo nad kluczem `prefix`
z `messages.yml`:

```yaml
settings:
  prefix: "<gradient:#38bdf8:#818cf8><bold>Bank</bold></gradient> <dark_gray>»</dark_gray> "
```

- Wartość **pusta** (`prefix: ""`) = plugin użyje klucza `prefix` z `messages.yml`.
- Gdy prefiks nie kończy się spacją, plugin dokleja ją automatycznie (żeby nie sklejał się
  z treścią komunikatu).
- Zmiana działa po `/bankadmin reload` (bez restartu serwera).
- Starsze wersje pluginu zapisywały prefiks z brandingiem „SkyRiseBank” w `messages.yml` —
  plugin **odświeża taki stary wpis sam** przy wczytaniu pliku (komunikat w konsoli przy
  `settings.console-messages: true`), a także dopisuje do `messages.yml` nowe klucze,
  których w pliku jeszcze nie ma.

---

### 8.1. Komunikaty w konsoli (`settings.console-messages`)

Cała "gadatliwość" pluginu sterowana jest **jednym ustawieniem**:

```yaml
settings:
  console-messages: false   # false = cisza (domyślnie), true = pełne informacje
  debug: false              # logi [debug], niezależne od console-messages
```

| | `console-messages: false` (domyślnie) | `console-messages: true` |
|---|---|---|
| Start / wyłączenie pluginu | — | + |
| Magazyn danych, tworzenie tabel | — | + |
| Bankomaty, Nexo, karta, weryfikacja wpisów | — | + |
| Ostrzeżenia statusowe (np. brak modeli) | — (poziom FINE) | + |
| Logi bibliotek (HikariCP, sterownik MySQL) | wyciszone automatycznie | bez zmian |
| **Błędy krytyczne** (brak bazy, błąd zapisu konta, błąd komendy) | **zawsze widoczne** | zawsze widoczne |

- W trybie ciszy informacje trafiają na poziom `FINE` — są dostępne przy debugowaniu logów,
  ale nie zaśmiecają konsoli.
- Wyciszenie bibliotek wykonuje `util/LogSilencer` (Log4j2, tylko wskazane pakiety;
  jeżeli serwer użyje innego backendu logów — po prostu nic się nie dzieje).
- Ustawienie działa przy starcie pluginu. Po zmianie na `true` w trakcie działania
  (`/bankadmin reload`) komunikaty pluginu wrócą od razu, a logi bibliotek dopiero po restarcie.
- Uwaga: linie `Loading server plugin SkyRiseBank` / `Enabling SkyRiseBank` pochodzą od
  samego serwera (Paper/Purpur) i nie zależą od pluginu.

---

## 9. Test na serwerze Purpur 1.21.10

Konfiguracja testowa użyta przy weryfikacji:

```yaml
storage:
  type: MYSQL      # lub IN_MEMORY do testu bez bazy
  mysql:
    host: 127.0.0.1
    port: 3306
    database: skyrisebank
    username: srb
    password: "srbpass"
    table-prefix: "srb_"
    connection-parameters: "?useUnicode=true&characterEncoding=utf8&serverTimezone=UTC"
currency:
  starting-balance: 250.0
settings:
  debug: true
```

Kolejność testu: uruchom serwer → wpisz graczem `/bank` (konto utworzone automatycznie z saldem startowym),
`/bankadmin give <nick> 1000`, `/bank przelew <nick> 100`, `/bank top`, `/bank historia`,
sprawdź tabele `srb_accounts` i `srb_transactions` w bazie.

---

## 10. Wyniki weryfikacji (test na żywym serwerze)

Projekt został zbudowany i uruchomiony na prawdziwym serwerze:

| Element | Wartość |
|---|---|
| Serwer | Purpur **1.21.10**-2535-HEAD@0a2dc04 (API 1.21.10-R0.1-SNAPSHOT) |
| Java | OpenJDK **21** (kompilacja `--release 21`, class file 65) |
| Baza | MariaDB **11.8** (protokół MySQL, sterownik `com.mysql.cj.jdbc.Driver`) |
| Artefakt | `SkyRiseBank.jar` (~3,0 MB, HikariCP + sterownik MySQL w środku) |

Log startowy serwera (fragment):

```
[SkyRiseBank] Loading server plugin SkyRiseBank v1.0.0
[SkyRiseBank] Enabling SkyRiseBank v1.0.0
[pl.skyrise.bank.libs.hikari.HikariDataSource] SkyRiseBank-Pool - Starting...
[pl.skyrise.bank.libs.hikari.pool.HikariPool] SkyRiseBank-Pool - Added connection ...
[SkyRiseBank] Sprawdzanie struktury tabel (prefiks: 'srb_')...
[SkyRiseBank] SkyRiseBank włączony. Magazyn: MySQL | waluta: SkyCoins | Vault: nie
```

Sprawdzone zachowanie (komendy przez konsolę/RCON):

1. Tabele `srb_accounts` i `srb_transactions` utworzyły się automatycznie (`auto-migrate`).
2. `/bank` — pomoc renderuje się poprawnie (MiniMessage: gradient, kolory, prefiks).
3. `/bank saldo <gracz>` z konsoli — poprawna walidacja „tylko dla graczy”.
4. `/bankadmin set TestPlayer 5000` → `/bankadmin give TestPlayer 1000` → `/bankadmin take TestPlayer 300`
   → `/bankadmin give TestPlayer 250`: saldo w bazie zmieniało się dokładnie jak w komendach
   (**5000 → 6000 → 5700 → 5950**), a każda operacja zapisała wpis w historii:

   ```
   ADMIN | 250.00 | 5950.00 | give /bankadmin
   ADMIN | 300.00 | 5700.00 | take /bankadmin
   ADMIN | 1000.00 | 6000.00 | set /bankadmin
   ```

5. Wpisy połączeń działają: HikariCP loguje `SkyRiseBank-Pool - Start completed`, zapytania asynchroniczne
   nie blokują wątku serwera (`Done (14.425s)!` przy starcie, brak opóźnień w TPS).

### Uwaga o testach przez RCON

Komunikaty zwrotne operacji bankowych wysyłane są **po** zakończeniu zapisu w bazie (asynchronicznie),
a konsola RCON zbiera output tylko w trakcie wykonywania komendy — dlatego w RCON widać odpowiedzi
komend synchronicznych, a odpowiedzi operacji bankowych pojawiają się tylko w logu debug
(`[debug] Odpowiedź /bankadmin dla Rcon: status=SUCCESS, komunikat=admin.give-success`).
Gracz w grze otrzymuje je normalnie.

### Wnioski dla dalszej pracy

- Ścieżka asynchroniczna jest w pełni sprawna: walidacja → zapis → historia → komunikat.
- Wszystkie przyszłe funkcje (odsetki, limity, konta firmowe itp.) wystarczy dopiąć w `BankService`
  + nowe rekordy w `PluginConfig` i klucze w `messages.yml`.

---

## 11. Bankomaty i karta bankomatowa (Nexo)

Funkcja odpowiada za to, żeby plugin **wiedział, że postawiony obiekt to bankomat**.
Modele ustawia się w `config.yml` — zmiana modelu w Nexo nie wymaga zmian w kodzie.

### 11.1. Konfiguracja modeli

```yaml
models:
  # Model przedmiotu - karty bankomatowej
  bank-card:
    - "karta_bankomatowa"
  # Model bankomatu stojącego (furniture w Nexo)
  atm-standing:
    - "bankomat_stojacy"
  # Model bankomatu montowanego w ścianie
  atm-wall:
    - "bankomat_sciana"
```

- Można podać **listę**, **pojedynczy wpis** albo wartości **po przecinku**.
- Prefiks `nexo:` jest opcjonalny (`nexo:bankomat` == `bankomat`), wielkość liter nie ma znaczenia.
- Do każdej pozycji można wpisać wiele modeli (np. warianty bankomatu).
- `models.bank-card-fallback` (domyślnie `PAPER`) to materiał karty, gdy brak modelu Nexo
  albo Nexo nie jest zainstalowane — karta działa wtedy „na papierze”, z pełnymi danymi w opisie.
- Karta bankomatowa jest **budowana z danych konta** (właściciel, **krótki numer konta**,
  rodzaj, data utworzenia — bez PIN-u), niezależnie od tego, czy jest model Nexo,
  czy materiał zastępczy.
- Karta zapisuje dodatkowo w PDC **identyfikator konta** — to on decyduje, do jakiego salda
  karta daje dostęp (karta, nie gracz).

### 11.2. Konfiguracja zachowania bankomatów

```yaml
atms:
  enabled: true
  register-on-place: true      # rejestracja w chwili postawienia
  unregister-on-break: true    # usunięcie wpisu przy zniszczeniu
  notify-on-place: true        # komunikat po zarejestrowaniu
  notify-on-use: true          # komunikat po kliknięciu bankomatu
  auto-register-on-use: true   # rejestracja przy użyciu (bankomaty postawione wcześniej)
  verify-interval-minutes: 5   # kontrola wpisów-sierot (0 = wyłączone)
  list-limit: 20               # ile pozycji w /bankadmin atm list
  names:
    standing: "Bankomat stojący"
    wall: "Bankomat w ścianie"
  fallback:                    # awaryjne wykrywanie bez Nexo (typ bloku)
    standing-material: ""
    wall-material: ""
```

### 11.3. Jak plugin rozpoznaje bankomat

| Sytuacja | Ścieżka rozpoznania |
|---|---|
| Bankomat jako **furniture** Nexo (stojący / w ścianie) | zdarzenia Nexo: `NexoFurniturePlaceEvent`, `NexoFurnitureBreakEvent`, `NexoFurnitureInteractEvent` |
| Bankomat jako **custom block** Nexo | `BlockPlaceEvent` → model przedmiotu; zniszczenie/kliknięcie → `BlockBreakEvent` / `PlayerInteractEvent` |
| Brak Nexo | typ bloku z sekcji `atms.fallback` |
| Bankomat postawiony wcześniej (WorldEdit, schemat, przed włączeniem funkcji) | rejestracja przy pierwszym użyciu (`auto-register-on-use`) lub ręcznie `/bankadmin atm add` |

Dodatkowo co `verify-interval-minutes` minut plugin sprawdza, czy zarejestrowane bankomaty
nadal istnieją (nie ładuje przy tym nieaktywnych chunków) i usuwa wpisy-sieroty.

### 11.4. Rejestr w bazie

Wpisy trafiają do tabeli **`<prefiks>atms`** (domyślnie `srb_atms`):

```sql
srb_atms  -- id, world, x, y, z, kind (standing/wall), model_id, owner_uuid, created_at
          -- UNIQUE (world, x, y, z) -> jedna pozycja = jeden bankomat
```

### 11.5. Komendy (`/bankadmin atm ...`)

| Komenda | Opis |
|---|---|
| `/bankadmin atm check` | diagnostyka: co plugin widzi w miejscu, na które patrzysz (model Nexo bloku, furniture, karta w ręce, wpis w rejestrze) |
| `/bankadmin atm add [standing\|wall]` | ręczna rejestracja bankomatu (bez argumentu rodzaj wykrywany z modelu) |
| `/bankadmin atm remove` | usunięcie wpisu na pozycji, na którą patrzysz |
| `/bankadmin atm list` | lista zarejestrowanych bankomatów |
| `/bankadmin atm karta [gracz]` | wydanie karty bankomatowej z konta gracza (bez argumentu — sobie) |

Uprawnienie: `bank.admin.atm` (domyślnie OP). Celowanie: do 6 bloków.
Karta jest wydawana wyłącznie graczowi, który **ma już konto bankowe** (inaczej: stosowny komunikat).

### 11.6. Jak przetestować

1. Ustaw modele w `config.yml` → `models` (ID dokładnie takie jak pliki `items/*.yml` w Nexo).
2. `/bankadmin reload` i sprawdź konsolę: linia `Bankomaty: Nexo wykryte | modele ATM: skonfigurowane | karta: skonfigurowana`.
3. Postaw bankomat (stojący i w ścianie) — rejestracja działa **po cichu** (bez komunikatów);
   ewentualną jednorazową informację o nowym wpisie włącza `atms.notify-on-place: true`.
4. `/bankadmin atm check` wycelowany w bankomat — pokaże model i wpis w rejestrze.
5. `/bankadmin atm list` — pozycja powinna być na liście; w bazie pojawi się wiersz w `srb_atms`.
6. Kliknij bankomat **bez karty** → „Przyłóż kartę bankomatową…”.
7. Kliknij bankomat **z kartą w ręce** → dialog z prośbą o PIN; poprawny PIN otwiera menu kont.
8. Zniszcz bankomat → wpis znika z listy i z tabeli.
9. `/bankadmin atm karta [gracz]` — wydaje kartę na podstawie konta gracza.

### 11.7. Uwagi

- Nexo jest **miękką zależnością** (`softdepend`) — plugin działa bez niego (tryb `fallback` po materiale).
- API Nexo jest wywoływane wyłącznie przez `NexoHook`, w całości zabezpieczone (`try/catch`):
  brak klasy/metody nie wywala pluginu, a jedynie wyłącza integrację z czytelnym logiem.
- Budowanie wymaga dostępu do repozytorium `https://repo.nexomc.com/releases`
  (zależność `com.nexomc:nexo`, zakres `provided` — **nie trafia do jara**).

---

## 12. NPC „Bankier” → GUI skrzynkowe → konto z PIN-em (FancyNpcs + Paper Dialogs)

### 12.1. Przepływ

**Część 1 — zakładanie konta u Bankiera**

1. Gracz klika **prawym przyciskiem** NPC o nazwie **`Bankier`** (FancyNpcs).
2. Otwiera się okno skrzynkowe z **jedną ikonką na środku** (zielony barwnik):
   **„Stwórz konto bankowe”**.
3. Kliknięcie ikonki → **dialog** (Paper Dialogs) z prośbą o ustawienie **PIN-u do karty**.
4. Po zatwierdzeniu poprawnego PIN-u konto zostaje utworzone (PIN zapisany jako hash),
   a gracz **otrzymuje kartę bankomatową** z danymi konta (bez PIN-u).
5. Jeśli konto już istnieje, karta nie jest dublowana — plugin informuje, że karta została
   już wydana (i nie tworzy drugiego konta).

**Część 2 — korzystanie z bankomatu**

6. Gracz podchodzi do bankomatu i **trzyma kartę w ręce** (głównej lub pomocniczej).
7. Bez karty w ręce bankomat **nie działa** — pojawia się tylko informacja „Przyłóż kartę…”.
8. Z kartą w ręce → **dialog z PIN-em**; poprawny PIN otwiera **menu kont z karty**
   (cztery konta w środkowym rzędzie, z odstępami).
9. W menu: **Konto osobiste** → panel konta (saldo konta, numer konta, informacja
   o PIN-ie, data utworzenia, powrót do listy), pozostałe konta → czerwona notka
   **„W trakcie prac”**.

> **Karta należy do konta, nie do gracza.** Jeśli kartę dostanie ktoś inny, może z niej
> skorzystać — wystarczy, że zna PIN. Karta bez PIN-u (np. założona przez ekonomię Vault)
> działa dopiero po ustawieniu PIN-u u Bankiera.

Walidacja PIN-u: wyłącznie cyfry, dokładnie `banking.pin.length` znaków oraz (domyślnie)
odrzucanie PIN-ów oczywistych — `0000`, `1111`, `1234`, `4321`, `19xx`, `20xx`.
PIN nie jest nigdzie zapisywany jawnie — w bazie leży hash **PBKDF2WithHmacSHA256**
(50 000 iteracji, 16-bajtowa sól), a porównanie jest odporne na timing.

### 12.2. Konfiguracja (`config.yml`)

```yaml
npc:
  enabled: true
  name: "Bankier"          # musi się zgadzać z NPC w FancyNpcs
  cancel-interaction: true # bank sam obsługuje kliknięcie
  skin: ""                 # nick gracza na skin NPC (puste = domyślny)
  auto-create: false       # true = postaw NPC sam przy starcie (wymaga location)
  location: { world: "world", x: 0.5, y: 65.0, z: 0.5, yaw: 0.0, pitch: 0.0 }

banking:
  pin:
    length: 4
    block-obvious: true
    max-attempts: 3       # ile razy można pomylić PIN przy bankomacie
  number-length: 6        # długość losowego numeru konta (4-12 cyfr)
  types:
    personal:     { enabled: true }   # działa
    business:     { enabled: false }  # reszta: czerwona notka "W trakcie prac"
    organization: { enabled: false }
    faction:      { enabled: false }

card:                      # karta bankomatowa (dane konta, bez PIN-u)
  name: "<green><bold>Karta bankomatowa</bold>"
  lore: [ ..., "<gray>Numer konta: <white><number></white>", ... ]

integrations:
  vault: true             # ekonomia dla Vault / EssentialsX (wymaga pluginu Vault)
  vault-source: WALLET    # WALLET = portfel gracza, CARD_ACCOUNT = konto-karta

gui:
  work-in-progress: "<red>W trakcie prac"
  create:   { title: ..., rows: 3, slot: 13, material: LIME_DYE, name: "<green>Stwórz konto bankowe", lore: [...] }
  bank:     { title: ..., rows: 3, slots: [10, 12, 14, 16], filler: BLACK_STAINED_GLASS_PANE, items: { ... } }
  personal: { title: ..., rows: 3, info: {...}, back: {...}, actions: { deposit, withdraw, transfer, history } }
```

- `gui.create` to okno otwierane przez NPC: **jedna ikonka** (`slot: 13`) — domyślnie zielony
  barwnik (`LIME_DYE`) z nazwą „Stwórz konto bankowe”, bez kursywy.
- `gui.bank.slots` to sloty czterech kont **w kolejności** osobiste → biznesowe → organizacyjne → frakcyjne.
  Domyślnie `[10, 12, 14, 16]` — między kontami są **odstępy** (puste sloty wypełnione tłem).
- Nazwy i opisy przedmiotów w GUI oraz na karcie są automatycznie pozbawiane kursywy
  (`util/Items#noItalic`) — nie trzeba dopisywać `<italic:false>` w tekstach.
- Miejsca w kartach i GUI: `<player>`, `<number>`, `<balance>`, `<wallet>`, `<pin>`, `<created>`, `<type>`.
- Każdy przedmiot i każdy tekst ma własny wpis w `config.yml`; opisy obsługują placeholdery
  `<player>`, `<balance>`, `<wallet>`, `<pin>`, `<created>`, `<type>`.
- Ustawienie `banking.types.*.enabled: true` natychmiast włącza dany rodzaj konta w GUI
  (logika kont biznesowych/organizacyjnych/frakcyjnych to kolejne kroki).

### 12.3. Tabela w bazie

```sql
srb_bank_accounts  -- id, number, owner_name, owner_uuid, type, balance, pin_hash, pin_set_at, ...
                   -- UNIQUE (number)           -> krótki numer konta (namierzanie właściciela)
                   -- UNIQUE (owner_uuid, type) -> jedno konto danego rodzaju na gracza
                   -- idx_bank_owner_name      -> wyszukiwanie po nicku właściciela
```

Kolumny `number` i `owner_name` dokładają się automatycznie przy starcie; konta założone
wcześniej dostają losowe numery, a nicki właścicieli są uzupełniane z kont portfeli
(migracja + uzupełnienie, sekcja 12.8).

Tabela tworzy się automatycznie przy starcie (gdy `storage.auto-migrate: true`).
Konto bankowe jest **osobnym bytem** od portfela gracza (`srb_accounts`) — środki będą
przenoszone między nimi w kolejnych krokach (wpłata/wypłata na koncie).

### 12.4. Komendy (`/bankadmin npc ...`)

| Komenda | Opis |
|---|---|
| `/bankadmin npc create` | tworzy NPC „Bankier” w miejscu, w którym stoisz (konsola: lokalizacja z `config.yml`) |
| `/bankadmin npc remove` | usuwa NPC |
| `/bankadmin npc info` | nazwa, lokalizacja, informacja o obsłudze kliknięcia |
| `/bankadmin konto <numer>` | namierzenie właściciela po numerze konta (sekcja 12.8) |
| `/bankadmin atm karta [gracz]` | wydanie karty bankomatowej z konta gracza (sekcja 11.5) |

Uprawnienie: `bank.admin.npc` (domyślnie OP).
NPC można też postawić samodzielnie w FancyNpcs — plugin rozpoznaje go **po nazwie**
(`npc.name`), więc nie trzeba go tworzyć przez SkyRiseBank.

### 12.5. Jak przetestować

1. Zainstaluj **FancyNpcs** (2.11+ wymaga Javy 25) i wrzuć nowy `SkyRiseBank.jar`.
2. `/bankadmin npc create` (stań w miejscu, gdzie ma być NPC) albo postaw NPC o nazwie `Bankier`
   samodzielnie w FancyNpcs.
3. Kliknij NPC prawym przyciskiem → okno z **jedną ikonką na środku** („Stwórz konto bankowe”).
4. Kliknij ikonkę → dialog z prośbą o PIN; wpisz np. `1234` (zostanie odrzucony jako oczywisty),
   potem `7391` → konto utworzone, a w ekwipunku pojawia się **karta bankomatowa** z danymi konta.
5. W bazie pojawi się wiersz w `srb_bank_accounts` (`pin_hash` zaczyna się od `pbkdf2$50000$`).
6. Kliknij NPC ponownie → karta nie jest dublowana (komunikat o posiadanej karcie).
7. Idź do bankomatu **bez karty w ręce** i kliknij → komunikat „Przyłóż kartę bankomatową…”.
8. Trzymaj kartę w ręce i kliknij bankomat → dialog z PIN-em; podaj PIN → otwiera się **menu kont**.
9. **Konto osobiste** → panel konta (saldo, portfel, PIN: ustawiony, data); **Powrót** wraca do listy.
10. Konta **biznesowe / organizacyjne / frakcyjne** → komunikat „W trakcie prac” (czerwona notka).

> Uwaga: dialogi wymagają klienta 1.21.6+ (Paper Dialogs) — na Purpur 1.21.10 działa to natywnie.

### 12.6. Uwagi techniczne

- FancyNpcs jest **miękką zależnością** (`softdepend`), a całe API jest wołane wyłącznie przez
  `npc/NpcHook` w `try/catch` — brak pluginu nie psuje banku (NPC po prostu nie powstanie).
- NPC tworzony automatycznie (`npc.auto-create: true`) powstaje dopiero ~13 s po starcie serwera,
  bo rejestracja NPC w pierwszych sekundach po starcie jest niewskazana (zalecenie dokumentacji FancyNpcs).
- Duplikat NPC o tej samej nazwie rzuca wyjątek w FancyNpcs, dlatego `NpcHook` najpierw sprawdza,
  czy NPC już istnieje.
- Zapytania do bazy kont bankowych idą asynchronicznie (`Scheduler.supplyAsync`), a GUI otwierane jest
  już na wątku serwera (`Scheduler.sync`) — dotyczy to też odpowiedzi z dialogu.
- Karta bankomatowa rozpoznawana jest po **znaczniku w PDC przedmiotu** (działa też bez Nexo),
  a dodatkowo po modelu z `models.bank-card`; właściciel karty jest sprawdzany przy bankomacie.
- Postawienie bankomatu **nie wysyła komunikatów** — wpis trafia do rejestru w tle
  (jednorazowy komunikat o nowym wpisie włącza `atms.notify-on-place: true`).
- Błędny PIN przy bankomacie można podać `banking.pin.max-attempts` razy (domyślnie 3);
  po przekroczeniu limitu trzeba przyłożyć kartę ponownie.
- Kolejność przygotowania NPC wg API FancyNpcs: `NpcData` → `getNpcAdapter().apply(data)` →
  `registerNpc(npc)` → `npc.create()` → `npc.spawnForAll()`.

### 12.7. Karta bankomatowa i logowanie w bankomacie

Karta jest **przedmiotem** (model Nexo z `models.bank-card` albo materiał
`models.bank-card-fallback`, domyślnie `PAPER`). Zawiera w opisie dane konta,
ale **nigdy PIN-u**:

| Na karcie | Wartość |
|---|---|
| Właściciel | nick gracza |
| Numer konta | krótki, losowy numer (sekcja 12.8), np. `482 190` |
| Rodzaj | nazwa rodzaju konta (np. „Konto osobiste”) |
| Utworzono | data i godzina założenia konta |

Dane techniczne (znacznik karty, właściciel, numer, rodzaj, id konta) są zapisane
w **PDC przedmiotu**, dzięki czemu karta jest rozpoznawana nawet bez Nexo
i nie da się jej podmienić na zwykły papier.

**Zasady korzystania z bankomatu:**

1. Kartę trzeba **trzymać w ręce** (głównej albo pomocniczej) — bez karty bankomat nie reaguje.
2. Karta **nie musi należeć do klikającego** — jeśli znasz PIN, możesz korzystać z cudzej
   karty (saldo należy do konta-karty, nie do gracza).
3. Karta musi mieć **konto bankowe** (karta bez konta nie istnieje).
4. Po przyłożeniu karty trzeba podać **PIN**; poprawny PIN otwiera menu kont z tej karty.
5. Błędny PIN można podać `banking.pin.max-attempts` razy (domyślnie 3) — potem trzeba
   przyłożyć kartę ponownie.
6. Karta **bez PIN-u** (np. założona przez ekonomię Vault) nie wpuszcza do bankomatu —
   najpierw trzeba ustawić PIN u Bankiera.

Dodatkowe komendy administracyjne:

| Komenda | Opis |
|---|---|
| `/bankadmin atm karta` | wydaje kartę Tobie (na podstawie Twojego konta) |
| `/bankadmin atm karta <gracz>` | wydaje kartę wskazanemu graczowi |

Jeśli gracz nie ma konta, karta nie zostanie wydana (komunikat). Jeśli kartę już ma,
plugin nie dubluje przedmiotu.

### 12.8. Numer konta i wyszukiwanie kont (po numerze i po nicku)

Numer konta jest teraz **krótki i losowy** — domyślnie 6 cyfr (np. `482 190`), a długość
ustala `banking.number-length` (dozwolone 4-12; zmiana działa też dla nowych kont).

| Zagadnienie | Jak działa |
|---|---|
| Losowanie | `util/AccountNumbers#generate` — `SecureRandom`, pierwsza cyfra 1-9 (bez zer wiodących) |
| Unikalność | kolumna `number` ma w bazie `UNIQUE`, a plugin ponawia losowanie, gdy numer jest zajęty |
| Wyświetlanie | zawsze w grupach po 3 cyfry (`482 190`) — na karcie, w panelu konta i w komendach |
| Migracja | przy starcie dochodzi kolumna `number`, a istniejące konta dostają losowe numery |
| Namierzanie po numerze | `/bankadmin konto <numer>` pokazuje właściciela (nick + UUID), rodzaj konta, saldo, czy jest PIN i datę utworzenia |
| Wyszukiwanie po nicku | `/bankadmin konto <nick>` — najpierw dokładne dopasowanie (bez wielkości liter), potem po początku nicku (np. `jan` znajdzie `Janek123`); wypisuje wszystkie konta właściciela |
| Nick w bazie | kolumna `owner_name` — zapisywana przy zakładaniu konta i odświeżana przy każdym wejściu gracza (zmiana nicku nie psuje wyszukiwania) |
| Stare konta | brakujące nicki uzupełniają się przy starcie pluginu z kont portfeli (`bank_accounts`)
| Znaczenie argumentu | same cyfry = numer konta, cokolwiek innego = nick (np. `12345` vs `SkyRise`) |

Skąd administracja bierze numer: jest on **na karcie** (linia „Numer konta" w opisie) oraz
w bazie w kolumnie `number`. Numer można podać z myślnikami, spacjami lub bez — plugin go
normalizuje. Wyszukiwanie obsługują `BankAccountService#findByNumber` oraz
`BankAccountService#searchByOwnerName` (nick), więc inne pluginy mogą użyć tego samego
mechanizmu przez wskaźnik `plugin.bankAccounts()`.

Przykłady:

```
/sbadmin konto 482190        -> konto 482 190 i jego właściciel
/sbadmin konto 482 190       -> to samo (spacje są ignorowane)
/sbadmin konto SkyRise       -> wszystkie konta gracza SkyRise
/sbadmin konto sky          -> konta właścicieli, których nick zaczyna się od „sky"
```

---

## 13. Ekonomia Vault i EssentialsX

SkyRiseBank **udostępnia swoje saldo jako ekonomię Vault**, więc każdy plugin, który korzysta
z Vault (EssentialsX, sklepy, wypożyczalnie, nagrody za głosowanie), operuje na tym samym
salonie co bankomaty.

Jak to jest zrobione:

| Element | Szczegóły |
|---|---|
| Implementacja | `hook/VaultEconomy` — pełna implementacja `net.milkbowl.vault.economy.Economy` |
| Rejestracja | `bank/EconomyBridge` — usługa Vault zgłaszana z priorytetem `Highest` |
| Nazwa ekonomii | `SkyRiseBank` (celowo **inna** niż „EssentialsX Economy”) |
| Banki (`createBank`, …) | `NOT_IMPLEMENTED` — `hasBankSupport() = false` (konta bankowe robimy własnym systemem) |
| Zależność | VaultAPI 1.7 z JitPack, zakres `provided` — **nie jest pakowane do jara** |
| Bez Vault | plugin działa normalnie, tylko bez ekonomii dla innych pluginów |

**Dlaczego to działa z EssentialsX.** EssentialsX rejestruje własnego dostawcę ekonomii
(„EssentialsX Economy") z priorytetem `Normal`, ale przy starcie sprawdza, czy w Vault jest
**inna** ekonomia o wyższym priorytecie — jeśli tak, **przejmuje ją** (`EconomyLayers` →
`VaultLayer`). Ponieważ SkyRiseBank zgłasza się jako `Highest` i pod inną nazwą, to jego saldo
widzą `/balance`, `/pay`, `/eco`, bankomaty EssentialsX i inne pluginy. W EssentialsX **nie ma**
do tego żadnej opcji w `config.yml` — wystarczy, że plugin Vault jest na serwerze.

Konfiguracja (`config.yml`):

```yaml
integrations:
  vault: true             # false = wyłącz ekonomię dla Vault/EssentialsX
  vault-source: WALLET    # WALLET = portfel gracza (srb_accounts)
                          # CARD_ACCOUNT = konto osobiste, czyli karta bankomatowa
```

- `vault-source: WALLET` (domyślnie) — Vault i EssentialsX operują na portfelu gracza;
  bankomaty i karty dalej używają własnych kont.
- `vault-source: CARD_ACCOUNT` — cała ekonomia serwera (EssentialsX, sklepy) działa na
  **koncie-karcie**. Świetnie łączy się z Partią 3: gracz trzyma majątek na karcie i może ją
  przekazać razem z saldem.
- Konto dla Vault powstaje automatycznie przy pierwszej operacji (`ensureAccount` /
  `ensureCardAccount`) — konta założone w ten sposób **nie mają PIN-u**, więc karta z takiego
  konta wpuszcza do bankomatu dopiero po ustawieniu PIN-u u Bankiera.

Uwagi techniczne:

- API Vault jest synchroniczne, a magazyn SkyRiseBank asynchroniczny — mostek czeka na wynik
  z bazy maksymalnie **5 s** (po tym czasie operacja kończy się niepowodzeniem, a serwer nie
  zamarza). Odczyt salda korzysta najpierw z pamięci podręcznej portfela.
- Kwoty przechodzą przez ten sam mechanizm co komendy banku, więc limity salda, blokady kont
  i zdarzenie `BankTransactionEvent` działają również dla operacji z Vault.

Jak sprawdzić na serwerze:

1. `/balance` (EssentialsX) — powinno pokazać saldo SkyRiseBank.
2. `/pay <gracz> <kwota>` — przelew idzie przez bank (widać zmianę w `/bankadmin info <gracz>`).
3. `/eco give <gracz> <kwota>` — dodaje środki na to samo saldo.
4. `/bankadmin reload` po zmianie `integrations.vault-source` — przełącza źródło salda.
