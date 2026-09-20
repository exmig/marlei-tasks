# ===========================================================================
# Entfernt MARLEI Tasks von diesem Windows.
#
# Aufruf in einer PowerShell ALS ADMINISTRATOR:
#     .\setup\windows\uninstall.ps1
#
# **Der Bestand bleibt.** Weg ist danach das Programm, die Aufgabe, das
# Konto marlei-tasks und die Firewallregel; die Ablage, die Einstellungen und der Ausgang bleiben
# liegen, und das Skript sagt am Ende, wo. Wer auch die weghaben will,
# verlangt es -- und schreibt das Wort dann ein zweites Mal:
#
#     .\setup\windows\uninstall.ps1 -Bestand
#
# ---------------------------------------------------------------------------
# WARUM ES DIESES SKRIPT GIBT -- UND WARUM ES BIS ZUM 19.09.2026 KEINS GAB
#
# Von Hand sind es fuenf Befehle, und sie stehen in der Anleitung. Zwei
# davon uebersieht man aber zuverlaessig, **und es sind die beiden, die
# nicht im Programmverzeichnis liegen:** die Aufgabe in der
# Aufgabenplanung und die Regel in der Firewall. Beide tragen einen Namen,
# den install.ps1 selbst gesetzt hat -- dieses Skript muss also nichts
# raten, und genau deshalb darf es sie anfassen.
#
# **Was es nicht anfasst, ist Absicht.** Python war vorher da und gehoert
# nicht diesem Werkzeug; dieselbe Zurueckhaltung wie beim nginx auf der
# Linux-Seite, wo ein "apt-get remove nginx" der Griff waere, der den
# Bootserver mitnimmt.
# ===========================================================================
[CmdletBinding()]
param(
    # Loescht auch die Ablage, die Einstellungen und den Ausgang. Verlangt
    # zusaetzlich das Losungswort -- siehe unten.
    [switch]$Bestand
)

# ---------------------------------------------------------------------------
# "Continue" und nicht "Stop" -- dieselbe Begruendung wie in install.ps1:
# Ein fremdes Programm, das auf die Fehlerausgabe schreibt, ist kein
# Fehler. Geprueft wird, was zaehlt.
$ErrorActionPreference = "Continue"
Set-StrictMode -Version 2.0

$APP_DIR = Join-Path $env:ProgramFiles "MARLEI Tasks"
$DATA_DIR = Join-Path $env:ProgramData "MARLEI Tasks"

# DIESELBEN NAMEN WIE IN install.ps1, und das ist keine Formsache: Ein
# Name, der hier anders heisst, laesst genau das stehen, was weg soll --
# eine Aufgabe, die beim naechsten Hochfahren ein Programm startet, das es
# nicht mehr gibt, und eine Firewallregel auf einen Port, auf dem niemand
# mehr hoert. Die Testreihe haelt beide Dateien gegeneinander.
$AUFGABE = "MARLEI Tasks"
$REGELNAME = "MARLEI-Tasks"
$KONTO = "marlei-tasks"

# Das Wort, das beim Loeschen des Bestands getippt werden muss.
$LOSUNG = "Bestand"

# Dieselbe Stelle wie in install.ps1 -- warum sie eine eigene Datei ist,
# steht dort im Kopf.
. (Join-Path $PSScriptRoot "files\eigene-prozesse.ps1")
. (Join-Path $PSScriptRoot "files\konto.ps1")

function Log($text) { Write-Host "`n==> $text" -ForegroundColor Cyan }
function Warnung($text) { Write-Host "[!] $text" -ForegroundColor Yellow }
function Abbruch($text) { Write-Host "[X] $text" -ForegroundColor Red; exit 1 }

if ($env:OS -ne "Windows_NT") {
    Abbruch "Dieses Skript ist fuer Windows. Auf einem Linux gilt setup/linux/uninstall.sh."
}
$ich = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $ich.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Abbruch @"
Bitte als Administrator ausfuehren.
    Die Aufgabe und das Konto $KONTO gehoeren der Maschine, das Programm
    liegt unter $env:ProgramFiles, und die Ablage liest nur, wer
    Administrator ist.
"@
}

