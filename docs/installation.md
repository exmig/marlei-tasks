# MARLEI Tasks — Installation

**Ein Befehl, und danach steht die Oberfläche im Browser.** Was dieses
Dokument beschreibt, ist der Anfang; alles, was am laufenden Server zu
bedienen ist, steht in der **Hilfe** — dort, wo man es braucht.

**Zwei Wege, und keiner davon ist der Nebenfall:**

| | Wo es hingehört | Was es mitbringt |
|---|---|---|
| **Debian** (Ubuntu, Raspberry Pi OS) | Eine VM, ein alter Rechner, der Server neben MARLEI Boot | `systemd`, ein nginx davor, ein eigenes Dienstkonto |
| **Windows** 10 / 11 | Der Arbeitsplatz, auf dem sowieso gearbeitet wird | Aufgabenplanung, uvicorn hört selbst, kein nginx |

Die Anwendung ist auf beiden dieselbe. Was sich unterscheidet, ist der
Weg hinein — und drei Karten, die von der Maschine reden und dort andere
Quellen haben. **Wo eine Quelle fehlt, wird nichts behauptet:** Windows
führt etwa kein Lastmittel, und dann steht dort keine Kachel statt einer
geschätzten Zahl.

---

## 1. Was gebraucht wird

| | Debian | Windows |
|---|---|---|
| **System** | Debian, Ubuntu oder Raspberry Pi OS. Das Skript benutzt `apt-get`, `systemd` und die Paketnamen dieser Familie und bricht auf allem anderen ab, statt auf halbem Weg liegenzubleiben. | Windows 10 oder 11 (oder eine Serverfassung daneben), PowerShell 5.1 — beides ab Werk dabei. Dazu **Python 3.10 oder neuer**: Anders als auf Debian bringt Windows keins mit. |
| **Werkzeuge** | `git`, um den Stand zu holen. Auf einer schlanken Installation fehlt es und kommt mit `sudo apt-get install git`. Python bringt das System mit. | **Beides fehlt ab Werk: `git` und Python.** Windows 11 bringt `ssh`, `curl` und `tar` mit, Git nicht — und Python ebenso wenig. Wie sie hinkommen, steht bei *Installieren auf Windows*. |
| **Maschine** | Sehr wenig. Eine SQLite-Datei, ein Python-Prozess, ein nginx — 1 GB Arbeitsspeicher und ein Kern genügen. | Noch weniger, denn der nginx fällt weg. Was der Dienst tatsächlich braucht, steht danach auf **Server Health**. |
| **Netz** | Eine Adresse, die bleibt. Sie steht in `MARLEI_BASE_URL` und damit im Kopfband; ändert sie sich, ist ein erneuter Lauf die Antwort. | Dasselbe — und hier hängt mehr daran: **Aus dieser Adresse nimmt der Start den Port.** |
| **Rechte** | `root`, einmal. Danach läuft alles unter einem eigenen Dienstkonto ohne Anmelderecht. | Administrator, einmal. Danach läuft die Aufgabe unter dem eigenen Konto `marlei-tasks` ohne Anmelderecht. |

**Was nicht gebraucht wird:** eine Datenbank, ein Docker, ein Konto
irgendwo. Es gibt nichts einzurichten außer diesem einen Lauf.

---

## 2. Installieren auf Debian

```bash
git clone https://github.com/exmig/marlei-tasks.git marlei-tasks
cd marlei-tasks
sudo ./setup/linux/install.sh
```

Danach steht die Oberfläche unter **`http://<adresse>:8081/`**.

**8081 ist der Port dieses Werkzeugs**, nicht die 80 — und das ist eine
Entscheidung, keine Verlegenheit: Auf einer Maschine mit MARLEI Boot ist
die 80 vergeben, und ein Port, der mal so und mal so ist, gehört in kein
Lesezeichen. Wer die 80 will, sagt es:

```bash
sudo MARLEI_PORT=80 ./setup/linux/install.sh
```

Netzwerkkarte und Adresse erkennt das Skript selbst. Überschreiben geht
ebenso:

