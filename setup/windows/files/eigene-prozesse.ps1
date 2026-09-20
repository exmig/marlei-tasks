# ===========================================================================
# Wer laeuft hier aus UNSEREM Verzeichnis, und wer hoert auf einem Port?
#
# Eingebunden von install.ps1 und uninstall.ps1 (dot-sourcing):
#     . "$PSScriptRoot\files\eigene-prozesse.ps1"
#
# **Warum eine eigene Datei fuer zwoelf Zeilen.** Beide Skripte muessen
# dasselbe wissen -- was von dieser Installation noch laeuft -- und beide
# muessen es GENAU wissen: Das eine beendet danach etwas, das andere
# loescht danach ein Verzeichnis. Als Doppelung waere es die Sorte Code,
# die auseinanderlaeuft, sobald einer davon einen Fall dazulernt. Genau das
# ist am 19.09.2026 passiert, und der Fall steht unten.
#
# ---------------------------------------------------------------------------
# DER FALL, DER DIESE DATEI ERZWUNGEN HAT
#
# Beim zweiten Lauf von install.ps1 auf der ersten echten Maschine:
#
#     ==> Laeuft schon etwas, und ist der Port frei?
#         Aufgabe ist da -- wird angehalten.
#     [X] Auf Port 8081 hoert bereits etwas anderes:
#         7944 unbekannt
#
# **Es war nichts anderes, es war unser eigener Prozess.** Zwei Fehler auf
# einmal:
#
# 1. **Die Aufgabe anzuhalten beendet nicht, was sie gestartet hat.**
#    start.ps1 startet uvicorn als eigenen Prozess; der haelt den Port
#    weiter, nachdem die Aufgabe als beendet gilt.
#
# 2. **"Nicht zuordenbar" wurde als "fremd" gelesen.** Der Pfad kam ueber
#    ``Get-Process().Path`` -- und der ist leer, sobald der Prozess gerade
#    endet oder sich nicht oeffnen laesst. Aus einem *weiss nicht* wurde
#    damit ein *gehoert jemand anderem*, und das Skript brach an seiner
#    eigenen Installation ab.
#
# Gefragt wird deshalb hier ueber CIM: ``ExecutablePath`` UND
# ``CommandLine``. Die Befehlszeile zaehlt mit, weil der Starter
# ``powershell.exe`` ist und ausserhalb unseres Verzeichnisses liegt --
# unser Verzeichnis steht dort nur im Argument. Wer nur den Pfad der
# ausfuehrbaren Datei ansieht, erkennt den eigenen Starter nicht.
#
# **Und "weiss nicht" bleibt "weiss nicht".** Keine der Funktionen hier
# entscheidet, was mit einem Prozess zu tun ist, den sie nicht zuordnen
# kann; sie sagt es, und der Aufrufer entscheidet. Ein Skript, das im
# Zweifel fremde Prozesse beendet, waere schlimmer als eines, das im
# Zweifel abbricht.
# ===========================================================================

