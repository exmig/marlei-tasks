# ===========================================================================
# Installiert MARLEI Tasks auf Windows 10 oder 11.
#
# Aufruf im geklonten Projekt, in einer PowerShell ALS ADMINISTRATOR:
#     .\setup\windows\install.ps1
#
# Die Oberflaeche hoert auf **Port 8081** -- dieselbe Zahl wie auf der
# Linux-Seite, und aus demselben Grund: Ein Port, der mal so und mal so
# ist, gehoert in kein Lesezeichen. Anders geht auch:
#     .\setup\windows\install.ps1 -Port 80
#
# Die Regel in der Windows-Firewall wird NICHT ungefragt gesetzt. Wer sie
# will, verlangt sie:
#     .\setup\windows\install.ps1 -Firewallregel
#
# Das Skript ist wiederholbar: ein zweiter Aufruf aktualisiert nur.
#
# ---------------------------------------------------------------------------
# WAS HIER ANDERS IST ALS AUF DEM SERVER, UND WARUM
#
# **Kein nginx.** Auf dem Server nimmt er den Weg von aussen ab, damit der
# Port eine Sache der Maschine ist und nicht der Anwendung. Hier hoert
# uvicorn selbst auf dem Port -- ein nginx unter Windows waere ein zweites
# Stueck Software, das jemand pflegen, aktualisieren und verstehen muss,
# fuer einen Nutzen, den es auf einem Arbeitsplatz nicht gibt. Damit
# faellt der halbe Aufwand dieses Skripts weg: kein vhost, keine
# Portpruefung gegen fremde vhosts, kein Standardseite-Abschalten.
#
# **Ein eigenes Konto: marlei-tasks.** Derselbe Name wie das Systemkonto
# auf der Linux-Seite, und dieselbe Regel fuer die ganze Suite: je Modul
# eines. Bis zum 19.09.2026 lief die Aufgabe als SYSTEM; eine Luecke in
# Tasks waere eine Luecke im ganzen Rechner gewesen. Das Konto darf das
# Datenverzeichnis aendern, das Programm lesen -- und sonst nichts. Sein
# Kennwort erzeugt dieses Skript bei jedem Lauf neu, und niemand kennt es.
# Einzelheiten: files/konto.ps1.
#
# **Eine Aufgabe statt einer Dienst-Einheit.** Windows kennt Dienste, aber
# kein Bordmittel, das ein beliebiges Programm zu einem macht -- dafuer
# braucht es ein Fremdwerkzeug. Die Aufgabenplanung kann alles, was hier
# gebraucht wird: beim Systemstart, ohne angemeldeten Benutzer, mit
# Neustart nach einem Fehler und ohne Zeitlimit.
# ===========================================================================
[CmdletBinding()]
param(
    # Port der Oberflaeche. Ohne Angabe der Port der bestehenden
    # Installation, sonst 8081 wie auf dem Server (docs/ports.md).
    [int]$Port = 0,

    # Die Adresse, unter der die Maschine im Netz erreichbar ist. Ohne
    # Angabe erkannt -- ueber die Karte mit der Standardroute.
    [string]$IP = "",

    # Legt die eine eingehende Regel in der Windows-Firewall an. **Ohne
    # diesen Schalter wird die Firewall nicht angefasst** -- sie gehoert
    # der Maschine, nicht diesem Werkzeug; das Skript nennt dann den
    # Befehl zum Kopieren.
    [switch]$Firewallregel,

    # Welches Python das venv bauen soll. Ohne Angabe gesucht.
    [string]$Python = "",

    # Das Kennwort der Oberflaeche neu setzen. Ohne diesen Schalter wird
    # nur gefragt, wenn noch keines gesetzt ist. **Das Kennwort selbst ist
    # kein Parameter** -- es wird verdeckt abgefragt; auf der Befehlszeile
    # stuende es im Verlauf der Konsole.
    [switch]$Kennwort
)

# ---------------------------------------------------------------------------
# "Continue" UND NICHT "Stop", und das ist ein Fund und keine Nachlaessigkeit
#
# **Ein fremdes Programm, das auf die Fehlerausgabe schreibt, ist kein
# Fehler.** git schreibt dort seinen Fortschritt hin, pip seine Hinweise,
# robocopy seine Meldungen. Mit ``$ErrorActionPreference = "Stop"`` macht
# PowerShell daraus einen abbrechenden Fehler -- **mitten in einem Lauf,
# der gerade alles richtig macht.**
#
# Aufgefallen beim Bauen, am unscheinbarsten Fall: ``git rev-parse`` in
# einem Ordner ohne Repository. Die freundliche Meldung darunter kam nie,
# stattdessen ein PowerShell-Fehlerbericht mit Zeilennummern -- die
# Auskunft, die jemandem hilft, war von der Maschinerie verdeckt.
#
# Geprueft wird deshalb, was zaehlt: der Rueckgabewert. ``$LASTEXITCODE``
# steht nach jedem Aufruf, auf den es ankommt, und jede Stelle, die
# abbrechen soll, bricht selbst ab -- mit einem Satz, der sagt, was zu tun
# ist. Das ist derselbe Umgang wie auf der Linux-Seite, wo die Skripte
# ``if ! git pull`` schreiben und nicht auf ``set -e`` hoffen.
$ErrorActionPreference = "Continue"
Set-StrictMode -Version 2.0

$SRC_DIR = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$APP_DIR = Join-Path $env:ProgramFiles "MARLEI Tasks"
$DATA_DIR = Join-Path $env:ProgramData "MARLEI Tasks"
$ENV_DATEI = Join-Path $DATA_DIR "marlei-tasks.env"
$VORLAGE = Join-Path $PSScriptRoot "files\marlei-tasks.env.example"
$AUFGABE = "MARLEI Tasks"
$REGELNAME = "MARLEI-Tasks"
# Das Konto, unter dem die Aufgabe laeuft -- derselbe Name wie DIENST in
# setup/linux/install.sh.
$KONTO = "marlei-tasks"

