# ===========================================================================
# Das Konto, unter dem MARLEI Tasks unter Windows laeuft.
#
# Eingebunden von install.ps1 und uninstall.ps1 (dot-sourcing):
#     . "$PSScriptRoot\files\konto.ps1"
#
# **Je Modul ein eigenes Konto, auf beiden Systemen gleich benannt.** Unter
# Linux legt install.sh das Systemkonto marlei-tasks an; hier ist es ein
# lokaler Benutzer desselben Namens. Bis zum 19.09.2026 lief die Aufgabe als
# SYSTEM -- eine Luecke in Tasks oder in uvicorn, FastAPI oder Jinja waere
# eine Luecke im ganzen Rechner gewesen. Unter diesem Konto ist es eine
# Luecke in Tasks.
#
# **Es bleibt eine Aufgabe der Aufgabenplanung, kein Dienst.** Ein Dienst
# in services.msc braeuchte ein Fremdwerkzeug; neu ist nur, unter wem die
# Aufgabe laeuft.
#
# ---------------------------------------------------------------------------
# DAS KONTO HAT EIN KENNWORT, UND NIEMAND KENNT ES
#
# Die Aufgabenplanung braucht es, um die Aufgabe ohne angemeldeten Menschen
# zu starten. Es wird bei JEDEM Lauf von install.ps1 neu erzeugt, zufaellig
# und lang, und landet an genau zwei Stellen: im Konto und in der Aufgabe.
# Neu erzeugt und nicht gemerkt, weil die Aufgabe beim Neuanlegen das
# Kennwort wieder braucht -- ein gemerktes muesste irgendwo liegen.
#
# **Das Konto kann sich nicht am Bildschirm anmelden**, weder vor Ort noch
# per Remotedesktop, und steht nicht auf dem Anmeldebildschirm. Es kann
# genau eines: als Batchauftrag laufen.
#
# **Mit SIDs und nicht mit Namen**, wo Windows Namen uebersetzt: Die Gruppe
# heisst auf einem deutschen Windows "Benutzer", auf einem englischen
# "Users". Dieselbe Falle wie bei icacls in install.ps1.
# ===========================================================================

# Die Gruppe der Benutzer. Ohne sie liest das Konto das Programmverzeichnis
# nicht und auch nicht das Python, auf dem das venv steht -- beide erben
# ihre Leserechte von dieser Gruppe.
$SID_BENUTZER = "S-1-5-32-545"

# Die Rechte, die das Konto bekommt bzw. die ihm verweigert werden.
#   SeBatchLogonRight                  als Batchauftrag anmelden -- ohne das
#                                      startet die Aufgabe nicht
#   SeDenyInteractiveLogonRight        keine Anmeldung am Bildschirm
#   SeDenyRemoteInteractiveLogonRight  keine per Remotedesktop
$KONTO_RECHTE = @("SeBatchLogonRight", "SeDenyInteractiveLogonRight",
                  "SeDenyRemoteInteractiveLogonRight")

