# ===========================================================================
# Startet MARLEI Tasks -- das, was die Aufgabenplanung aufruft.
#
# Aufgerufen wird diese Datei von der Aufgabe "MARLEI Tasks" unter dem
# Konto marlei-tasks, beim Hochfahren der Maschine. Von Hand geht es auch
# (als Administrator -- die Einstellungen liest sonst niemand):
#
#     powershell -ExecutionPolicy Bypass -File "C:\Program Files\MARLEI Tasks\start.ps1"
#
# ---------------------------------------------------------------------------
# WARUM ES DIESE DATEI GIBT UND NICHT NUR EINEN BEFEHL IN DER AUFGABE
#
# Sie ist das Gegenstueck zu "EnvironmentFile=" in der systemd-Einheit.
# Eine Aufgabe der Aufgabenplanung kann keine Umgebungsdatei lesen -- sie
# kennt nur ein Programm und seine Argumente. Also liest dieses Skript die
# Datei und setzt die Werte, bevor es uvicorn startet.
#
# **Der Gewinn davon ist nicht die Bequemlichkeit, sondern der EINE Ort:**
# Wer eine Einstellung aendert, aendert sie in der Umgebungsdatei -- nicht
# in einer Aufgabe, die man in einer Oberflaeche suchen muss. Und die Karte
# "Einstellungen" zeigt genau diese Datei.
#
# DER PORT STEHT DESHALB AUCH NICHT HIER, sondern in MARLEI_BASE_URL. Er
# ist die einzige Zahl, die zugleich im Kopfband steht, in der Karte
# "Einstellungen", in der Portliste unter Firewall und in dem, worauf
# uvicorn hoert -- **eine Zahl, eine Quelle.** Unter Linux uebernimmt das
# der nginx-vhost; hier gibt es keinen.
# ===========================================================================
$ErrorActionPreference = "Stop"

$APP_DIR = $PSScriptRoot
$DATA_DIR = Join-Path $env:ProgramData "MARLEI Tasks"
$ENV_DATEI = Join-Path $DATA_DIR "marlei-tasks.env"
$LOG_DIR = Join-Path $DATA_DIR "log"

# Das Protokoll des vorigen Laufs wird beiseitegelegt, nicht ueberschrieben
# -- siehe unten: Start-Process schreibt die Datei neu, und der Lauf, den
# man lesen will, ist meistens der, der gerade abgebrochen ist.

# --------------------------------------------------------------------------
# Die Umgebungsdatei lesen
# --------------------------------------------------------------------------
#
# Format wie unter Linux: NAME=wert, eine Zeile je Wert, # ist ein
# Kommentar. **Nicht in Anfuehrungszeichen setzen** -- der Rest der Zeile
# gilt wortwoertlich, Leerzeichen in Pfaden eingeschlossen. Genau deshalb
# wird hier nur am ERSTEN Gleichheitszeichen getrennt.
function Lies-Umgebung {
    param([string]$Datei)
    $werte = @{}
    if (-not (Test-Path -LiteralPath $Datei)) { return $werte }
    foreach ($zeile in Get-Content -LiteralPath $Datei -Encoding UTF8) {
        $roh = $zeile.Trim()
        if ($roh -eq "" -or $roh.StartsWith("#")) { continue }
        $teiler = $roh.IndexOf("=")
        if ($teiler -lt 1) { continue }
        $name = $roh.Substring(0, $teiler).Trim()
        $wert = $roh.Substring($teiler + 1).Trim()
        if ($name -match '^[A-Z][A-Z0-9_]*$') { $werte[$name] = $wert }
    }
    return $werte
}

$umgebung = Lies-Umgebung $ENV_DATEI
foreach ($name in $umgebung.Keys) {
    Set-Item -Path ("Env:" + $name) -Value $umgebung[$name]
}

# --------------------------------------------------------------------------
# Auf welchem Port?
# --------------------------------------------------------------------------
#
# Aus MARLEI_BASE_URL, also aus der Adresse, die im Kopfband steht. Steht
# dort keine Zahl, ist es die 80 -- **das ist keine Vorgabe, sondern die
# Bedeutung einer Adresse ohne Doppelpunkt.** Dieselbe Regel, nach der die
# Karte "Einstellungen" den Port nennt; sie steht dort in
# app._oberflaechenport().
$port = 80
$adresse = $env:MARLEI_BASE_URL
if ($adresse -match '^[a-z]+://[^/]*:(\d+)') { $port = [int]$Matches[1] }

# --------------------------------------------------------------------------
# Protokoll
# --------------------------------------------------------------------------
#
# **Unter Linux uebernimmt das journalctl; hier gibt es nichts
# Vergleichbares.** Eine Aufgabe der Aufgabenplanung wirft die Ausgabe
# ihres Programms weg -- und damit genau das, was man beim ersten
# "es geht nicht" braucht. Deshalb zwei Dateien: uvicorn schreibt seine
# Meldungen auf die Fehlerausgabe, nicht auf die normale.
#
# **Je eine Fassung zurueck, und zwar bei JEDEM Start.** Nicht erst ab
# einer Groesse: Start-Process schreibt seine Zieldatei neu, und der Lauf,
# den man lesen will, ist der, der gerade abgebrochen ist -- nicht der, der
# eben angefangen hat. Damit waechst hier auch nichts unbemerkt.
New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null
$log_aus = Join-Path $LOG_DIR "ausgabe.log"
$log_meldungen = Join-Path $LOG_DIR "meldungen.log"
foreach ($datei in @($log_aus, $log_meldungen)) {
    if ((Test-Path -LiteralPath $datei) -and
        ((Get-Item -LiteralPath $datei).Length -gt 0)) {
        Move-Item -LiteralPath $datei -Destination ($datei + ".1") -Force
    }
}

# --------------------------------------------------------------------------
# Und los
# --------------------------------------------------------------------------
#
# **--host 0.0.0.0, und das ist der eine echte Unterschied zur
# systemd-Einheit.** Dort steht 127.0.0.1, weil ein nginx davorsteht und
# den Weg von aussen macht. Hier gibt es keinen: Wer nur auf sich selbst
# hoert, ist von keinem anderen Rechner erreichbar, und dann waere das
# ganze Werkzeug auf dieser Maschine ein Selbstgespraech.
#
# Was daran haengt, steht in der README und gilt hier woertlich: Diese
# Oberflaeche hat ein Kennwort und sonst nichts, und sie spricht http.
# Sie gehoert in ein Netz, dem man vertraut.
#
# -Wait, damit dieses Skript so lange laeuft wie uvicorn: Die Aufgabe gilt
# als beendet, sobald ihr Programm zurueckkommt -- ein Start, der sofort
# zurueckkehrt, sieht fuer die Aufgabenplanung wie ein erledigter Lauf aus
# und wird nie neu gestartet.
$python = Join-Path $APP_DIR "venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Kein Python im venv: $python -- install.ps1 erneut ausfuehren."
}

Start-Process -FilePath $python `
    -ArgumentList @("-m", "uvicorn", "app:app", "--host", "0.0.0.0",
                    "--port", "$port") `
    -WorkingDirectory (Join-Path $APP_DIR "app") `
    -RedirectStandardOutput $log_aus `
    -RedirectStandardError $log_meldungen `
    -NoNewWindow -Wait