# Wer aus unserem Verzeichnis laeuft und wer auf einem Port hoert -- an
# einer Stelle, weil uninstall.ps1 dasselbe wissen muss. Warum das eine
# eigene Datei ist, steht dort im Kopf: Es ist der Fall vom 19.09.2026.
. (Join-Path $PSScriptRoot "files\eigene-prozesse.ps1")
# Das Konto samt Kennwort, Rechten und Gruppe -- ebenfalls eine eigene
# Datei, weil uninstall.ps1 es wieder abbauen muss.
. (Join-Path $PSScriptRoot "files\konto.ps1")

function Log($text) { Write-Host "`n==> $text" -ForegroundColor Cyan }
function Warnung($text) { Write-Host "[!] $text" -ForegroundColor Yellow }
function Abbruch($text) { Write-Host "[X] $text" -ForegroundColor Red; exit 1 }

# --------------------------------------------------------------------------
# Laeuft das hier auf einem System, das dieses Skript kennt?
# --------------------------------------------------------------------------
#
# Es kennt Windows 10 und 11 (und die Serverfassungen daneben) -- es
# benutzt die Aufgabenplanung, robocopy und die NetSecurity-Befehle. Auf
# allem anderen bricht es ab, statt auf halbem Weg liegenzubleiben:
# dieselbe Haltung wie die Linux-Seite gegenueber allem, was nicht Debian
# ist.
if ($env:OS -ne "Windows_NT") {
    Abbruch "Dieses Skript ist fuer Windows. Auf einem Linux gilt setup/linux/install.sh."
}
if (-not (Test-Path -LiteralPath (Join-Path $SRC_DIR "webui"))) {
    Abbruch @"
$SRC_DIR ist kein Projektordner (webui\ fehlt).
    Aufrufen aus dem geklonten Projekt:  <projekt>\setup\windows\install.ps1
"@
}

$ich = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $ich.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Abbruch @"
Bitte als Administrator ausfuehren.
    Dieses Skript schreibt nach $env:ProgramFiles, legt das Konto $KONTO
    und eine Aufgabe an und setzt die Rechte auf dem Datenverzeichnis.
    In einer PowerShell mit "Als Administrator ausfuehren" erneut starten.
"@
}
foreach ($befehl in @("Register-ScheduledTask", "Get-NetTCPConnection")) {
    if (-not (Get-Command $befehl -ErrorAction SilentlyContinue)) {
        Abbruch @"
$befehl fehlt -- dieses Windows ist zu alt fuer dieses Skript.
    Gebraucht werden die Aufgabenplanung und die Netzbefehle aus
    Windows 8 / Server 2012 oder neuer.
"@
    }
}

# **Windows 11 meldet sich als Version 10, und die Build-Nummer ist die
# einzige Stelle, an der es sich unterscheidet** (ab 22000). Auf der
# ersten echten Maschine stand hier "Windows 10 (Build 22631)" -- ein
# Widerspruch in einer Zeile, und daneben nennt die Karte Serverdetails
# dasselbe System richtig, weil Python die Schwelle kennt. Zwei Quellen,
# die auseinandergehen, sind genau das, was dieses Produkt sonst
# vermeidet.
$fassung = [System.Environment]::OSVersion.Version
$name = if ($fassung.Build -ge 22000) { "11" } else { "$($fassung.Major)" }
Write-Host ("    System        : Windows {0} (Build {1})" -f $name, $fassung.Build)
Write-Host ("    PowerShell    : {0}" -f $PSVersionTable.PSVersion)

# --------------------------------------------------------------------------
Log "Python suchen"
# --------------------------------------------------------------------------
#
# **Gesucht wird der Pfad, nicht der Befehl.** "py -3" ist ein Starter, der
# je nach Installation ein anderes Python nimmt; die Aufgabe laeuft
# spaeter als $KONTO und muss genau das Python finden, mit dem das venv
# gebaut wurde. Also wird hier einmal gefragt, welches es wirklich ist --
# und danach nur noch dieser Pfad benutzt.
function Finde-Python {
    param([string]$Vorgabe)
    $kandidaten = @()
    if ($Vorgabe) { $kandidaten += ,@($Vorgabe, @()) }
    $kandidaten += ,@("py", @("-3"))
    $kandidaten += ,@("python", @())
    $kandidaten += ,@("python3", @())
    foreach ($k in $kandidaten) {
        $befehl, $argumente = $k
        if (-not (Get-Command $befehl -ErrorAction SilentlyContinue)) { continue }
        try {
            $pfad = & $befehl @argumente -c "import sys; print(sys.executable)" 2>$null
        } catch { continue }
        if ($LASTEXITCODE -ne 0 -or -not $pfad) { continue }
        $pfad = ($pfad | Select-Object -First 1).Trim()
        if ($pfad -and (Test-Path -LiteralPath $pfad)) { return $pfad }
    }
    return ""
}

$PY = Finde-Python $Python
if (-not $PY) {
    Abbruch @"
Kein Python gefunden.
    Gebraucht wird Python 3.10 oder neuer -- von python.org oder aus dem
    Microsoft Store. Danach dieses Skript erneut aufrufen; mit einem
    bestimmten Python geht es auch:
      .\setup\windows\install.ps1 -Python "C:\Python313\python.exe"
"@
}

