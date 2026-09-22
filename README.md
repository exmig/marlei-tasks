<img src="webui/static/exmig-logo.svg" alt="Exmig" width="200">

# MARLEI Tasks

*Teil der MARLEI Assistance Suite — herausgegeben von Exmig.*

**Ein Werkzeug für die Arbeit an einem Projekt, das man selbst betreibt.**
Was auffällt, kommt in die Sammlung. Was daraus wird, wird eine Aufgabe.
Woran es hängt, steht als Entscheidung — und am Ende lässt sich ablesen,
was entschieden wurde und warum.

Es läuft auf **Debian, Ubuntu oder Raspberry Pi OS** — als VM, auf einem
alten Rechner oder neben einem anderen Dienst — und auf **Windows 10 und
11**, auf dem Arbeitsplatz, auf dem sowieso gearbeitet wird. Kein Konto,
keine Datenbank, kein Docker: eine SQLite-Datei, ein Python-Prozess, und
auf dem Server ein nginx davor.

```
   ┌─────────────┐   was auffällt, roh
   │  Sammlung   │   Ideen und Fehler, noch unsortiert
   └──────┬──────┘
          │  wird eine Aufgabe — oder verworfen
          ▼
   ┌─────────────┐   woran gearbeitet wird
   │  Aufgaben   │   mit Abnahme: ohne sie ist nichts fertig
   └──────┬──────┘
          │  hängt an einem Stein
          ▼
   ┌─────────────┐   die Straße, und was dazwischenkam
   │Meilensteine │
   └─────────────┘

   ┌─────────────┐   quer zu allem: was entschieden wurde,
   │Entscheidun. │   getrennt vom Weg dorthin
   └─────────────┘
```

## Was es kann

- **Mehrere Projekte, eine Vorauswahl.** Der Reiter *Projekte* bestimmt,
  was auf allen anderen steht. Ein Projekt ist ein eigener Bestand —
  eigene Einträge, eigene Aufgaben, eigene Achsen.
- **Die Sammlung nimmt Rohes auf.** Was auffällt, wird eingetragen, ohne
  dass jemand vorher entscheiden muss, wie wichtig es ist: An einer rohen
  Beobachtung arbeitet niemand. Die Priorität vergibt eine **Durchsicht**,
  und die zählt auch dann, wenn alles so bleibt.
- **Ein FEHLER fragt nach fünf Angaben — und sperrt nicht.** Wann, woran,
  was tun, warum nicht, was es kostet. Fehlt etwas, steht der Eintrag als
  Befund oben, aber er ist da. Eine Regel, deren Weg teuer ist, wird
  umgangen.
- **Zusammenlegen statt Doppeln.** Zwei Einträge, die dasselbe meinen,
  werden zu einer Aufgabe — gefunden werden sie über die *Beschreibung*,
  nicht über den Titel.
- **Die Abnahme ist der Unterschied zwischen fertig und weggeklickt.**
  Eine Aufgabe ohne abgehakte Abnahme ist nicht erledigt, und das lässt
  sich auch nachträglich nicht umgehen.
- **Meilensteine als Straße, samt Umwegen.** Was dazwischenkam, wird
  notiert, sobald es passiert — nicht bei der Abnahme, sonst wird es aus
  dem Gedächtnis nachgetragen und ist wertlos.
- **Entscheidungen mit Weg und Ergebnis.** Oben steht, was entschieden
  wurde; darunter, wie man dahin kam. Der Weg zeigt, wie gründlich eine
  Entscheidung war.
- **Der Ausgang bleibt Text.** Jedes Projekt lässt sich als Markdown
  ausgeben — bei unverändertem Bestand byteweise dieselbe Ausgabe. Damit
  bekommt der Bestand eine Versionsgeschichte, wenn man ihn in ein
  Repository legt.
- **Server Health.** Was die Maschine tut und was der Dienst selbst
  braucht. Wo es keine Quelle gibt, wird nichts behauptet.

## Worauf es läuft

| | |
|---|---|
| **Debian und was davon abstammt** | Ubuntu und Raspberry Pi OS eingeschlossen. Das Skript liest `ID` und `ID_LIKE` aus `/etc/os-release` und verlangt `systemd`. Dahinter ein nginx, davor ein eigenes Dienstkonto. |
| **Windows 10 und 11** | Eine Aufgabe der Aufgabenplanung startet es beim Hochfahren, uvicorn hört selbst auf dem Port — **kein nginx, kein Fremdwerkzeug.** Gebraucht wird Python 3.10 oder neuer; alles andere bringt Windows mit. |
| **Alles andere** | Beide Skripte brechen ab, statt auf halbem Weg liegenzubleiben: Paketnamen und Dienstverwaltung sind dort andere. |