# --------------------------------------------------------------------------
Log "Was ist hier ueberhaupt da?"
# --------------------------------------------------------------------------
#
# **Erst nachsehen, dann anfassen** -- und es hinschreiben. Ein
# Deinstallationsskript, das schweigend durchlaeuft, laesst einen im
# Zweifel darueber, ob es etwas gefunden hat oder nur nichts gesagt.
function Groesse($pfad) {
    if (-not (Test-Path -LiteralPath $pfad)) { return "" }
    $summe = (Get-ChildItem -LiteralPath $pfad -Recurse -Force -File `
                -ErrorAction SilentlyContinue |
              Measure-Object -Property Length -Sum).Sum
    if (-not $summe) { return "leer" }
    return "{0:N1} MB" -f ($summe / 1MB)
}

$aufgabe_da = [bool](Get-ScheduledTask -TaskName $AUFGABE -ErrorAction SilentlyContinue)
$regel_da = [bool](Get-NetFirewallRule -Name $REGELNAME -ErrorAction SilentlyContinue)
$app_da = Test-Path -LiteralPath $APP_DIR
$konto_da = Konto-Da $KONTO
$daten_da = Test-Path -LiteralPath $DATA_DIR
$ablage = Join-Path $DATA_DIR "tasks.db"

Write-Host ("    Aufgabe        : {0}" -f $(if ($aufgabe_da) { $AUFGABE } else { "nicht da" }))
Write-Host ("    Firewallregel  : {0}" -f $(if ($regel_da) { $REGELNAME } else { "nicht da" }))
Write-Host ("    Konto          : {0}" -f $(if ($konto_da) { $KONTO } else { "nicht da" }))
Write-Host ("    Programm       : {0}" -f $(if ($app_da) { "$APP_DIR  ($(Groesse $APP_DIR))" } else { "nicht da" }))
Write-Host ("    Ablage         : {0}" -f $(if (Test-Path -LiteralPath $ablage) { "$ablage  ($(Groesse $DATA_DIR))" } else { "nicht da" }))

if (-not ($aufgabe_da -or $regel_da -or $app_da -or $daten_da -or $konto_da)) {
    Write-Host ""
    Write-Host "Hier ist nichts von MARLEI Tasks installiert. Nichts zu tun."
    exit 0
}

# --------------------------------------------------------------------------
# Das Losungswort -- nur wenn der Bestand mit weg soll
# --------------------------------------------------------------------------
#
# **Ein Schalter sagt, DASS etwas geloescht wird; das Wort bestaetigt,
# dass man es gelesen hat.** Dieselbe Ueberlegung wie bei der
# Werkseinstellung in der Anwendung, wo der Projektname getippt werden
# muss: Der zerstoerende Knopf trifft dort ein Ziel, das im Band steht,
# und hier eines, das oben auf dieser Ausgabe steht.
#
# Ein Abbruch statt einer Rueckfrage, wenn niemand antworten kann: Ein
# Skript, das in einer Pipeline auf eine Eingabe wartet, haengt -- und ein
# Skript, das ohne Antwort einfach loescht, ist schlimmer.
if ($Bestand -and $daten_da) {
    if (-not [Environment]::UserInteractive) {
        Abbruch @"
-Bestand braucht eine Rueckfrage, und hier kann niemand antworten.
    In einer gewoehnlichen PowerShell erneut aufrufen.
"@
    }
    Write-Host ""
    Write-Host "  Mit -Bestand wird auch das geloescht:" -ForegroundColor Yellow
    Write-Host "      $DATA_DIR"
    Write-Host "    also die Ablage, die Einstellungen, der Ausgang und die Protokolle."
    Write-Host "    Ein Abbild holt man erneut, einen eingetragenen Gedanken nicht:"
    Write-Host "    Wer den Bestand noch braucht, bricht hier ab (Strg+C) und gibt ihn"
    Write-Host "    vorher unter Einrichtung aus."
    Write-Host ""
    $antwort = Read-Host "  Zum Loeschen bitte »$LOSUNG« eingeben"
    if ($antwort.Trim() -ne $LOSUNG) {
        Abbruch "Das Wort stimmt nicht -- es ist nichts geloescht worden."
    }
}

# --------------------------------------------------------------------------
Log "Aufgabe anhalten und entfernen"
# --------------------------------------------------------------------------
if ($aufgabe_da) {
    Stop-ScheduledTask -TaskName $AUFGABE -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $AUFGABE -Confirm:$false `
        -ErrorAction SilentlyContinue
    if (Get-ScheduledTask -TaskName $AUFGABE -ErrorAction SilentlyContinue) {
        Warnung "Die Aufgabe `"$AUFGABE`" ist noch da -- von Hand:
    Unregister-ScheduledTask -TaskName `"$AUFGABE`" -Confirm:`$false"
    } else {
        Write-Host "    weg."
    }
} else {
    Write-Host "    war nicht da."
}

# **Der Prozess ueberlebt die Aufgabe**, und dann haelt er Dateien im
# Programmverzeichnis offen -- Remove-Item scheitert danach mit "wird von
# einem anderen Prozess verwendet". Das Anhalten der Aufgabe genuegt
# dafuer nicht: uvicorn ist ein eigener Prozess, und er bleibt.
#
# Beendet wird nur, was aus UNSEREM Verzeichnis kommt -- erkannt an Pfad
# UND Befehlszeile, denn der Starter ist powershell.exe und liegt
# woanders. Die Einzelheiten stehen in files/eigene-prozesse.ps1; dort
# steht auch, warum ein "weiss nicht" hier nie ein "gehoert uns" wird.
if ($app_da) {
    $beendet = Beende-Eigene $APP_DIR
    if ($beendet -eq 0) { Write-Host "    (es lief nichts mehr)" }
}

# --------------------------------------------------------------------------
Log "Firewallregel entfernen"
# --------------------------------------------------------------------------
#
# **Sie ist unsere, und nur sie.** Gesucht wird nach dem Namen, den
# install.ps1 gesetzt hat -- keine Regel, die jemand anderes angelegt hat,
# und kein Aufraeumen nach Portnummer: Auf demselben Port kann etwas
# stehen, das jemand anderes braucht.
if ($regel_da) {
    Get-NetFirewallRule -Name $REGELNAME -ErrorAction SilentlyContinue |
        Remove-NetFirewallRule -ErrorAction SilentlyContinue
    if (Get-NetFirewallRule -Name $REGELNAME -ErrorAction SilentlyContinue) {
        Warnung "Die Regel `"$REGELNAME`" ist noch da."
    } else {
        Write-Host "    weg."
    }
} else {
    Write-Host "    war keine da (oder sie hiess anders -- dann gehoert sie jemand anderem)."
}

# --------------------------------------------------------------------------
Log "Programm entfernen"
# --------------------------------------------------------------------------
function Weg-Damit($pfad) {
    # Zwei Versuche mit einer Sekunde dazwischen: Windows gibt eine
    # gerade geschlossene Datei nicht immer sofort frei.
    for ($versuch = 1; $versuch -le 3; $versuch++) {
        Remove-Item -LiteralPath $pfad -Recurse -Force -ErrorAction SilentlyContinue
        if (-not (Test-Path -LiteralPath $pfad)) { return $true }
        Start-Sleep -Seconds 1
    }
    return -not (Test-Path -LiteralPath $pfad)
}

if ($app_da) {
    if (Weg-Damit $APP_DIR) {
        Write-Host "    $APP_DIR -- weg (Programm, venv, start.ps1)."
    } else {
        Warnung @"
$APP_DIR liess sich nicht entfernen.
    Meist haelt noch ein Prozess eine Datei offen. Nachsehen, was aus dem
    Verzeichnis laeuft, und danach von Hand:
      Remove-Item "$APP_DIR" -Recurse -Force
"@
    }
} else {
    Write-Host "    war nicht da."
}

# --------------------------------------------------------------------------
Log "Konto $KONTO entfernen"
# --------------------------------------------------------------------------
#
# **Auch wenn der Bestand bleibt -- anders als auf der Linux-Seite.** Dort
# gehoeren die Dateien dem Konto, und ein geloeschtes Konto hinterliesse
# Dateien, deren Besitzer eine Zahl ohne Namen ist. Hier gehoeren sie den
# Administratoren; das Konto hat nur ein Recht darauf, und das wird vorher
# ausgetragen. Eine erneute Installation legt ein neues Konto an und gibt
# ihm das Recht wieder.
#
# Nach dem Programm, weil vorher noch ein Prozess unter dem Konto laufen
# koennte -- und dessen Profil liesse sich dann nicht entfernen.
if ($konto_da) {
    $sid = Konto-Sid $KONTO
    if ($sid -and $daten_da -and -not $Bestand) {
        $null = & icacls.exe $DATA_DIR /remove:g "*$sid" /C /Q 2>&1
    }
    try {
        $null = Konto-Entfernen $KONTO
        if (Konto-Da $KONTO) {
            Warnung "Das Konto $KONTO ist noch da -- von Hand:  net user $KONTO /delete"
        } else {
            Write-Host "    weg, samt Rechten."
        }
    } catch {
        Warnung "Das Konto $KONTO liess sich nicht entfernen: $($_.Exception.Message)"
    }
} else {
    Write-Host "    war nicht da."
}

# --------------------------------------------------------------------------
Log "Der Bestand"
# --------------------------------------------------------------------------
$bestand_weg = $false
if ($Bestand -and $daten_da) {
    if (Weg-Damit $DATA_DIR) {
        $bestand_weg = $true
        Write-Host "    $DATA_DIR -- weg."
    } else {
        Warnung "$DATA_DIR liess sich nicht entfernen."
    }
} elseif ($daten_da) {
    Write-Host "    BLEIBT LIEGEN: $DATA_DIR"
    Write-Host "    Darin die Ablage (tasks.db), die Einstellungen, der Ausgang"
    Write-Host "    und die Protokolle. Eine erneute Installation nimmt alles"
    Write-Host "    wieder auf -- der Bestand und die Einstellungen ueberleben."
} else {
    Write-Host "    war nichts da."
}

Write-Host @"

===========================================================================
 Fertig.

 Weg ist: das Programm, die Aufgabe$(if ($konto_da) { ", das Konto $KONTO" })$(if ($regel_da) { ", die Firewallregel" })$(if ($bestand_weg) { ", der Bestand" }).
$(if (-not $bestand_weg -and $daten_da) { " Liegen bleibt: $DATA_DIR
 Loeschen mit:   .\setup\windows\uninstall.ps1 -Bestand
" })
 **Python bleibt stehen** -- es war vorher da und gehoert nicht diesem
 Werkzeug. Wer es nur dafuer installiert hat, entfernt es ueber die
 Einstellungen von Windows.

===========================================================================
"@