# **Die Rechte ueber die LSA und nicht ueber secedit.** secedit exportiert
# die ganze Richtlinie als Textdatei, man aendert eine Zeile und spielt sie
# zurueck -- ein Weg, auf dem man auch alles andere mitnehmen kann, was dort
# steht. LsaAddAccountRights fasst genau das eine Konto an.
if (-not ("MarleiLsa" -as [type])) {
    Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Security.Principal;

public static class MarleiLsa {
    [StructLayout(LayoutKind.Sequential)]
    struct LSA_UNICODE_STRING {
        public ushort Length; public ushort MaximumLength; public IntPtr Buffer;
    }
    [StructLayout(LayoutKind.Sequential)]
    struct LSA_OBJECT_ATTRIBUTES {
        public int Length; public IntPtr RootDirectory; public IntPtr ObjectName;
        public int Attributes; public IntPtr SecurityDescriptor;
        public IntPtr SecurityQualityOfService;
    }
    [DllImport("advapi32.dll")]
    static extern uint LsaOpenPolicy(IntPtr system, ref LSA_OBJECT_ATTRIBUTES attr,
                                     int access, out IntPtr policy);
    [DllImport("advapi32.dll")]
    static extern uint LsaAddAccountRights(IntPtr policy, byte[] sid,
                                           LSA_UNICODE_STRING[] rights, int count);
    [DllImport("advapi32.dll")]
    static extern uint LsaRemoveAccountRights(IntPtr policy, byte[] sid, bool all,
                                              LSA_UNICODE_STRING[] rights, int count);
    [DllImport("advapi32.dll")]
    static extern uint LsaClose(IntPtr policy);
    [DllImport("advapi32.dll")]
    static extern int LsaNtStatusToWinError(uint status);

    const int POLICY_ALL_ACCESS = 0x000F0FFF;
    const uint STATUS_OBJECT_NAME_NOT_FOUND = 0xC0000034;

    static IntPtr Oeffnen() {
        LSA_OBJECT_ATTRIBUTES attr = new LSA_OBJECT_ATTRIBUTES();
        IntPtr policy;
        uint status = LsaOpenPolicy(IntPtr.Zero, ref attr, POLICY_ALL_ACCESS, out policy);
        if (status != 0) { throw new System.ComponentModel.Win32Exception(LsaNtStatusToWinError(status)); }
        return policy;
    }

    static byte[] Sid(string sid) {
        SecurityIdentifier s = new SecurityIdentifier(sid);
        byte[] b = new byte[s.BinaryLength];
        s.GetBinaryForm(b, 0);
        return b;
    }

    public static void Geben(string sid, string[] rechte) {
        IntPtr policy = Oeffnen();
        LSA_UNICODE_STRING[] liste = new LSA_UNICODE_STRING[rechte.Length];
        try {
            for (int i = 0; i < rechte.Length; i++) {
                liste[i].Buffer = Marshal.StringToHGlobalUni(rechte[i]);
                liste[i].Length = (ushort)(rechte[i].Length * 2);
                liste[i].MaximumLength = (ushort)(rechte[i].Length * 2 + 2);
            }
            uint status = LsaAddAccountRights(policy, Sid(sid), liste, liste.Length);
            if (status != 0) { throw new System.ComponentModel.Win32Exception(LsaNtStatusToWinError(status)); }
        } finally {
            foreach (LSA_UNICODE_STRING s in liste) {
                if (s.Buffer != IntPtr.Zero) { Marshal.FreeHGlobal(s.Buffer); }
            }
            LsaClose(policy);
        }
    }

    // Alle Rechte weg -- vor dem Loeschen des Kontos. Sonst bleibt in der
    // Richtlinie eine SID stehen, die niemandem mehr gehoert.
    public static void AlleNehmen(string sid) {
        IntPtr policy = Oeffnen();
        try {
            uint status = LsaRemoveAccountRights(policy, Sid(sid), true, null, 0);
            if (status != 0 && status != STATUS_OBJECT_NAME_NOT_FOUND) {
                throw new System.ComponentModel.Win32Exception(LsaNtStatusToWinError(status));
            }
        } finally { LsaClose(policy); }
    }
}
"@
}

function Konto-Da {
    <# Gibt es den lokalen Benutzer? net.exe, weil es das auf jedem Windows
       gibt und die Antwort nur ein Rueckgabewert ist. #>
    param([string]$Name)
    & net.exe user $Name *> $null
    return ($LASTEXITCODE -eq 0)
}

function Konto-Sid {
    <# Die SID des lokalen Benutzers, oder leer. #>
    param([string]$Name)
    try {
        return (New-Object Security.Principal.NTAccount("$env:COMPUTERNAME\$Name")).Translate(
            [Security.Principal.SecurityIdentifier]).Value
    } catch { return "" }
}

