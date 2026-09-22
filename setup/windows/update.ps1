# ===========================================================================
# Holt den neuesten Stand und uebernimmt ihn -- die Windows-Seite.
#
#     .\setup\windows\update.ps1
#
# Bewusst OHNE Administratorrechte aufrufen: "git pull" soll mit deinem
# Benutzer und deinem SSH-Schluessel laufen. Fuer install.ps1 fragt dieses
# Skript selbst nach -- es startet ihn in einem eigenen Fenster mit
# erhoehten Rechten, und Windows fragt dabei um Erlaubnis.
#
# ---------------------------------------------------------------------------
# DER PORT WIRD GEMERKT, NICHT ERFRAGT -- UND NICHT HIER
#
# Laeuft diese Installation auf einem anderen Port als 8081, waere ein
# Update, das die Vorgabe nimmt, eine stille Umstellung -- die Adresse im
# Kopfband stimmte danach nicht mehr, und jedes Lesezeichen zeigte ins
# Leere.
#
# **Gemerkt wird er in install.ps1, nicht hier.** Bis September 2026 las
# dieses Skript MARLEI_BASE_URL selbst aus der Umgebungsdatei. Seit dem
# eigenen Konto darf die aber nur ein Administrator lesen -- darin steht
# der Hash des Kennworts --, und dieses Skript laeuft bewusst ohne. Es
# fand keinen Port und nahm 8081. install.ps1 laeuft mit erhoehten
# Rechten und nimmt ohne -Port den der bestehenden Installation; hier
# wird -Port nur weitergereicht, wenn jemand ihn angibt.
#
# ---------------------------------------------------------------------------
# INSTALLIERT WIRD, WENN DIE INSTALLATION ZURUECKLIEGT -- NICHT, WENN DER
# PULL ETWAS GEBRACHT HAT
#
# Bis zum 19.09.2026 hing es am Pull: vorher und nachher derselbe Commit,
# also "Schon aktuell". Das stimmte nur, solange Repository und Installation
# immer gemeinsam weiterruecken. Drei Faelle, in denen sie es nicht tun:
# ein "git pull" von Hand vor dem Update, ein Update, dessen Installation
# abbrach (etwa weil jemand die Rueckfrage von Windows abgelehnt hat), und
# der Rechner, auf dem entwickelt wird. Jedes Mal lief der alte Stand
# weiter, und das Skript sagte, alles sei aktuell -- so geschehen am
# 19.09.2026 auf dem Entwicklungsrechner.
#
# Verglichen wird deshalb der Stempel der Installation ($VERSION_DATEI)
# mit dem, den install.ps1 jetzt schreiben wuerde -- **mit demselben
# Befehl, damit beide Seiten dieselbe Sprache sprechen.** Ein Stand mit
# "-dirty" wird immer uebernommen: Was darin geaendert ist, sagt der
# Stempel nicht.
# ===========================================================================
[CmdletBinding()]
param(
    # Wird an install.ps1 weitergegeben, wenn angegeben -- eine Angabe von
    # aussen gewinnt. Ohne sie bleibt der Port der Installation.
    [int]$Port = 0,

    # Wird an install.ps1 weitergegeben.
    [switch]$Firewallregel
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

$PROJEKT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$DATA_DIR = Join-Path $env:ProgramData "MARLEI Tasks"
$INSTALL = Join-Path $PSScriptRoot "install.ps1"
# Der Stempel, den install.ps1 schreibt -- dort APP_DIR\app\VERSION.
$VERSION_DATEI = Join-Path $env:ProgramFiles "MARLEI Tasks\app\VERSION"

function Log($text) { Write-Host "`n==> $text" -ForegroundColor Cyan }
function Warnung($text) { Write-Host "[!] $text" -ForegroundColor Yellow }
function Abbruch($text) { Write-Host "[X] $text" -ForegroundColor Red; exit 1 }

$ich = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if ($ich.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Abbruch @"
Bitte OHNE Administratorrechte aufrufen -- git soll deinem Benutzer gehoeren.
    Ein "git pull" als Administrator legt Dateien an, die dir danach nicht
    mehr gehoeren, und benutzt nicht deinen SSH-Schluessel. Fuer die
    Installation fragt dieses Skript selbst nach.
"@
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Abbruch "git fehlt -- ohne git gibt es keinen neuen Stand zu holen."
}
Push-Location $PROJEKT
try {
    & git rev-parse --git-dir *> $null
    if ($LASTEXITCODE -ne 0) {
        Abbruch "$PROJEKT ist kein Git-Repository. Erst klonen -- siehe docs/installation.md."
    }
    $VORHER = (& git rev-parse HEAD).Trim()

    Log "Neuen Stand holen"
    # --ff-only: lieber sauber abbrechen als einen Merge-Commit erzeugen.
    # Diese Maschine soll nur nachziehen.
    & git pull --ff-only
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Der Stand laesst sich nicht ohne Weiteres uebernehmen."
        Write-Host "Meist wurde hier etwas veraendert. Was, zeigt:"
        Write-Host "    git -C `"$PROJEKT`" status"
        Write-Host ""
        Write-Host "Wegwerfen und stur den Stand aus dem Repository nehmen:"
        Write-Host "    git -C `"$PROJEKT`" fetch origin"
        Write-Host "    git -C `"$PROJEKT`" reset --hard origin/main"
        exit 1
    }
    $NACHHER = (& git rev-parse HEAD).Trim()

    # Was laeuft, und was wuerde jetzt installiert? Dieselbe Formel wie in
    # install.ps1, sonst sprechen die beiden Stempel nie dieselbe Sprache.
    #
    # GELESEN WIRD DAS FELD "stand", nicht die ganze Datei. Seit dem
    # 22.09.2026 stehen dort vier Felder (stand, commit, zweig,
    # installiert), weil die Karte "Stand" in der Oberflaeche den Commit
    # braucht. Hier stand bis dahin ein ReadAllText().Trim() ueber die
    # ganze Datei -- mit der neuen Datei ergaebe das Kommentar und alle
    # vier Felder am Stueck, und das ist mit keinem "git describe" je
    # gleich. Die Folgen waeren still: "Schon aktuell" griffe nie mehr,
    # und gezaehlt wuerde vom Stand vor dem Pull statt vom installierten.
    #
    # Die alte einzeilige Datei wird weiter gelesen -- dieselbe Ruecksicht
    # wie in webui\versionsstand.py: Eine Installation von vor diesem Tag
    # traegt sie noch, und genau die will ja aktualisiert werden.
    $INSTALLIERT = ""
    if (Test-Path -LiteralPath $VERSION_DATEI) {
        $zeilen = [System.IO.File]::ReadAllLines($VERSION_DATEI)
        $feld = $zeilen | Where-Object { $_ -match '^stand=' } | Select-Object -First 1
        if ($feld) {
            $INSTALLIERT = ($feld -replace '^stand=', '').Trim()
        } else {
            $INSTALLIERT = (($zeilen | Where-Object {
                $_.Trim() -and -not $_.TrimStart().StartsWith("#")
            }) -join "").Trim()
        }
    }
    $JETZT = & git describe --tags --always --dirty 2>$null
    $JETZT = if ($LASTEXITCODE -eq 0 -and $JETZT) { "$JETZT".Trim() } else { "unbekannt" }

    if ($INSTALLIERT -eq $JETZT -and -not $JETZT.EndsWith("-dirty")) {
        Log "Schon aktuell ($(& git log -1 --format='%h %s'))"
        Write-Host "    Installiert ist genau dieser Stand."
        Write-Host "    install.ps1 trotzdem ausfuehren? Dann direkt (als Administrator):"
        Write-Host "      $INSTALL"
        exit 0
    }

    # Von wo aus gezaehlt wird, was dazukommt: vom installierten Stand,
    # wenn Git ihn kennt -- sonst vom Stand vor dem Pull. Der Stempel ist
    # eine Ausgabe von "git describe" und laesst sich deshalb
    # zurueckuebersetzen; nur das "-dirty" kennt Git nicht.
    $BASIS = $VORHER
    if ($INSTALLIERT) {
        $ohne = $INSTALLIERT -replace '-dirty$', ''
        $gefunden = & git rev-parse -q --verify "$ohne^{commit}" 2>$null
        if ($LASTEXITCODE -eq 0 -and $gefunden) { $BASIS = "$gefunden".Trim() }
    }

    if ($VORHER -eq $NACHHER) {
        Log "Nichts Neues geholt -- aber die Installation liegt zurueck"
        Write-Host ("    installiert: {0}" -f $(if ($INSTALLIERT) { $INSTALLIERT } else { "unbekannt" }))
        Write-Host "    im Projekt:  $JETZT"
    }

    if ($BASIS -ne $NACHHER) {
        Log "Diese Aenderungen sind dazugekommen"
        & git --no-pager log --oneline "$BASIS..$NACHHER"
        Write-Host ""
        & git --no-pager diff --stat "$BASIS..$NACHHER"
    }

    # Aendert sich die Ablage, ist eine Kopie vorher billig -- und
    # hinterher unmoeglich. Beim Start zieht die Anwendung fehlende Spalten
    # nach und entfernt entfallene; das ist gewollt und laesst sich nicht
    # rueckgaengig machen. GESAGT, NICHT GETAN: Wohin eine Sicherung
    # gehoert, weiss der Betreiber, nicht dieses Skript.
    $geaendert = & git diff --name-only "$BASIS..$NACHHER"
    if ($geaendert -contains "webui/datenbank.py") {
        $heute = Get-Date -Format "yyyyMMdd"
        Write-Host @"

---------------------------------------------------------------------------
 An der Ablage hat sich etwas geaendert. Beim naechsten Start zieht die
 Anwendung Spalten nach oder entfernt entfallene -- eine Kopie vorher
 kostet eine Sekunde (als Administrator, die Ablage ist geschuetzt):

   Copy-Item "$DATA_DIR\tasks.db" "`$HOME\tasks-$heute.db"

---------------------------------------------------------------------------
"@
    }
} finally {
    Pop-Location
}