```bash
sudo MARLEI_IFACE=enp0s3 MARLEI_IP=192.168.178.31 ./setup/linux/install.sh
```

**Es ist wiederholbar.** Ein zweiter Lauf aktualisiert nur: Er kopiert
den neuen Stand, zieht die Abhängigkeiten nach, trägt neue Einstellungen
nach — und lässt die Ablage und alles, was Sie selbst geändert haben,
in Ruhe.

---

## 3. Installieren auf Windows

### Zuerst: Git und Python

**Windows bringt weder das eine noch das andere mit.** Git holt den Stand
und hält ihn später aktuell — `update.ps1` macht einen `git pull` —, und
Python ist das, worauf die Anwendung läuft. Beides liegt im
Paketmanager, der auf Windows 11 ab Werk dabei ist:

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
```

**Danach das PowerShell-Fenster schließen und ein neues öffnen.** Ein
laufendes Fenster kennt den erweiterten Suchpfad nicht; wer im selben
weitermacht, bekommt *„Der Befehl … wurde nicht gefunden"* und hält es
für einen Fehlschlag der Installation. Zur Probe im neuen Fenster:

```powershell
git --version
python --version
```

*Wer Python lieber von python.org holt: Beim Installieren **„Add
python.exe to PATH"** anhaken, sonst findet das Setup es nicht.*

### Dann das Setup

In einer PowerShell **als Administrator**, im geklonten Projekt:

```powershell
git clone https://github.com/exmig/marlei-tasks.git marlei-tasks
cd marlei-tasks
Set-ExecutionPolicy -Scope Process Bypass -Force
.\setup\windows\install.ps1
```

Danach steht die Oberfläche unter **`http://<adresse>:8081/`** — dieselbe
Zahl wie auf dem Server, aus demselben Grund. `-Port 80` geht auch.

### Die Zeile mit `Set-ExecutionPolicy`

**Ein frisches Windows führt keine Skripte aus.** `Get-ExecutionPolicy
-List` steht dort in allen Bereichen auf `Undefined`, und das heißt
`Restricted`: Der Aufruf oben bricht ohne diese Zeile mit *„die
Ausführung von Skripts ist auf diesem System deaktiviert"* ab, **bevor
eine Zeile des Setups läuft** — vor jeder Prüfung, vor jeder Meldung,
die dieses Dokument beschreibt.

`-Scope Process` gilt nur für dieses eine Fenster und steht in keiner
Registrierung; wird es geschlossen, ist nichts geblieben. **Damit gilt
sie für alles Weitere hier:** Jeder Aufruf von `install.ps1`,
`update.ps1` oder `uninstall.ps1` in diesem Dokument setzt voraus, dass
sie in derselben PowerShell gelaufen ist. Für einen einzelnen Aufruf —
etwa aus einer Verknüpfung oder einem anderen Skript heraus — geht auch
der Weg ohne Vorlauf:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup\windows\install.ps1
```

**Genau so startet die Aufgabenplanung den Dienst**, und deshalb ist das
hier kein Kunstgriff: Der laufende Server hat diese Frage nie, nur der
Mensch beim ersten Aufruf von Hand.

**Vom Rechner selbst ist sie sofort erreichbar, von einem anderen noch
nicht.** Windows blockt eingehende Verbindungen von Haus aus, und die
Firewall gehört der Maschine, nicht diesem Werkzeug — das Skript fasst
sie deshalb nur an, wenn man es verlangt:

```powershell
.\setup\windows\install.ps1 -Firewallregel
```

Das legt genau eine Regel an: eingehend, TCP, der eine Port, **und nur
für die Profile *Domäne* und *Privat*.** Ein Port, den man in einem
fremden WLAN offen hält, ist eine andere Entscheidung als einer im
eigenen Netz — diese Oberfläche spricht http, und ihr Kennwort ginge
dort im Klartext durch ein fremdes Netz. Wer sie auch dort braucht, sagt
es der Firewall selbst.

Ohne den Schalter nennt das Skript den Befehl zum Kopieren; die Karte
*Firewall* unter Einrichtung sagt dasselbe.

**Einmal verlangt, bleibt sie liegen — bis zum Entfernen.** Ein zweiter
Installationslauf und jedes Update lassen eine vorhandene Regel in Ruhe,
auch ohne den Schalter; das Skript sagt dann *„Nicht angefasst"*.
`uninstall.ps1` nimmt sie dagegen mit, und zwar die eigene und nur die
eigene. **Wer danach neu installiert, muss den Schalter also wieder
setzen** — sonst läuft die Oberfläche, antwortet auf der Maschine selbst,
und von einem anderen Rechner kommt nichts an. Das sieht aus wie ein
Fehler im Dienst und ist keiner:

```powershell
# nach einem uninstall, wenn sie wieder von außen erreichbar sein soll
.\setup\windows\install.ps1 -Firewallregel