# Alles, was von diesem Python zu wissen ist, in einem Aufruf.
#
# **FTS5 ist keine Formsache:** Ohne die Erweiterung findet die Suche ueber
# die Sammlung nichts -- die Anwendung laeuft weiter und sagt es beim
# Start, aber die Buendelprobe, also der Griff, um den es in diesem
# Werkzeug geht, fehlt dann.
#
# ``Py_GIL_DISABLED`` sagt, ob es die Fassung ohne globale
# Interpretersperre ist -- siehe unten, das ist der Grund, warum es diese
# Frage hier ueberhaupt gibt.
function Frag-Python {
    param([string]$Exe)
    $auskunft = & $Exe -c @"
import sqlite3, sys, sysconfig
v = sys.version_info
fts = True
try:
    sqlite3.connect(':memory:').execute('CREATE VIRTUAL TABLE t USING fts5(x)')
except Exception:
    fts = False
print('%d.%d.%d|%s|%s|%s' % (
    v[0], v[1], v[2], 'fts5' if fts else 'ohne-fts5', sqlite3.sqlite_version,
    'ohne-gil' if sysconfig.get_config_var('Py_GIL_DISABLED') else 'mit-gil'))
"@
    if (-not $auskunft) {
        # Keine Zeile zurueck heisst: Dieses Python startet, sagt aber
        # nichts -- eine kaputte Installation. Lieber hier abbrechen als
        # drei Schritte spaeter an einer Stelle, die davon nichts weiss.
        Abbruch @"
$Exe antwortet nicht auf eine einfache Frage.
    Gepruefte Frage war die Python-Version. Von Hand nachsehen:
      & "$Exe" -c "import sys; print(sys.version)"
"@
    }
    $teile = ($auskunft | Select-Object -First 1).Trim().Split("|")
    return @{
        Version = [version]$teile[0]
        FTS5 = ($teile[1] -eq "fts5")
        SQLite = $teile[2]
        OhneGIL = ($teile[3] -eq "ohne-gil")
    }
}

$info = Frag-Python $PY

# **NICHT DIE FASSUNG OHNE GIL, WENN DANEBEN DIE GEWOEHNLICHE LIEGT.**
#
# "py -3" nimmt, was im Starter als Vorgabe eingetragen ist -- und das war
# auf der Maschine, auf der dieses Skript entstanden ist, python3.14t.exe:
# die Fassung ohne globale Interpretersperre. Sie ist neu, und fuer
# Fremdpakete gibt es dafuer nicht immer eine fertige Rad-Datei; pip
# versucht dann zu bauen und bricht mit einer Meldung ueber einen
# fehlenden Compiler ab. Das Merkwuerdige daran waere, DASS es abbricht,
# obwohl dasselbe Python im Projektordner laengst laeuft -- dort steht
# naemlich die gewoehnliche Fassung im venv.
#
# Gefragt wird das Python selbst, nicht der Dateiname: Wie eine Fassung
# heisst, ist eine Verabredung, ``Py_GIL_DISABLED`` eine Tatsache.
if ($info.OhneGIL) {
    $gewoehnlich = Join-Path (Split-Path -Parent $PY) "python.exe"
    if ((Test-Path -LiteralPath $gewoehnlich) -and $gewoehnlich -ne $PY) {
        $andere = Frag-Python $gewoehnlich
        if (-not $andere.OhneGIL) {
            Write-Host "    Python ohne GIL uebersprungen: $PY"
            $PY = $gewoehnlich
            $info = $andere
        }
    }
}

$pyversion = $info.Version
Write-Host "    Python        : $pyversion  ($PY)"
Write-Host "    SQLite        : $($info.SQLite)  $(if ($info.FTS5) { 'fts5' } else { 'ohne-fts5' })"
if ($pyversion -lt [version]"3.10") {
    Abbruch @"
Python $pyversion ist zu alt -- gebraucht wird 3.10 oder neuer.
    Der Quelltext benutzt Schreibweisen, die es vorher nicht gab
    (etwa "int | None").
"@
}
if (-not $info.FTS5) {
    Warnung @"
Dieses Python bringt SQLite ohne FTS5 mit -- die Suche ueber die Sammlung
    steht dann nicht zur Verfuegung, und damit die Buendelprobe nicht.
    Die Anwendung laeuft trotzdem und sagt es beim Start.
"@
}
if ($info.OhneGIL) {
    Warnung @"
Dieses Python ist die Fassung ohne globale Interpretersperre
    (Py_GIL_DISABLED), und eine gewoehnliche liegt nicht daneben. Fuer sie
    gibt es nicht zu jedem Fremdpaket eine fertige Rad-Datei -- bricht die
    Installation der Abhaengigkeiten gleich ab, ist das der erste Verdacht.
"@
}
# **Seit dem eigenen Konto ein Abbruch und keine Warnung mehr.** Solange
# die Aufgabe als SYSTEM lief, las sie jedes Profil; das Konto $KONTO
# liest keines ausser seinem eigenen. Das venv steht auf diesem Python --
# die Aufgabe startete, und uvicorn kaeme nie hoch.
if ($PY -like (Join-Path $env:SystemDrive "Users\*")) {
    Abbruch @"
Dieses Python liegt im Profil eines Benutzers:
      $PY
    Die Aufgabe laeuft unter dem Konto $KONTO, und das darf in fremde
    Profile nicht hineinsehen -- der Dienst startete nie. Gebraucht wird
    ein Python "fuer alle Benutzer" (Installer: "Install for all users"),
    dann erneut:  .\setup\windows\install.ps1 -Python "C:\Program Files\Python3xx\python.exe"
"@
}