# --------------------------------------------------------------------------
Log "Uebernehmen"
# --------------------------------------------------------------------------
#
# **Ein eigenes Fenster, und daran ist nichts zu machen:** Windows erhoeht
# Rechte nur fuer einen NEUEN Prozess -- ein "sudo" mitten in einer
# laufenden Sitzung gibt es nicht. Deshalb -Wait: Dieses Skript bleibt
# stehen, bis die Installation durch ist, damit man hier nicht weiterliest,
# waehrend daneben noch etwas laeuft.
$argumente = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $INSTALL)
# Ohne Angabe entscheidet install.ps1 -- es liest den Port der bestehenden
# Installation, was dieses Skript nicht darf (siehe Kopf).
if ($Port -gt 0) { $argumente += @("-Port", "$Port") }
if ($Firewallregel) { $argumente += "-Firewallregel" }

Write-Host "    Das Installationsfenster oeffnet sich -- Windows fragt nach der Erlaubnis."
$lauf = Start-Process -FilePath "powershell.exe" -ArgumentList $argumente `
            -Verb RunAs -Wait -PassThru
if ($lauf.ExitCode -ne 0) {
    Abbruch @"
Die Installation ist mit $($lauf.ExitCode) abgebrochen.
    Was sie gesagt hat, stand in dem Fenster. Erneut von Hand, dann bleibt
    es stehen:
      $INSTALL$(if ($Port -gt 0) { " -Port $Port" })
"@
}
Write-Host ""
Write-Host "Uebernommen. Welcher Stand laeuft, sagt die Fusszeile jeder Seite."