# nachsehen, ob sie da ist
Get-NetFirewallRule -DisplayName "MARLEI Tasks*" | Select-Object DisplayName, Enabled, Profile
```

**Was wohin kommt:**

```
C:\Program Files\MARLEI Tasks\app    die Anwendung (eine Kopie, kein Verweis)
C:\Program Files\MARLEI Tasks\venv   die Abhängigkeiten
C:\Program Files\MARLEI Tasks\start.ps1
C:\ProgramData\MARLEI Tasks\tasks.db          die Ablage
C:\ProgramData\MARLEI Tasks\marlei-tasks.env  die Einstellungen
C:\ProgramData\MARLEI Tasks\log\              was uvicorn sagt
```

**Der Projektordner darf danach weg.** Er ist die Quelle, nicht die
Installation — genauso wie auf dem Server. Für ein Update braucht man ihn
wieder (Abschnitt 7).

**Die Ablage liest nur, wer Administrator ist** — und das Konto, unter
dem Tasks läuft. Das Datenverzeichnis bekommt die Vererbung abgeschnitten,
es bleiben `SYSTEM`, die Administratoren und `marlei-tasks` — das
Gegenstück zu `chmod 0750` auf dem Server. *In einer Aufgabenverwaltung
steht, woran eine Firma arbeitet.* Die Einstellungen darf das Konto nur
lesen: Darin steht der Hash des Kennworts.

### Das Konto `marlei-tasks`

**Tasks läuft unter einem eigenen lokalen Konto** — demselben Namen wie
auf dem Server, und nach derselben Regel für die ganze Suite: je Modul
eines. Es darf das Datenverzeichnis ändern und das Programm lesen, sonst
nichts; eine Lücke in Tasks bleibt damit eine Lücke in Tasks und wird
keine im ganzen Rechner.

- **Sein Kennwort kennt niemand.** Das Setup erzeugt es bei jedem Lauf
  neu und hinterlegt es nur in der Aufgabe.
- **Es kann sich nicht am Bildschirm anmelden**, weder vor Ort noch per
  Remotedesktop, und steht nicht auf dem Anmeldebildschirm.
- **Python muss „für alle Benutzer" installiert sein.** Ein Python im
  Profil eines Benutzers liest das Konto nicht; das Setup bricht dann ab
  und sagt es.
- **Ein Ausgang außerhalb des Datenverzeichnisses** — etwa ein
  Git-Repository — braucht ein Schreibrecht für das Konto. Das Setup
  vergibt es dort nicht ungefragt, sondern nennt den Befehl:

```powershell
icacls "D:\ablage\tasks-ausgang" /grant "marlei-tasks:(OI)(CI)M"
```

### Was die Anwendung startet

Eine **Aufgabe der Aufgabenplanung** namens `MARLEI Tasks`: beim
Hochfahren, unter dem Konto `marlei-tasks`, ohne dass jemand angemeldet
sein muss, mit Neustart nach einem Fehler und **ohne Zeitlimit** — die
Vorgabe der Aufgabenplanung wären drei Tage, und ein Dienst hat keins.

**Nur als Administrator** — auch das Nachsehen. Für einen gewöhnlichen
Benutzer gibt es die Aufgabe nicht; `Get-ScheduledTask` meldet dann, sie
sei nicht gefunden, obwohl sie läuft.

```powershell
Get-ScheduledTask   -TaskName "MARLEI Tasks" | Select-Object TaskName, State
Stop-ScheduledTask  -TaskName "MARLEI Tasks"
Start-ScheduledTask -TaskName "MARLEI Tasks"
```

**Anhalten beendet nicht, was die Aufgabe gestartet hat.** `start.ps1`
startet uvicorn als eigenen Prozess; der hält den Port weiter, nachdem
die Aufgabe als beendet gilt. Der nächste Start findet die Zahl dann
besetzt und landet im Protokoll statt in der Oberfläche — **ein
`Restart` ist das hier also nicht, und die Aufgabenplanung kennt auch
keins.**

**Zum Neustarten ist der einfache Weg ein zweiter Lauf von
`install.ps1`:** Er hält an, beendet, was aus dem Programmordner läuft,
wartet auf den Port und startet neu — und lässt Ablage, Kennwort und
Einstellungen in Ruhe. Von Hand geht es auch, aber nur als Administrator
(einem gewöhnlichen Benutzer bleibt `ExecutablePath` leer, und dann
findet die Zeile nichts):

```powershell
Stop-ScheduledTask -TaskName "MARLEI Tasks"
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object { $_.ExecutablePath -like "C:\Program Files\MARLEI Tasks\*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-ScheduledTask -TaskName "MARLEI Tasks"
```

**Warum kein echter Windows-Dienst:** Windows kennt Dienste, aber kein
Bordmittel, das ein beliebiges Programm zu einem macht — dafür bräuchte
es ein Fremdwerkzeug im Setup. Die Aufgabenplanung kann alles, was hier
gebraucht wird. Der Preis ist ehrlich genannt: kein Eintrag in
`services.msc`.

**Und kein nginx.** Auf dem Server nimmt er den Weg von außen ab, damit
der Port eine Sache der Maschine ist und nicht der Anwendung. Hier hört
uvicorn selbst darauf. Damit fällt der halbe Aufwand weg — und **eine
Zahl bekommt eine einzige Quelle:** Der Port steht in `MARLEI_BASE_URL`,
der Start liest ihn von dort, die Karte *Einstellungen* nennt ihn von
dort, und die Portliste unter *Firewall* auch.

### Wenn es nicht läuft

```
C:\ProgramData\MARLEI Tasks\log\meldungen.log
```

Dort steht, was uvicorn sagt. **Eine Aufgabe wirft die Ausgabe ihres
Programms sonst weg** — und damit genau das, was man beim ersten *es geht
nicht* braucht; ein `journalctl` gibt es hier nicht. Von jedem Start
bleibt der vorige Lauf als `.log.1` liegen: Der interessante ist der, der
gerade abgebrochen ist.

---

## 4. Neben MARLEI Boot auf derselben Maschine

**Das geht, und es ist der Regelfall auf einer Entwicklungsmaschine.**
Es betrifft nur die Debian-Seite — MARLEI Boot läuft nicht auf Windows.
Alles Trennbare ist getrennt:

| | MARLEI Boot | MARLEI Tasks |
|---|---|---|
| Anwendung | `127.0.0.1:8080` | `127.0.0.1:18081` |
| Benutzer | `pxeweb` | `marlei-tasks` |
| Verzeichnis | `/opt/pxeweb` · `/var/lib/pxeweb` | `/opt/marlei-tasks` · `/var/lib/marlei-tasks` |
| Einheit | `pxeweb.service` | `marlei-tasks.service` |
| Einstellungen | `/etc/pxeweb.env` | `/etc/marlei-tasks.env` |
| nginx-vhost | `sites-available/pxe` | `sites-available/marlei-tasks` |

**Der Weg von außen ist der einzige, den es nur einmal gibt.** Boots
vhost trägt `listen 80 default_server` und fängt damit alles ab, was auf
Port 80 hereinkommt. Ein zweiter vhost auf demselben Port wäre still
unerreichbar — und ein zweites `default_server` ließe nginx gar nicht
mehr starten. Dann stünde nicht dieses Werkzeug still, sondern der
Bootserver.

**Deshalb hört Tasks von vornherein auf 8081** — auf einer Maschine mit
Boot und auf einer ohne dieselbe Zahl. Es ist also nichts weiter zu tun
als der gewöhnliche Lauf.

**Und das Skript prüft trotzdem vorher und bricht ab, statt etwas zu
überschreiben** — es sieht nach, ob ein fremder Dienst auf dem Port
horcht, *und* ob ein anderer nginx-vhost ihn schon nennt. Den zweiten
Fall sieht man sonst nicht: nginx startet damit klaglos und schreibt die
doppelte Verwendung nur ins Log.

**Boots Dateien werden nicht angefasst.** Weder seine nginx-Konfiguration
noch seine Umgebungsdatei noch seine Einheit; die einzige gemeinsame
Sache ist der nginx-Dienst selbst.

---

## 5. Was danach zu tun ist

**Der erste Schritt steht auf dem Reiter Projekte:** ein Projekt anlegen
— Name, Beschreibung, Vision. **Und dazu mindestens einen Bereich**,
sonst nimmt die Sammlung nichts an.

Alles Weitere erklärt die **Hilfe**: ein Kapitel je Reiter, ein Abschnitt
je Karte, und das Fragezeichen in jedem Kartenkopf springt genau dorthin.

### Ohne Internet betreiben

**Das geht vollständig, und zwar von Haus aus.** Die Oberfläche lädt
keine Schrift und kein Stück ihrer selbst von einem fremden Server —
alles liegt bei der Installation daneben.

Die einzige Abfrage nach außen ist die Frage, ob es eine neuere Fassung
gibt: einmal in der Woche, bei GitHub, und es geht dabei nichts hin außer
dem Commit, auf dem diese Installation steht. Wer auch das nicht will,
legt den **Offline-Modus** um — *Einrichtung → Stand → Einschalten*.
Dann fragt diese Maschine nirgends mehr nach, und die Auswahl darunter
verschwindet.

**Nicht zu verwechseln mit *nie*.** Die Auswahl *nie / wöchentlich /
monatlich* sagt, wie oft von selbst nachgesehen wird; der Offline-Modus
sagt, dass hier überhaupt kein Ausgang ist — und gilt damit auch für
alles, was später einmal dazukommt.

### Das Kennwort

**Das Setup fragt bei der ersten Installation danach**, verdeckt und
zweimal. Es ist ein Kennwort für diese Installation, keines für eine
Person; eine Anmeldung gilt danach einen Monat. Ein Update fragt nicht
erneut, solange eines gesetzt ist.

**Leer lassen geht** — dann gibt es keine Anmeldung, und oben im Band
steht auf jeder Seite *ohne Kennwort*. Wer die Oberfläche im Netz
erreicht, darf dann alles.

**Vergessen heißt neu setzen, nicht wiederherstellen.** Gespeichert ist
nur ein Hash, und aus dem lässt sich das Kennwort nicht zurückrechnen. Neu
setzen darf, wer auf der Maschine Administrator ist:

```bash
sudo MARLEI_KENNWORT=neu ./setup/linux/install.sh    # Debian
```

```powershell
.\setup\windows\install.ps1 -Kennwort                # Windows, als Administrator
```

Der Bestand bleibt dabei unberührt, und jede bestehende Anmeldung endet —
wer das Kennwort neu setzt, weil es jemand anderes kennt, will genau das.

**Die Oberfläche spricht http.** Das Kennwort geht damit unverschlüsselt
durchs Netz; es hält das eigene Netz draußen, nicht ein fremdes. Deshalb
kein anderes Kennwort verwenden, das anderswo etwas öffnet — auch nicht
das des Windows-Kontos.

**Ein Blick lohnt sich noch auf die Umgebungsdatei:**

| | |
|---|---|
| Debian | `/etc/marlei-tasks.env` |
| Windows | `C:\ProgramData\MARLEI Tasks\marlei-tasks.env` |

| Wert | wofür |
|---|---|
| `MARLEI_KENNZEICHNUNG` | Steht hier ein Wort, ist dieser Server nicht die Produktion: Der Seitengrund wechselt auf Sand, und das Wort steht in der Kopfzeile. **Auf einer Entwicklungsmaschine gehört hier `Entwicklung` hinein.** |
| `MARLEI_EXPORT` | Wohin der Export schreibt. Zeigt der Pfad in ein Git-Repository, bekommt der Bestand damit eine Versionsgeschichte — bei unverändertem Bestand ist die Ausgabe byteweise dieselbe. |
| `MARLEI_BERICHT` | Wohin ein Fehlerbericht geht. |
| `MARLEI_KENNWORT_HASH` | Das Kennwort der Oberfläche, als Hash. **Nicht von Hand eintragen** — das Setup schreibt ihn, siehe *Das Kennwort* oben. |

Nach einer Änderung:

```bash
sudo systemctl restart marlei-tasks           # Debian
```

```powershell
.\setup\windows\install.ps1                   # Windows
```

**Unter Windows steht hier kein `Restart`**, weil es keinen gibt: Die
Aufgabe anzuhalten lässt uvicorn weiterlaufen. Warum der zweite Lauf die
Antwort ist, steht oben unter *Was die Anwendung startet*.

**Die Anwendung schreibt nie in diese Datei.** Die Karte *Einstellungen*
unter Einrichtung zeigt sie an und ändert nichts — sie beantwortet die
Frage, wie dieser Server aufgesetzt ist, ohne dass man sich an der
Maschine anmelden muss.

**Der Port steht nicht in dieser Tabelle** — und der Grund ist je System
ein anderer. Auf Debian gehört er dem nginx davor und steht in der
Umgebungsdatei überhaupt nicht; unter Windows steht er darin, aber als
Teil der Adresse. Ändern heißt beides Mal: erneut installieren, mit der
Zahl daneben.

```bash
sudo MARLEI_PORT=9090 ./setup/linux/install.sh
```

```powershell
.\setup\windows\install.ps1 -Port 9090
```

Die Karte *Einstellungen* sagt es ebenfalls und legt den Befehl zum
Kopieren daneben — den, der auf diesem System gilt. **Unter Windows
kommt ein Satz dazu:** Eine Firewallregel auf den alten Port zieht nicht
mit.

---

## 6. Sichern

**Eine Datei, und sie ist alles:**

```
/var/lib/marlei-tasks/tasks.db                Debian
C:\ProgramData\MARLEI Tasks\tasks.db          Windows
```

Wer sie kopiert, hat den ganzen Bestand. Unter Windows braucht das
Administratorrechte — die Ablage ist genau deshalb so eingerichtet.

**Der Export ist nicht dasselbe** — er schreibt den Text, lesbar ohne
dieses Werkzeug und geeignet für ein Repository, aber er ist keine
Sicherung der Ablage. Beides steht unter **Einrichtung**, mit Pfad und
Zustand.

> **Vor dem Löschen eines Projekts und vor der Werkseinstellung: erst
> ausgeben.** Ein Abbild holt man erneut, einen eingetragenen Gedanken
> nicht.

---

## 7. Aktualisieren

```bash
cd marlei-tasks
./setup/linux/update.sh
```

```powershell
cd marlei-tasks
.\setup\windows\update.ps1
```

**Ohne `sudo`, ohne Administrator** — `git pull` soll mit Ihrem Benutzer
und Ihrem Schlüssel laufen; für die Installation fragt das Skript selbst
nach. Unter Windows öffnet sich dafür ein zweites Fenster mit erhöhten
Rechten: **Windows erhöht Rechte nur für einen neuen Prozess, ein `sudo`
mitten in einer Sitzung gibt es nicht.**

Beide holen den neuen Stand, zeigen, was dazugekommen ist, und übernehmen
ihn.

**Übernommen wird, wenn die Installation zurückliegt — nicht nur, wenn
`git pull` etwas geholt hat.** Beide vergleichen den Stand, den die
Installation trägt (`VERSION` im Programmverzeichnis, derselbe, den die
Fußzeile zeigt), mit dem im geklonten Projekt. Ein `git pull` von Hand
vorher oder eine Installation, die beim letzten Mal abgebrochen ist,
holt das Update deshalb nach, statt „Schon aktuell“ zu melden. Enthält
das Projekt nicht committete Änderungen (`-dirty`), wird immer
übernommen.

**Den Port merkt sich die Installation selbst**, und zwar aus der
Quelle, die auf ihrem System gilt: Auf Debian steht er im installierten
vhost, unter Windows in `MARLEI_BASE_URL`. Ohne `MARLEI_PORT` bzw.
`-Port` nehmen `install.sh` und `install.ps1` den Port der bestehenden
Installation und erst dann die Vorgabe aus [`docs/ports.md`](ports.md).
*Ein zweiter Lauf soll nicht anders ausfallen als der erste* — auch
nicht, wenn man das Installationsskript direkt aufruft.

Von Hand geht es deshalb genauso, ohne die Zahl:

```bash
git pull && sudo ./setup/linux/install.sh
```

```powershell
git pull; .\setup\windows\install.ps1
```

Welcher Stand läuft, sagt die Fußzeile jeder Seite und die Karte
**Stand** unter Einrichtung.

---

## 8. Wieder entfernen

```bash
sudo ./setup/linux/uninstall.sh
```

```powershell
.\setup\windows\uninstall.ps1
```

**Der Bestand bleibt.** Weg sind danach die Anwendung, der Dienst
(Einheit bzw. Aufgabe) und der Weg von außen (nginx-vhost bzw.
Firewallregel). Die Ablage, die Einstellungen und der Ausgang bleiben
liegen — und das Skript sagt am Ende, wo. **Eine erneute Installation
nimmt alles wieder auf.**

**Alles bis auf den Weg von außen:** Unter Windows legt der nächste Lauf
die Firewallregel nur mit `-Firewallregel` wieder an (Abschnitt 3), und
unter Debian gehört der vhost zum Lauf ohnehin dazu. Bestand, Kennwort
und Einstellungen kommen von selbst zurück, die Erreichbarkeit nicht.

Beide sehen erst nach und schreiben hin, was sie gefunden haben; ist
nichts installiert, sagen sie das und tun nichts. Ein zweiter Lauf
schadet nicht.

**Was der Windows-Lauf der Reihe nach anfasst** — und in dieser
Reihenfolge, weil jede Stufe die nächste erst möglich macht:

| | |
|---|---|
| 1. Die Aufgabe anhalten und austragen | Sonst startet sie mitten im Aufräumen neu. |
| 2. Beenden, was aus dem Programmordner läuft | Das Anhalten allein beendet uvicorn nicht — siehe *Was die Anwendung startet*. |
| 3. Die Firewallregel entfernen | Nur die eigene, am Namen erkannt, nicht nach Portnummer. |
| 4. `C:\Program Files\MARLEI Tasks` löschen | Programm, venv, `start.ps1`. |
| 5. Das Konto `marlei-tasks` entfernen | Erst jetzt: Vorher könnte noch ein Prozess darunter laufen. |
| 6. Den Bestand melden | Er bleibt liegen, außer mit `-Bestand`. |

### Windows: das Konto geht mit, sein Profil bleibt oft bis zum Neustart

**Anders als auf Debian wird das Dienstkonto entfernt, auch wenn der
Bestand bleibt.** Dort gehören die Dateien dem Konto, und ein gelöschtes
Konto hinterließe Dateien, deren Besitzer eine Zahl ohne Namen ist. Unter
Windows gehören sie den Administratoren; das Konto hat nur ein Recht
darauf, und genau das trägt das Skript vorher aus dem Datenverzeichnis
aus. Eine erneute Installation legt ein neues Konto an und gibt ihm das
Recht wieder.

**Sein Profil unter `C:\Users\marlei-tasks` überlebt den Lauf jedoch
häufig.** Windows hält den Registrierungszweig eines Kontos, unter dem
die Aufgabenplanung gearbeitet hat, noch geladen — mitunter bis zum
Neustart, und erzwingen lässt sich das nicht. Das Skript wartet fünfzehn
Sekunden, löscht das Profil, sobald es frei ist, und sagt es, wenn nicht:

```
[!] Das Profil von marlei-tasks (C:\Users\marlei-tasks) ist noch da.
    Windows haelt es noch geladen und gibt es erst nach einem Neustart frei.
    Danach, als Administrator -- und VOR einer erneuten Installation:
      Get-CimInstance Win32_UserProfile -Filter "SID='S-1-5-21-…'" | Remove-CimInstance
```

**Diese Meldung ist kein Schönheitsfehler, sondern eine Bedingung für den
nächsten Installationslauf.** Steht der Ordner noch da, wenn
`install.ps1` ein Konto gleichen Namens anlegt, legt Windows das Profil
daneben: `C:\Users\marlei-tasks.<RECHNERNAME>`. Danach gibt es zwei
Ordner, einer davon tot — und keiner sagt einem, welcher.

**Der Weg ist deshalb: neu starten, nachsehen, dann erst installieren.**

```powershell
# Nach dem Neustart, als Administrator. Die SID steht in der Meldung;
# ohne sie geht es über den Pfad:
Get-CimInstance Win32_UserProfile |
    Where-Object { $_.LocalPath -like "*\marlei-tasks*" } |
    Remove-CimInstance

# Und nachsehen, dass wirklich nichts mehr dasteht:
Test-Path C:\Users\marlei-tasks
```

Manchmal räumt Windows das Profil beim Neustart selbst weg — am
19.09.2026 war es so. **Verlassen sollte man sich nicht darauf:** Am
20.09.2026 hielt eine frisch aufgesetzte Maschine es nach dem Entfernen
weiter geladen. Nachsehen kostet eine Zeile.

### Wenn auch der Bestand weg soll

```bash
sudo ./setup/linux/uninstall.sh --bestand
```

```powershell
.\setup\windows\uninstall.ps1 -Bestand
```

**Dann fragt das Skript zurück, und zwar nach einem Wort:** `Bestand`,
getippt. Der Schalter sagt, *dass* gelöscht wird; das Wort bestätigt,
dass Sie gelesen haben, *was* — dieselbe Überlegung wie beim Losungswort
der Werkseinstellung in der Anwendung.

> **Erst ausgeben, dann löschen.** Ein Abbild holt man erneut, einen
> eingetragenen Gedanken nicht. Der Ausgang steht unter **Einrichtung**.

Kann niemand antworten — in einer Pipeline, in einer Aufgabe —, brechen
beide ab, statt zu fragen oder einfach zu löschen.

### Was stehen bleibt, und warum

| | |
|---|---|
| **nginx** (Debian) | Es könnte auf dieser Maschine noch jemand anderes brauchen. Auf einer mit MARLEI Boot wäre ein `apt-get remove nginx` genau der Griff, der den Bootserver mitnimmt. Entfernt wird der eigene vhost, und nginx wird **neu geladen, nicht neu gestartet.** |
| **Python** (Windows) | Es war vorher da und gehört nicht diesem Werkzeug. Wer es nur dafür installiert hat, entfernt es über die Einstellungen von Windows. |
| **Das Dienstkonto** (Debian) | Es bleibt, **solange der Bestand bleibt** — und das ist keine Vorsicht, sondern nötig: Die Dateien unter `/var/lib` gehören ihm. Wer es entfernt und die Dateien liegen lässt, hat Dateien, deren Besitzer eine Zahl ohne Namen ist; die nächste Kontovergabe macht daraus jemand anderen. Geht der Bestand mit weg, geht das Konto mit. |

**Von Hand geht es auch.** Unter Debian sind es fünf Schritte, unter
Windows vier — sie stehen in den Skripten selbst, und bis zum 19.09.2026
standen sie hier. Zwei davon übersieht man dabei zuverlässig, und es sind
die beiden, die nicht im Programmverzeichnis liegen: **die Aufgabe in der
Aufgabenplanung und die Regel in der Firewall.** Beide tragen einen
Namen, den das Setup selbst gesetzt hat — deshalb darf ein Skript sie
anfassen, ohne zu raten.