# --------------------------------------------------------------------------
Log "Adresse und Port"
# --------------------------------------------------------------------------
#
# **Ohne -Port gilt der Port der bestehenden Installation, erst dann die
# Vorgabe.** Bis September 2026 hiess ohne Angabe immer 8081 -- ein
# zweiter Lauf auf einer Installation mit anderem Port stellte sie still
# zurueck, und jedes Lesezeichen zeigte ins Leere. Gelesen wird hier und
# nicht in update.ps1: Die Umgebungsdatei liest nur ein Administrator
# (weiter unten, "Die Einstellungen darf das Konto lesen"), und dieses
# Skript ist einer. Die Tabelle der Vorgaben: docs/ports.md.
$VORGABE_PORT = 8081
$PORT_HER = "angegeben"
if ($Port -eq 0) {
    $Port = $VORGABE_PORT
    $PORT_HER = "Vorgabe, docs/ports.md"
    if (Test-Path -LiteralPath $ENV_DATEI) {
        foreach ($z in @(Get-Content -LiteralPath $ENV_DATEI -Encoding UTF8)) {
            if ($z -match '^MARLEI_BASE_URL=[a-z]+://[^:/]+:(\d+)') {
                $Port = [int]$Matches[1]
                $PORT_HER = "wie bisher, aus MARLEI_BASE_URL"
            } elseif ($z -match '^MARLEI_BASE_URL=[a-z]+://[^:/]+/?$') {
                # Eine Adresse ohne Doppelpunkt heisst 80 -- das ist keine
                # Vorgabe, sondern die Bedeutung einer Adresse.
                $Port = 80
                $PORT_HER = "wie bisher, aus MARLEI_BASE_URL"
            }
        }
    }
}
if ($Port -lt 1 -or $Port -gt 65535) { Abbruch "-Port $Port ist keine Portnummer." }