**Die Anwendung ist auf beiden dieselbe** — derselbe Quelltext, dieselbe
Ablage, dieselben neun Reiter. Anders ist der Weg hinein und das, was die
Maschine von sich erzählt: Prozessorlast und Speicher kommen unter Linux
aus `/proc`, unter Windows vom Kernel. **Wo eine Quelle fehlt, wird
nichts behauptet:** Windows führt kein Lastmittel, und dann steht dort
keine Kachel statt einer geschätzten Zahl.

**Einzelne Versionen sind nicht durchgespielt.** Was hier läuft, ist eine
Maschine und kein Testfeld — eine Rückmeldung von einem anderen System
ist deshalb mehr wert als eine Zeile Code.

**Ein Mensch, ein Bestand.** Die Ablage ist SQLite, und SQLite trägt
beliebig viele Leser, aber einen Schreiber zur Zeit. Für die Arbeit an
einem eigenen Projekt reicht das mit großem Abstand; wo mehrere
gleichzeitig schreiben, ist es die falsche Grundlage.

## Loslegen

| Schritt | Wo es steht |
|---|---|
| 1. Installieren — ein Befehl | [docs/installation.md](docs/installation.md) |
| 2. Bedienen | der Reiter **Hilfe** in der Anwendung selbst, oder [dieselbe Seite im Netz](https://exmig.github.io/marlei-tasks/) |
| 3. Warum es so gebaut ist | [docs/aufbau.md](docs/aufbau.md) und [docs/datenhaltung.md](docs/datenhaltung.md) |

```bash
git clone https://github.com/exmig/marlei-tasks.git marlei-tasks
cd marlei-tasks
sudo ./setup/linux/install.sh
```

Auf Windows, in einer PowerShell als Administrator:

```powershell
git clone https://github.com/exmig/marlei-tasks.git marlei-tasks
cd marlei-tasks
Set-ExecutionPolicy -Scope Process Bypass -Force
.\setup\windows\install.ps1
```

**Die dritte Zeile gehört dazu, und zwar auf jedem frischen Windows:**
Ab Werk führt es überhaupt keine Skripte aus, und ohne sie bricht der
Aufruf ab, bevor die erste Zeile des Setups läuft. `-Scope Process` gilt
nur für dieses eine Fenster — an der Einstellung des Systems ändert sich
nichts.

Danach steht die Oberfläche unter `http://<adresse>:8081/` — auf beiden
Systemen dieselbe Zahl, damit sie in ein Lesezeichen passt.

**Unter Windows ist sie zunächst nur vom Rechner selbst erreichbar.** Die
Firewall gehört der Maschine, nicht diesem Werkzeug; mit
`-Firewallregel` legt das Setup die eine Regel an, wenn man sie
ausdrücklich verlangt.

## Was heute so ist, kann morgen anders sein

Dieses Werkzeug wird benutzt, während es entsteht — es trägt den Bestand
seiner eigenen Entwicklung. Was hier steht, beschreibt den Stand auf
`main` und nicht eine Zusage für die nächste Fassung.

**Die Weboberfläche hat ein Kennwort, und nur eines.** Das Setup fragt
bei der Installation danach; es gibt keine Benutzer und keine Rechte, und
wer angemeldet ist, darf alles, was sie kann. Vergessen heißt neu setzen,
auf der Maschine mit Administratorrechten — siehe
[docs/installation.md](docs/installation.md). Wer das Kennwort leer lässt,
hat keine Anmeldung, und die Oberfläche sagt das auf jeder Seite.

**Die Oberfläche spricht http, nicht https.** Das Kennwort geht damit
unverschlüsselt durchs Netz. Sie gehört deshalb in ein Netz, dem du
vertraust, nicht ins offene Internet.

## Lizenz

**AGPL-3.0** — siehe [LICENSE](LICENSE).

Kurz und ohne Anspruch auf juristische Genauigkeit: Benutzen, verändern
und weitergeben ist erlaubt. Wer eine veränderte Fassung **als Dienst über
ein Netz anbietet**, muss den Quelltext dieser Fassung den Benutzern
zugänglich machen. Das ist der Unterschied zur GPL, und er ist hier
Absicht.

Beiträge in Form von Code werden derzeit **nicht** angenommen; der Grund
steht offen in [CONTRIBUTING.md](CONTRIBUTING.md). Rückmeldungen dagegen
sind sehr willkommen — **am besten aus der Anwendung heraus, Reiter
*Einrichtung*, Karte *Fehlerbericht*:** Der Knopf dort erzeugt einen Text
mit System, Version und Größe der Ablage, und der geht an
[support@exmig.de](mailto:support@exmig.de). Wer noch gar nicht so weit
gekommen ist, schreibt an dieselbe Adresse.

Eine Sicherheitslücke gehört nicht in ein offenes Issue —
[SECURITY.md](SECURITY.md) sagt, wohin.

## Wenn dieses Werkzeug bei Ihnen im Betrieb läuft

Für Fragen zu Lizenz, Unterstützung im Betrieb oder einer Anpassung an
Ihre Verhältnisse: **[kontakt@exmig.de](mailto:kontakt@exmig.de)**.