function Prozessbild {
    <#
    Was ueber einen Prozess zu erfahren ist -- oder dass nichts zu erfahren
    ist. ``Zuordenbar`` sagt genau das: ob Pfad oder Befehlszeile bekannt
    sind. Ein Prozess, den es nicht mehr gibt, kommt mit $null zurueck.
    #>
    param([int]$Id)

    $bild = @{ Id = $Id; Name = ""; Pfad = ""; Zeile = ""; Zuordenbar = $false }

    # CIM zuerst: Es beantwortet die Frage auch fuer einen Prozess, der
    # unter SYSTEM laeuft, und liefert die Befehlszeile mit.
    $cim = Get-CimInstance Win32_Process -Filter "ProcessId=$Id" `
               -ErrorAction SilentlyContinue
    if ($cim) {
        $bild.Name = [string]$cim.Name
        $bild.Pfad = [string]$cim.ExecutablePath
        $bild.Zeile = [string]$cim.CommandLine
    } else {
        # Rueckfall, falls WMI nicht antwortet. Weniger Auskunft, aber
        # besser als keine.
        $p = Get-Process -Id $Id -ErrorAction SilentlyContinue
        if (-not $p) { return $null }
        $bild.Name = $p.ProcessName
        try { $bild.Pfad = [string]$p.Path } catch { }
    }
    $bild.Zuordenbar = [bool]($bild.Pfad -or $bild.Zeile)
    return $bild
}

function Gehoert-Uns {
    <#
    Laeuft dieser Prozess aus dem angegebenen Verzeichnis?

    Geprueft werden beide Stellen, an denen das Verzeichnis auftauchen
    kann: die ausfuehrbare Datei (uvicorn aus dem venv) und die
    Befehlszeile (powershell mit unserem start.ps1). **Bei Unsicherheit
    falsch** -- wer nichts weiss, besitzt nichts.
    #>
    param($Bild, [string]$Verzeichnis)

    if (-not $Bild) { return $false }
    foreach ($text in @($Bild.Pfad, $Bild.Zeile)) {
        if ($text -and $text.IndexOf($Verzeichnis,
                [StringComparison]::OrdinalIgnoreCase) -ge 0) {
            return $true
        }
    }
    return $false
}

function Beende-Eigene {
    <#
    Beendet alles, was aus diesem Verzeichnis laeuft -- und nichts sonst.

    **Das ist der Griff, der beim zweiten Lauf fehlte.** Die Aufgabe
    anzuhalten laesst uvicorn stehen; ohne diesen Schritt haelt er den Port
    weiter und das Programmverzeichnis offen. Gibt die Anzahl der
    beendeten Prozesse zurueck.
    #>
    param([string]$Verzeichnis, [switch]$Still)

    $beendet = 0
    foreach ($cim in @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)) {
        $bild = @{
            Id = [int]$cim.ProcessId
            Name = [string]$cim.Name
            Pfad = [string]$cim.ExecutablePath
            Zeile = [string]$cim.CommandLine
        }
        # Sich selbst nicht: Dieses Skript liegt im Projektordner, nicht im
        # Programmverzeichnis -- aber ein Aufruf mit -Verzeichnis auf den
        # Projektordner waere sonst ein Schuss ins eigene Knie.
        if ($bild.Id -eq $PID) { continue }
        if (-not (Gehoert-Uns $bild $Verzeichnis)) { continue }
        if (-not $Still) {
            Write-Host ("    beendet: {0} (PID {1})" -f $bild.Name, $bild.Id)
        }
        Stop-Process -Id $bild.Id -Force -ErrorAction SilentlyContinue
        $beendet++
    }
    return $beendet
}

function Port-Horcher {
    <#
    Wer hoert auf diesem Port? Eine Liste von Prozessbildern.

    Leer heisst: niemand. Ein Eintrag mit ``Zuordenbar = $false`` heisst:
    Da hoert etwas, und was es ist, war von hier aus nicht zu erfahren.
    #>
    param([int]$Port)

    $bilder = @()
    $gesehen = @{}
    foreach ($v in @(Get-NetTCPConnection -LocalPort $Port -State Listen `
                        -ErrorAction SilentlyContinue)) {
        $id = [int]$v.OwningProcess
        if ($gesehen.ContainsKey($id)) { continue }
        $gesehen[$id] = $true
        $bild = Prozessbild $id
        if (-not $bild) {
            # Der Prozess ist zwischen den beiden Fragen verschwunden.
            # Auch das ist eine Auskunft und kein Fehler.
            $bild = @{ Id = $id; Name = ""; Pfad = ""; Zeile = "";
                       Zuordenbar = $false }
        }
        $bilder += $bild
    }
    # **MIT KOMMA, und das ist keine Feinheit.** PowerShell packt ein Feld
    # beim Zurueckgeben aus: Aus einem Element wird das Element selbst, aus
    # keinem wird nichts. Ein Aufrufer, der dann ".Count" liest, bekommt
    # unter Set-StrictMode einen Fehler -- und zwar an einer Stelle, die
    # aussieht, als haette sie mit Prozessen zu tun. Das Komma macht aus dem
    # Rueckgabewert EIN Element, naemlich das Feld.
    #
    # Beim Bauen an der eigenen Pruefung aufgefallen: Die Liste war leer,
    # der Test fragte nach .Count und stuerzte ab -- ueber die Frage, nicht
    # ueber die Antwort.
    return ,$bilder
}