function Neues-Kennwort {
    <#
    Zufaellig, 36 Zeichen, aus dem Zufallsgenerator fuer Schluessel.

    **Die vier Zeichen vorn sind kein Schwachpunkt, sondern die
    Kennwortrichtlinie.** Verlangt sie Gross- und Kleinbuchstaben, Ziffer
    und Sonderzeichen, stehen sie damit sicher drin; die Staerke steckt in
    den 32 zufaelligen dahinter.
    #>
    $zeichen = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
    $bytes = New-Object byte[] 32
    $zufall = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $zufall.GetBytes($bytes) } finally { $zufall.Dispose() }
    return "Aa1-" + (-join ($bytes | ForEach-Object { $zeichen[$_ % $zeichen.Length] }))
}

function Konto-Einrichten {
    <#
    Legt das Konto an oder setzt bei einem vorhandenen das Kennwort neu --
    und in beiden Faellen alles, was dazugehoert. Gibt die SID zurueck.

    **ADSI und nicht New-LocalUser.** Das Modul LocalAccounts gibt es unter
    Windows PowerShell 5.1; unter PowerShell 7 laedt es nur ueber einen
    Umweg. ADSI ist in beiden dasselbe. Und nicht "net user <name>
    <kennwort>": Die Befehlszeile saehe jeder, der die Prozessliste liest.
    #>
    param([string]$Name, [string]$Kennwort, [string]$Beschreibung)

    $rechner = [ADSI]"WinNT://$env:COMPUTERNAME,computer"
    if (Konto-Da $Name) {
        $konto = [ADSI]"WinNT://$env:COMPUTERNAME/$Name,user"
        $null = $konto.Invoke("SetPassword", $Kennwort)
    } else {
        $konto = $rechner.Children.Add($Name, "User")
        $null = $konto.Invoke("SetPassword", $Kennwort)
        $konto.Properties["Description"].Value = $Beschreibung
        $konto.CommitChanges()
        # Erst nach dem Anlegen traegt das Konto die Werte, die Windows
        # selbst setzt -- UserFlags darunter.
        $konto.RefreshCache()
    }
    # 0x10000 Kennwort laeuft nie ab -- sonst startet die Aufgabe nach 42
    #         Tagen nicht mehr, und niemand weiss warum.
    # 0x40    Kennwort kann nicht vom Benutzer geaendert werden.
    # 0x2     (Konto deaktiviert) wird geloescht, falls es jemand gesetzt hat.
    $flags = [int]$konto.Properties["UserFlags"].Value
    $konto.Properties["UserFlags"].Value = (($flags -bor 0x10000 -bor 0x40) -band (-bnot 0x2))
    $konto.CommitChanges()

    # In die Gruppe der Benutzer -- ueber die SID nachgeschlagen.
    #
    # **Mitgliedschaft ueber die SID, nicht ueber IsMember.** Windows nimmt
    # ein neu angelegtes Konto von selbst in diese Gruppe auf; IsMember
    # erkannte es trotzdem nicht, weil es den Pfad in einer anderen
    # Schreibweise erwartet -- und das Add danach brach mit "bereits
    # Mitglied" ab. So geschehen beim ersten Lauf am 19.09.2026. Deshalb
    # zaehlen die SIDs der Mitglieder, und "bereits Mitglied" (1378) ist
    # kein Fehler, sondern das gewuenschte Ergebnis.
    $gruppe = (New-Object Security.Principal.SecurityIdentifier($SID_BENUTZER)).Translate(
        [Security.Principal.NTAccount]).Value.Split("\")[-1]
    $g = [ADSI]"WinNT://$env:COMPUTERNAME/$gruppe,group"
    $sid = Konto-Sid $Name
    $drin = $false
    foreach ($m in @($g.Invoke("Members"))) {
        try {
            $roh = ([ADSI]$m).Properties["objectSid"].Value
            if ($roh -and (New-Object Security.Principal.SecurityIdentifier($roh, 0)).Value -eq $sid) {
                $drin = $true
                break
            }
        } catch { }
    }
    if (-not $drin) {
        try {
            $null = $g.Invoke("Add", "WinNT://$env:COMPUTERNAME/$Name,user")
        } catch {
            $innen = $_.Exception.InnerException
            if (-not ($innen -and ($innen.HResult -band 0xFFFF) -eq 1378)) { throw }
        }
    }

    # Nicht auf dem Anmeldebildschirm. Ein Konto, das dort steht, laedt
    # zum Anklicken ein -- und fragt nach einem Kennwort, das niemand kennt.
    $liste = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\SpecialAccounts\UserList"
    New-Item -Path $liste -Force | Out-Null
    New-ItemProperty -Path $liste -Name $Name -Value 0 -PropertyType DWord -Force | Out-Null

    [MarleiLsa]::Geben($sid, $KONTO_RECHTE)
    return $sid
}

function Konto-Entfernen {
    <#
    Nimmt das Konto samt allem, was es hinterlaesst: die Rechte in der
    Richtlinie, das Profil unter C:\Users, den Eintrag, der es vom
    Anmeldebildschirm fernhaelt. Gibt zurueck, ob es da war.

    **Die Reihenfolge zaehlt.** Rechte und Profil haengen an der SID, und
    die ist nach dem Loeschen des Kontos nicht mehr nachzuschlagen.
    #>
    param([string]$Name)
    if (-not (Konto-Da $Name)) { return $false }
    $sid = Konto-Sid $Name
    if ($sid) {
        try { [MarleiLsa]::AlleNehmen($sid) } catch {
            Write-Host "[!] Die Rechte von $Name liessen sich nicht entfernen: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        # **Warten, bis das Profil frei ist -- und sagen, wenn nicht.**
        # Windows haelt ein Profil noch ein paar Sekunden geladen, nachdem
        # der letzte Prozess des Kontos beendet ist; ein Loeschen in dieser
        # Zeit scheitert. Beim ersten Lauf am 19.09.2026 ist genau das
        # passiert, und der Fehler war verschluckt: Konto weg, Profil samt
        # Eintrag in der ProfileList noch da.
        for ($versuch = 0; $versuch -lt 15; $versuch++) {
            $profil = Get-CimInstance Win32_UserProfile -Filter "SID='$sid'" -ErrorAction SilentlyContinue
            if (-not $profil) { break }
            if (-not $profil.Loaded) {
                try { $profil | Remove-CimInstance -ErrorAction Stop; break } catch { }
            }
            Start-Sleep -Seconds 1
        }
        # **Und manchmal gibt Windows es gar nicht frei, bis der Rechner neu
        # startet.** Beim ersten Lauf blieb das Profil geladen, obwohl kein
        # Prozess mehr unter dem Konto lief -- der Registry-Zweig eines
        # Kontos, unter dem die Aufgabenplanung gearbeitet hat, haengt
        # dann bis zum Neustart. Erzwingen laesst sich das nicht; gesagt
        # wird es, samt dem Befehl fuer danach.
        #
        # Bevor danach wieder installiert wird, gehoert es weg: Ein neues
        # Konto gleichen Namens bekaeme sonst ein Profil unter
        # C:\Users\<name>.<RECHNER>, weil der alte Ordner noch dasteht.
        $rest = Get-CimInstance Win32_UserProfile -Filter "SID='$sid'" -ErrorAction SilentlyContinue
        if ($rest) {
            $warum = if ($rest.Loaded) {
                "Windows haelt es noch geladen und gibt es erst nach einem Neustart frei."
            } else { "Es liess sich nicht loeschen." }
            Write-Host @"
[!] Das Profil von $Name ($($rest.LocalPath)) ist noch da.
    $warum
    Danach, als Administrator -- und VOR einer erneuten Installation:
      Get-CimInstance Win32_UserProfile -Filter "SID='$sid'" | Remove-CimInstance
"@ -ForegroundColor Yellow
        }
    }
    ([ADSI]"WinNT://$env:COMPUTERNAME,computer").Delete("user", $Name)
    $liste = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\SpecialAccounts\UserList"
    Remove-ItemProperty -Path $liste -Name $Name -ErrorAction SilentlyContinue
    return $true
}