$SERVER_IP = $IP
if (-not $SERVER_IP) {
    # Die Karte, ueber die diese Maschine hinauskommt -- also die mit der
    # Standardroute und der kleinsten Metrik. Dieselbe Frage wie
    # "ip -4 route show default" auf der anderen Seite.
    $route = Get-NetRoute -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue |
             Sort-Object RouteMetric, ifMetric | Select-Object -First 1
    if ($route) {
        $SERVER_IP = (Get-NetIPAddress -InterfaceIndex $route.ifIndex `
                        -AddressFamily IPv4 -ErrorAction SilentlyContinue |
                      Where-Object { $_.IPAddress -ne "127.0.0.1" } |
                      Select-Object -First 1).IPAddress
    }
}
if (-not $SERVER_IP) {
    Abbruch @"
Keine IPv4-Adresse mit Standardroute gefunden.
    Ueberschreiben mit:  .\setup\windows\install.ps1 -IP 192.168.178.31
"@
}
$ADRESSE = if ($Port -eq 80) { "http://$SERVER_IP" } else { "http://${SERVER_IP}:$Port" }
Write-Host "    Server-IP     : $SERVER_IP"
Write-Host "    Port          : $Port  ($PORT_HER)"

# --------------------------------------------------------------------------
Log "Laeuft schon etwas, und ist der Port frei?"
# --------------------------------------------------------------------------
#
# **Zuerst die eigene Aufgabe anhalten, dann fragen.** Beim zweiten Lauf
# haelt die laufende Anwendung den Port naemlich selbst -- wer hier stumpf
# prueft, bricht an seiner eigenen Installation ab.
$vorhanden = Get-ScheduledTask -TaskName $AUFGABE -ErrorAction SilentlyContinue
if ($vorhanden) {
    Write-Host "    Aufgabe ist da -- wird angehalten."
    Stop-ScheduledTask -TaskName $AUFGABE -ErrorAction SilentlyContinue
}

# **ERST BEENDEN, WAS UNS GEHOERT, DANN URTEILEN.** Die Aufgabe
# anzuhalten beendet nicht, was sie gestartet hat: start.ps1 startet
# uvicorn als eigenen Prozess, und der haelt den Port weiter. Auf der
# ersten echten Maschine hat genau das den zweiten Lauf abbrechen lassen --
# mit der Meldung, auf dem Port hoere "etwas anderes", und gemeint war die
# eigene Anwendung.
if ($vorhanden) {
    $beendet = Beende-Eigene $APP_DIR
    if ($beendet -eq 0) { Write-Host "    (nichts mehr aus $APP_DIR)" }
}

# Danach warten: Ein Port wird nicht in demselben Augenblick frei, in dem
# der Prozess endet.
for ($versuch = 0; $versuch -lt 10; $versuch++) {
    if (-not (Port-Horcher $Port)) { break }
    Start-Sleep -Milliseconds 500
}

# Und jetzt die Frage, die bleibt: Hoert da noch etwas, und was?
#
# **Drei Antworten, und die dritte ist die, die vorher fehlte.** Eigen --
# dann ist es ein Ueberrest, der sich nicht beenden liess. Fremd -- dann
# bricht dieses Skript ab, statt einen fremden Dienst zu verdecken
# (verdecken, nicht ueberschreiben: Zwei Programme auf einem Port heisst,
# dass eines davon unerreichbar ist). Oder **nicht zuordenbar** -- dann
# wird das gesagt und nicht geraten. Vorher galt "weiss nicht" als
# "fremd", und das war die halbe Fehlmeldung.
$horcher = Port-Horcher $Port
if ($horcher) {
    $eigene = @($horcher | Where-Object { Gehoert-Uns $_ $APP_DIR })
    $fremde = @($horcher | Where-Object { -not (Gehoert-Uns $_ $APP_DIR) -and $_.Zuordenbar })
    $unklare = @($horcher | Where-Object { -not $_.Zuordenbar })

    if ($fremde) {
        Abbruch @"
Auf Port $Port hoert ein fremder Dienst:
    $(($fremde | ForEach-Object { "$($_.Name) (PID $($_.Id))" }) -join ', ')
    Dieses Skript faengt ihn nicht ab. Einen anderen Port waehlen:
      .\setup\windows\install.ps1 -Port 9090
"@
    }
    if ($unklare) {
        Abbruch @"
Auf Port $Port hoert ein Prozess, den dieses Skript nicht zuordnen kann:
    PID $(($unklare | ForEach-Object { $_.Id }) -join ', ')
    Weder Pfad noch Befehlszeile waren zu erfahren -- **und im Zweifel
    wird hier nichts beendet.** Nachsehen mit:
      Get-CimInstance Win32_Process -Filter "ProcessId=$($unklare[0].Id)" |
        Select-Object ProcessId, Name, ExecutablePath, CommandLine
    Oder einen anderen Port waehlen:
      .\setup\windows\install.ps1 -Port 9090
"@
    }
    if ($eigene) {
        Abbruch @"
Auf Port $Port hoert noch die eigene Anwendung, und sie liess sich nicht
    beenden:
    $(($eigene | ForEach-Object { "$($_.Name) (PID $($_.Id))" }) -join ', ')
    Von Hand:  Stop-Process -Id $($eigene[0].Id) -Force
"@
    }
}
Write-Host "    Port $Port ist frei."

# --------------------------------------------------------------------------
Log "Konto $KONTO"
# --------------------------------------------------------------------------
#
# Bei jedem Lauf: Konto anlegen oder das vorhandene nehmen, Kennwort neu,
# Rechte nachziehen. **Das Kennwort bleibt nur bis zur Aufgabe in dieser
# Variablen** und wird danach geleert.
$war_da = Konto-Da $KONTO
$KONTO_KENNWORT = Neues-Kennwort
try {
    $KONTO_SID = Konto-Einrichten $KONTO $KONTO_KENNWORT "MARLEI Tasks -- Konto der Aufgabe"
} catch {
    Abbruch "Das Konto $KONTO liess sich nicht einrichten: $($_.Exception.Message)"
}
if (-not $KONTO_SID) { Abbruch "Das Konto $KONTO ist nicht nachzuschlagen." }
Write-Host ("    {0}, Kennwort neu gesetzt; keine Anmeldung am Bildschirm." -f
            $(if ($war_da) { "vorhanden" } else { "angelegt" }))

# --------------------------------------------------------------------------
Log "Verzeichnisse und Rechte"
# --------------------------------------------------------------------------
New-Item -ItemType Directory -Force -Path $APP_DIR, $DATA_DIR | Out-Null

# Die Ablage darf niemand sonst lesen: In einer Aufgabenverwaltung steht,
# woran eine Firma arbeitet. Das ist das Gegenstueck zu "chmod 0750" auf
# der anderen Seite -- die Vererbung wird abgeschnitten, und es bleiben
# SYSTEM, die Administratoren und das Konto der Aufgabe. Das Konto darf
# aendern, nicht die Rechte vergeben: Aendern (M) statt Vollzugriff (F).
#
# **Mit SIDs und nicht mit Namen:** Auf einem deutschen Windows heisst die
# Gruppe "Administratoren", auf einem englischen "Administrators" -- ein
# icacls mit dem falschen Namen scheitert, und die Rechte blieben, wie sie
# waren. S-1-5-18 ist SYSTEM, S-1-5-32-544 die lokalen Administratoren.
$null = & icacls.exe $DATA_DIR /inheritance:r /grant:r `
    "*S-1-5-18:(OI)(CI)F" "*S-1-5-32-544:(OI)(CI)F" "*${KONTO_SID}:(OI)(CI)M" 2>&1
if ($LASTEXITCODE -ne 0) {
    Warnung "Die Rechte auf $DATA_DIR liessen sich nicht setzen (icacls: $LASTEXITCODE)."
} else {
    Write-Host "    $DATA_DIR -- SYSTEM, Administratoren und $KONTO."
}

# --------------------------------------------------------------------------
Log "Anwendung kopieren"
# --------------------------------------------------------------------------
#
# /MIR spiegelt: Was im Quellordner weg ist, ist danach auch hier weg --
# dasselbe wie "rsync --delete". Deshalb liegt das venv NEBEN app\ und
# nicht darin, sonst raeumte der naechste Lauf es mit ab.
$robo = @(
    (Join-Path $SRC_DIR "webui"), (Join-Path $APP_DIR "app"),
    "/MIR", "/NFL", "/NDL", "/NJH", "/NJS", "/NP", "/R:2", "/W:1",
    "/XD", "__pycache__", "venv",
    "/XF", "*.db", "*.db-wal", "*.db-shm", "*.pyc"
)
& robocopy.exe @robo | Out-Null
# robocopy zaehlt anders als alle anderen: 0 bis 7 heisst "gut", ab 8 ist
# etwas schiefgegangen.
if ($LASTEXITCODE -ge 8) { Abbruch "robocopy ist mit $LASTEXITCODE abgebrochen." }

Copy-Item -LiteralPath (Join-Path $PSScriptRoot "files\start.ps1") `
          -Destination (Join-Path $APP_DIR "start.ps1") -Force

# Welcher Stand hier eingebaut wurde -- der Stempel, den die Fusszeile
# jeder Seite zeigt. NACH dem Kopieren, weil /MIR ihn sonst bei jedem Lauf
# wieder wegraeumt.
#
# "safe.directory": Dieses Skript laeuft mit erhoehten Rechten, der
# Projektordner gehoert einem normalen Benutzer. Ohne die Angabe
# verweigert Git die Auskunft ("detected dubious ownership").
$STAND = "ohne Git"
if (Get-Command git -ErrorAction SilentlyContinue) {
    $beschrieben = & git -C $SRC_DIR -c safe.directory="$SRC_DIR" describe --tags --always --dirty 2>$null
    if ($LASTEXITCODE -eq 0 -and $beschrieben) { $STAND = $beschrieben.Trim() }
}
[System.IO.File]::WriteAllText((Join-Path $APP_DIR "app\VERSION"),
                               $STAND + "`n",
                               (New-Object System.Text.UTF8Encoding($false)))
Write-Host "    Stand: $STAND"

# --------------------------------------------------------------------------
Log "Abhaengigkeiten"
# --------------------------------------------------------------------------
$VENV = Join-Path $APP_DIR "venv"
$VENV_PY = Join-Path $VENV "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $VENV_PY)) {
    if (Test-Path -LiteralPath $VENV) {
        Warnung "Das venv ist unbrauchbar (kein python.exe) -- es wird neu gebaut."
        Remove-Item -LiteralPath $VENV -Recurse -Force
    }
    & $PY -m venv $VENV
    if ($LASTEXITCODE -ne 0) { Abbruch "Das venv liess sich nicht anlegen." }
}
& $VENV_PY -m pip install --quiet --upgrade pip
& $VENV_PY -m pip install --quiet -r (Join-Path $APP_DIR "app\requirements.txt")
if ($LASTEXITCODE -ne 0) { Abbruch "Die Abhaengigkeiten liessen sich nicht installieren." }

# --------------------------------------------------------------------------
Log "Einstellungen schreiben"
# --------------------------------------------------------------------------
#
# Drei Faelle, und der dritte ist der, den man vergisst:
#   1. Die Datei fehlt          -> aus der Vorlage erzeugen, Werte einsetzen.
#   2. Die Datei ist da         -> nur die Adresse anfassen; eigene
#                                  Aenderungen ueberleben jeden Lauf.
#   3. Die Vorlage kennt einen Namen, die Datei nicht
#                               -> nachtragen, mit Wert und Kommentar.
#
# Der dritte Fall entsteht, sobald der Code einen Wert dazubekommt. Ohne
# ihn fehlt er in der Datei, und niemand merkt es, bis etwas nicht geht.
# Uebernommen von der Linux-Seite, wo genau das auf der produktiven
# Maschine aufgefallen ist.
function Schreib-Datei($pfad, $text) {
    # OHNE BOM, und das ist keine Feinheit: start.ps1 liest diese Datei
    # Zeile fuer Zeile und nimmt den Namen vor dem ersten
    # Gleichheitszeichen. Mit BOM hiesse der erste Name nicht
    # MARLEI_BASE_URL, sondern ein unsichtbares Zeichen davor -- und der
    # Port fiele stumm auf 80 zurueck.
    [System.IO.File]::WriteAllText($pfad, $text,
                                   (New-Object System.Text.UTF8Encoding($false)))
}

function Setze-Wert($zeilen, $name, $wert) {
    $getroffen = $false
    $neu = foreach ($z in $zeilen) {
        if ($z -match ("^" + [regex]::Escape($name) + "=")) {
            $getroffen = $true
            "$name=$wert"
        } else { $z }
    }
    if (-not $getroffen) { $neu = @($neu) + @("", "$name=$wert") }
    return @($neu)
}

if (-not (Test-Path -LiteralPath $VORLAGE)) { Abbruch "Die Vorlage fehlt: $VORLAGE" }
$vorlage_zeilen = @(Get-Content -LiteralPath $VORLAGE -Encoding UTF8)

if (Test-Path -LiteralPath $ENV_DATEI) {
    $zeilen = @(Get-Content -LiteralPath $ENV_DATEI -Encoding UTF8)
    $zeilen = Setze-Wert $zeilen "MARLEI_BASE_URL" $ADRESSE

    # Nachtragen, was die Vorlage kennt und die Datei nicht -- mit dem
    # Wert UND den Kommentarzeilen darueber. Ueberschrieben wird nichts.
    $kommentar = @()
    $nachgetragen = 0
    foreach ($z in $vorlage_zeilen) {
        if ($z -match "^#") { $kommentar += $z; continue }
        if ($z.Trim() -eq "") { $kommentar = @(); continue }
        if ($z -match "^([A-Z][A-Z0-9_]*)=") {
            $name = $Matches[1]
            if (-not ($zeilen -match ("^" + [regex]::Escape($name) + "="))) {
                $zeilen = @($zeilen) + @("") + $kommentar + @($z)
                Write-Host "    nachgetragen: $name"
                $nachgetragen++
            }
        }
        $kommentar = @()
    }
    if ($nachgetragen -gt 0) { Write-Host "    $nachgetragen Wert(e) nachgetragen" }
    Schreib-Datei $ENV_DATEI (($zeilen -join "`r`n") + "`r`n")
    Write-Host "    $ENV_DATEI -- nur die Adresse angepasst."
} else {
    $zeilen = Setze-Wert $vorlage_zeilen "MARLEI_BASE_URL" $ADRESSE
    $zeilen = Setze-Wert $zeilen "MARLEI_DB" (Join-Path $DATA_DIR "tasks.db")
    $zeilen = Setze-Wert $zeilen "MARLEI_EXPORT" (Join-Path $DATA_DIR "ausgang")
    Schreib-Datei $ENV_DATEI (($zeilen -join "`r`n") + "`r`n")
    Write-Host "    $ENV_DATEI -- neu angelegt."
}

# Der Ausgang des Exports. Er darf woanders liegen -- etwa in einem
# Git-Repository; dann bekommt der Bestand eine Versionsgeschichte.
# Angelegt wird er hier nur, wenn er unterhalb des Datenverzeichnisses
# liegt: Ein fremder Pfad gehoert jemand anderem.
$AUSGANG = ""
foreach ($z in @(Get-Content -LiteralPath $ENV_DATEI -Encoding UTF8)) {
    if ($z -match "^MARLEI_EXPORT=(.*)$") { $AUSGANG = $Matches[1].Trim() }
}
if ($AUSGANG) {
    if ($AUSGANG.StartsWith($DATA_DIR, [StringComparison]::OrdinalIgnoreCase)) {
        New-Item -ItemType Directory -Force -Path $AUSGANG | Out-Null
    } elseif (-not (Test-Path -LiteralPath $AUSGANG)) {
        Warnung @"
Den Ausgang $AUSGANG gibt es nicht -- er gehoert nicht unter
    $DATA_DIR, deshalb legt dieses Skript ihn nicht an. Die Karte
    "Ablageorte" sagt es ebenfalls.
"@
    } else {
        # **Er ist da, aber darf das Konto dort schreiben?** Solange die
        # Aufgabe als SYSTEM lief, war das keine Frage. Jetzt schon -- und
        # die Rechte vergibt dieses Skript an einem fremden Ort nicht
        # ungefragt; es nennt den Befehl.
        Warnung @"
Der Ausgang liegt ausserhalb des Datenverzeichnisses:
      $AUSGANG
    Das Konto $KONTO darf dort nur schreiben, wenn es jemand erlaubt:
      icacls "$AUSGANG" /grant "${KONTO}:(OI)(CI)M"
    Ob es geht, sagt danach die Karte "Ablageorte" unter Einrichtung.
"@
    }
}

# **Die Einstellungen darf das Konto lesen, nicht aendern.** Das
# Gegenstueck zu "chmod 0640 root:marlei-tasks" auf der Linux-Seite: Darin
# steht der Hash des Kennworts der Oberflaeche, und eine Anwendung, die
# ihre eigene Tuer umschreiben kann, hat keine.
$null = & icacls.exe $ENV_DATEI /inheritance:r /grant:r `
    "*S-1-5-18:F" "*S-1-5-32-544:F" "*${KONTO_SID}:R" 2>&1
if ($LASTEXITCODE -ne 0) {
    Warnung "Die Rechte auf $ENV_DATEI liessen sich nicht setzen (icacls: $LASTEXITCODE)."
}

# --------------------------------------------------------------------------
Log "Kennwort der Oberflaeche"
# --------------------------------------------------------------------------
#
# Dieselben Regeln wie in install.sh: Gefragt wird, wenn keines gesetzt
# ist oder -Kennwort dasteht; verdeckt gelesen, ueber die Standardeingabe
# an anmeldung.py gegeben, in die Datei kommt nur der Hash. Leer lassen
# heisst ohne Kennwort -- erlaubt, aber gesagt.
#
# **UTF-8 AUSDRUECKLICH beim Weiterreichen.** Windows PowerShell 5.1 gibt
# an ein fremdes Programm sonst ASCII weiter, und aus einem Umlaut wuerde
# ein Fragezeichen -- das Kennwort stimmte danach im Formular nie.
$hash_jetzt = ""
foreach ($z in @(Get-Content -LiteralPath $ENV_DATEI -Encoding UTF8)) {
    if ($z -match "^MARLEI_KENNWORT_HASH=(.*)$") { $hash_jetzt = $Matches[1].Trim() }
}

function Lies-Verdeckt($frage) {
    $sicher = Read-Host -Prompt $frage -AsSecureString
    $zeiger = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sicher)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($zeiger) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($zeiger) }
}

if ($hash_jetzt -and -not $Kennwort) {
    Write-Host "    gesetzt. Neu setzen:  .\setup\windows\install.ps1 -Kennwort"
} elseif (-not [Environment]::UserInteractive -or [Console]::IsInputRedirected) {
    # Ohne jemanden, der antworten kann, bleibt es, wie es ist.
    Warnung "Niemand kann antworten -- das Kennwort bleibt, wie es ist."
} else {
    while ($true) {
        $kw1 = Lies-Verdeckt "    Kennwort (mind. 8 Zeichen, leer = ohne)"
        if (-not $kw1) {
            if ($hash_jetzt) {
                Write-Host "    Nichts eingegeben -- das bisherige bleibt."
            } else {
                Warnung "Ohne Kennwort: Wer die Oberflaeche im Netz erreicht, darf alles."
            }
            break
        }
        $kw2 = Lies-Verdeckt "    noch einmal"
        if ($kw1 -cne $kw2) {
            Warnung "Die beiden Eingaben sind verschieden -- noch einmal."
            continue
        }
        $war_kodierung = $OutputEncoding
        $OutputEncoding = New-Object System.Text.UTF8Encoding($false)
        try {
            # Zu kurz meldet anmeldung.py selbst, mit Rueckgabewert 2.
            $hash_neu = $kw1 | & $VENV_PY (Join-Path $APP_DIR "app\anmeldung.py")
        } finally { $OutputEncoding = $war_kodierung }
        if ($LASTEXITCODE -eq 0 -and $hash_neu) {
            $zeilen = @(Get-Content -LiteralPath $ENV_DATEI -Encoding UTF8)
            $zeilen = Setze-Wert $zeilen "MARLEI_KENNWORT_HASH" ([string]$hash_neu).Trim()
            Schreib-Datei $ENV_DATEI (($zeilen -join "`r`n") + "`r`n")
            Write-Host "    gesetzt. Bestehende Anmeldungen enden damit."
            break
        }
    }
    $kw1 = $null; $kw2 = $null
}

# --------------------------------------------------------------------------
Log "Aufgabe einrichten"
# --------------------------------------------------------------------------
#
# Vier Einstellungen, die keine Geschmacksfrage sind:
#
#   AtStartup + Konto    Ohne angemeldeten Benutzer. Das ist der ganze
#                        Grund, eine Aufgabe zu nehmen und nicht einen
#                        Autostart im Profil. Das Kennwort des Kontos
#                        braucht die Aufgabenplanung genau dafuer.
#   ExecutionTimeLimit 0 **Ohne das hier beendet Windows die Aufgabe nach
#                        drei Tagen** -- die Vorgabe der Aufgabenplanung
#                        ist ein Zeitlimit, und ein Dienst hat keins.
#   RestartCount         Was "Restart=on-failure" in der Einheit tut.
#   IgnoreNew            Ein zweiter Lauf neben dem ersten waere ein
#                        zweiter Schreiber auf einer SQLite-Datei.
$aktion = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "{0}"' -f (Join-Path $APP_DIR "start.ps1")) `
    -WorkingDirectory (Join-Path $APP_DIR "app")
$anlass = New-ScheduledTaskTrigger -AtStartup
$wie = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew

if ($vorhanden) { Unregister-ScheduledTask -TaskName $AUFGABE -Confirm:$false }
# -User und -Password statt eines Principals: Ein Principal kennt kein
# Kennwort, und ohne Kennwort liefe die Aufgabe nur, solange das Konto
# angemeldet ist -- also nie. RunLevel Limited: Das Konto braucht keine
# erhoehten Rechte, und es bekommt keine.
Register-ScheduledTask -TaskName $AUFGABE -Action $aktion -Trigger $anlass `
    -User "$env:COMPUTERNAME\$KONTO" -Password $KONTO_KENNWORT `
    -RunLevel Limited -Settings $wie `
    -Description "MARLEI Tasks -- Weboberflaeche, gestartet ueber start.ps1" | Out-Null
$KONTO_KENNWORT = $null
# NACHGESEHEN, NICHT ANGENOMMEN: Ob die Aufgabe wirklich dasteht, sagt die
# Aufgabenplanung -- nicht der Umstand, dass der Befehl keine Meldung
# hinterlassen hat.
if (-not (Get-ScheduledTask -TaskName $AUFGABE -ErrorAction SilentlyContinue)) {
    Abbruch @"
Die Aufgabe "$AUFGABE" liess sich nicht einrichten.
    Nachsehen mit:  Get-ScheduledTask -TaskName "$AUFGABE"
"@
}
Write-Host "    Aufgabe `"$AUFGABE`" eingerichtet (bei Systemstart, als $KONTO)."

# --------------------------------------------------------------------------
Log "Firewall"
# --------------------------------------------------------------------------
#
# **GEFRAGT, DANN GESETZT.** Die Firewall gehoert der Maschine, nicht
# diesem Werkzeug -- dieselbe Grenze wie auf der Linux-Seite, wo gar keine
# Regel angefasst wird. Anders als dort ist sie hier aber von Haus aus an
# und blockt eingehende Verbindungen: Ohne Regel ist die Oberflaeche nur
# vom Rechner selbst erreichbar. Deshalb der Schalter -- verlangt, nicht
# ungefragt.
#
# **Domaene und Privat, nicht Oeffentlich.** Ein Port, den man in einem
# fremden WLAN offen haelt, ist eine andere Entscheidung als einer im
# eigenen Netz; diese Oberflaeche spricht http, und ihr Kennwort ginge
# dort im Klartext durch ein fremdes Netz. Wer sie auch dort braucht, sagt
# es der Firewall selbst.
if ($Firewallregel) {
    # Die alte Regel weg, sonst bleibt bei einem Portwechsel eine stehen,
    # die den falschen Port nennt.
    Get-NetFirewallRule -Name $REGELNAME -ErrorAction SilentlyContinue |
        Remove-NetFirewallRule -ErrorAction SilentlyContinue
    New-NetFirewallRule -Name $REGELNAME -DisplayName "MARLEI Tasks (TCP $Port)" `
        -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port `
        -Profile Domain,Private | Out-Null
    Write-Host "    Regel `"MARLEI Tasks (TCP $Port)`" angelegt -- Domaene und Privat."
} else {
    # Der Befehl steht ERST HIER und nicht oben neben dem Schalter: So
    # kommt in diesem Skript vor der Abfrage keine einzige Stelle vor, die
    # eine Regel anlegen koennte -- auch keine, die nur so aussieht. Die
    # Testreihe prueft genau das, und sie kann es nur am Ort pruefen.
    $regelbefehl = ('New-NetFirewallRule -Name "{0}" ' +
                    '-DisplayName "MARLEI Tasks (TCP {1})" ' +
                    '-Direction Inbound -Action Allow -Protocol TCP ' +
                    '-LocalPort {1} -Profile Domain,Private') -f $REGELNAME, $Port
    Write-Host "    Nicht angefasst. Von aussen erreichbar wird die Oberflaeche erst"
    Write-Host "    mit einer Regel -- entweder beim naechsten Lauf mit"
    Write-Host "      .\setup\windows\install.ps1 -Firewallregel"
    Write-Host "    oder von Hand:"
    Write-Host "      $regelbefehl"
}

# --------------------------------------------------------------------------
Log "Starten"
# --------------------------------------------------------------------------
Start-ScheduledTask -TaskName $AUFGABE
$laeuft = $false
for ($versuch = 0; $versuch -lt 20; $versuch++) {
    Start-Sleep -Milliseconds 500
    try {
        # -ErrorAction Stop AUSDRUECKLICH: Hier IST der Fehler die
        # Auskunft -- eine Antwort, die nicht kommt, soll im catch landen
        # und nicht als Meldung durchlaufen.
        $null = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" `
                    -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        $laeuft = $true
        break
    } catch { }
}
if ($laeuft) {
    Write-Host "    Die Oberflaeche antwortet."
} else {
    $zustand = (Get-ScheduledTask -TaskName $AUFGABE).State
    Warnung @"
Die Oberflaeche antwortet nicht auf http://127.0.0.1:$Port/health
    Zustand der Aufgabe: $zustand
    Was uvicorn dazu sagt, steht in
      $DATA_DIR\log\meldungen.log
"@
}

Write-Host @"

===========================================================================
 Fertig.

   Oberflaeche :  $ADRESSE/
   Ablage      :  $DATA_DIR\tasks.db
   Einstellung :  $ENV_DATEI
   Protokoll   :  $DATA_DIR\log\meldungen.log

 Anhalten, starten, nachsehen (als Administrator):
   Stop-ScheduledTask  -TaskName "$AUFGABE"
   Start-ScheduledTask -TaskName "$AUFGABE"
   Get-ScheduledTask   -TaskName "$AUFGABE" | Select-Object TaskName, State

 Anhalten beendet uvicorn NICHT -- zum Neustarten dieses Skript erneut.

 Der erste Schritt steht auf dem Reiter Projekte: ein Projekt anlegen --
 und dazu mindestens einen Bereich, sonst nimmt die Sammlung nichts an.

===========================================================================
"@
