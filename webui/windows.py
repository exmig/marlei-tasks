r"""
Was eine Windows-Maschine von sich erzaehlt -- alle Quellen an einer Stelle.

Drei Module fragen hier nach: ``auslastung.py``, ``bericht.py`` und
``firewall.py``. Unter Linux lesen sie ``/proc``, ``/etc/os-release`` und
``/etc/ufw/ufw.conf`` -- **Dateien, die es unter Windows nicht gibt, auch
nicht aehnlich.** Dieselben Auskuenfte stehen dort in der Registry oder
hinter einem Aufruf des Kernels.

**Warum ein eigenes Modul und keine Weiche in den dreien.** Zwei von ihnen
sind aus MARLEI Boot abgeschrieben und stehen unter Aufsicht
(``tools/gemeinsam.txt``): Jede Zeile, die dort dazukommt, laeuft zwischen
den Produkten auseinander. Hier drin steht nichts, was Boot je brauchen
wird -- ein Bootserver bootet keine Rechner von einem Windows aus. So
bleibt in den drei Modulen je eine Weiche stehen und die ganze
Windows-Kenntnis an einem Ort, an dem man sie sucht.

**Keine Fremdpakete, und das ist keine Sparsamkeit.** ``psutil`` und
``pywin32`` koennten alles, was hier steht, und wuerden
``requirements.txt`` von fuenf auf sieben Zeilen bringen -- zwei Pakete
mit eigenen Rad-Dateien je Python-Version, die bei jedem Update mitwollen.
``ctypes`` und ``winreg`` stehen in der Standardbibliothek; ``kernel32``,
``psapi`` und ``iphlpapi`` sind da, sobald Windows laeuft.

**Fehlt eine Quelle, kommt nichts zurueck.** Dieselbe Regel wie unter
Linux, und hier ist sie wichtiger: Jeder Aufruf hier geht an eine fremde
Schnittstelle, deren Rueckgabewert niemand garantiert. Meldet sie einen
Fehler, ist die Antwort ``None`` oder ``{}`` -- **nie eine geschaetzte
Zahl.** Eine Kachel, die fehlt, ist ehrlich; eine Kachel, die etwas
erfindet, ist es nicht.

**Ein Schluss aus der Zahl auf ihre Bedeutung wird nicht gezogen.** Was
hier herauskommt, sind Messwerte. Ob eine Firewall „im Weg steht", ob ein
Speicherstand knapp ist, entscheidet das Modul, das fragt -- so wie unter
Linux auch.
"""

from __future__ import annotations

import ctypes
import os
import platform
import time

# --------------------------------------------------------------------------
# Die Typen, und warum sie nicht aus ctypes.wintypes kommen
# --------------------------------------------------------------------------
#
# **``import ctypes.wintypes`` scheitert auf einem Linux** -- mit einem
# ValueError, nicht mit einem ImportError, und schon beim Import. Dieses
# Modul wird aber von drei Modulen unbedingt eingebunden, die auf beiden
# Systemen laufen; ein Import, der auf dem Server abbricht, waere der
# teuerste Fehler dieses ganzen Umbaus.
#
# Die vier Typen, um die es geht, sind ohnehin nur Namen fuer
# C-Grundtypen -- genau diese Zuordnung steht in ctypes.wintypes selbst,
# und die Testreihe haelt Groesse und Identitaet gegeneinander.
DWORD = ctypes.c_ulong
WORD = ctypes.c_ushort
BOOL = ctypes.c_long
HANDLE = ctypes.c_void_p

# --------------------------------------------------------------------------
# Die drei Bibliotheken, und was ein Fehlschlag hier bedeutet
# --------------------------------------------------------------------------
#
# Geladen wird beim Import, aber ohne Aufhebens: Auf einem System ohne
# Windows gibt es ``ctypes.WinDLL`` gar nicht, und dieses Modul soll
# importierbar bleiben -- die drei Module, die es benutzen, laufen auf
# beiden Systemen und duerfen keinen Importfehler erben. Ist hier etwas
# None, antwortet jede Funktion weiter unten mit einem leeren Wert.
IST_WINDOWS = os.name == "nt"


def _lade(name: str):
    if not IST_WINDOWS:
        return None
    try:
        return ctypes.WinDLL(name, use_last_error=True)
    except OSError:
        return None


_K32 = _lade("kernel32")
_PSAPI = _lade("psapi")
_IPHLP = _lade("iphlpapi")

# 100-Nanosekunden-Schritte je Sekunde. Windows zaehlt Zeiten in dieser
# Einheit -- sie heisst FILETIME und ist nirgends rund.
_HNS = 10_000_000

# Fuer Werte, die sich nur aus der Differenz zweier Messungen ergeben --
# dieselbe Mechanik wie in auslastung.py, und derselbe Grund: Der Kernel
# zaehlt Summen, keine Prozente.
_vorher: dict = {}


class _FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", DWORD),
                ("dwHighDateTime", DWORD)]


def _zahl(ft: _FILETIME) -> int:
    """Die beiden Haelften einer FILETIME zu einer Zahl."""
    return (ft.dwHighDateTime << 32) | ft.dwLowDateTime


# --------------------------------------------------------------------------
# Prozessor
# --------------------------------------------------------------------------

def cpu() -> int | None:
    """Auslastung in Prozent seit der letzten Abfrage.

    ``GetSystemTimes`` liefert dieselbe Art Auskunft wie ``/proc/stat``:
    aufgelaufene Zeitscheiben, keine Prozente. Der Wert ergibt sich aus
    der Differenz zweier Messungen, und **die erste Abfrage nach dem Start
    hat keinen Vergleichswert** -- sie liefert deshalb nichts. Genauso
    haelt es die Linux-Seite.

    **``kernel`` enthaelt ``idle`` bereits** -- das ist die Falle dieser
    Schnittstelle. Die Summe aus Kernel- und Benutzerzeit ist die ganze
    Zeit; die Untaetigkeit wird davon abgezogen und nicht dazugerechnet.
    """
    if _K32 is None:
        return None
    untaetig, kern, nutzer = _FILETIME(), _FILETIME(), _FILETIME()
    try:
        if not _K32.GetSystemTimes(ctypes.byref(untaetig), ctypes.byref(kern),
                                   ctypes.byref(nutzer)):
            return None
    except OSError:
        return None

    gesamt = _zahl(kern) + _zahl(nutzer)
    leer = _zahl(untaetig)
    alt = _vorher.get("cpu")
    _vorher["cpu"] = (gesamt, leer)
    if alt is None or gesamt <= alt[0]:
        return None

    d_gesamt = gesamt - alt[0]
    d_leer = leer - alt[1]
    return max(0, min(100, round((d_gesamt - d_leer) / d_gesamt * 100)))


def kerne() -> int:
    """Wie viele Kerne diese Maschine hat -- mindestens einer.

    ``os.cpu_count()`` fragt unter Windows den Kernel und braucht dafuer
    keine der drei Bibliotheken.
    """
    return os.cpu_count() or 1


# --------------------------------------------------------------------------
# Arbeitsspeicher
# --------------------------------------------------------------------------

class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", DWORD),
        ("dwMemoryLoad", DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def speicher() -> dict:
    """Wie viel Arbeitsspeicher da ist und wie viel belegt.

    **Gerechnet wird mit dem physischen Speicher, nicht mit der
    Auslagerungsdatei** -- ``MemAvailable`` unter Linux meint dasselbe.
    ``dwMemoryLoad`` waere der Anteil schon fertig; er wird trotzdem nicht
    genommen, sondern aus denselben zwei Zahlen gerechnet wie unter Linux.
    Zwei Wege zur selben Zahl gehen irgendwann auseinander.
    """
    if _K32 is None:
        return {}
    stand = _MEMORYSTATUSEX()
    stand.dwLength = ctypes.sizeof(stand)
    try:
        if not _K32.GlobalMemoryStatusEx(ctypes.byref(stand)):
            return {}
    except OSError:
        return {}
    gesamt = int(stand.ullTotalPhys)
    frei = int(stand.ullAvailPhys)
    if not gesamt:
        return {}
    return {"gesamt": gesamt, "belegt": gesamt - frei,
            "anteil": round((gesamt - frei) / gesamt * 100)}


# --------------------------------------------------------------------------
# Netz
# --------------------------------------------------------------------------
#
# **Die ganze Struktur steht hier, obwohl nur zwei Felder gebraucht
# werden.** ``InOctets`` liegt 1208 Byte weit hinten; wer die Felder davor
# weglaesst oder falsch ausrichtet, liest eine Zahl, die plausibel
# aussieht und falsch ist -- der schlimmste Fehler, den eine Karte machen
# kann, die sonst nichts behauptet. Die Grenze ist geprueft:
# ``ctypes.sizeof(_MIB_IF_ROW2)`` muss 1352 sein, und die Testreihe haelt
# das fest.

class _GUID(ctypes.Structure):
    _fields_ = [("Data1", DWORD), ("Data2", WORD),
                ("Data3", WORD), ("Data4", ctypes.c_ubyte * 8)]


_ULONG64 = ctypes.c_ulonglong


class _MIB_IF_ROW2(ctypes.Structure):
    _fields_ = [
        ("InterfaceLuid", _ULONG64),
        ("InterfaceIndex", ctypes.c_ulong),
        ("InterfaceGuid", _GUID),
        ("Alias", ctypes.c_wchar * 257),
        ("Description", ctypes.c_wchar * 257),
        ("PhysicalAddressLength", ctypes.c_ulong),
        ("PhysicalAddress", ctypes.c_ubyte * 32),
        ("PermanentPhysicalAddress", ctypes.c_ubyte * 32),
        ("Mtu", ctypes.c_ulong),
        ("Type", ctypes.c_ulong),
        ("TunnelType", ctypes.c_ulong),
        ("MediaType", ctypes.c_ulong),
        ("PhysicalMediumType", ctypes.c_ulong),
        ("AccessType", ctypes.c_ulong),
        ("DirectionType", ctypes.c_ulong),
        # Acht Bitschalter in einem Byte. Die beiden, auf die es ankommt,
        # sind die untersten: 1 = echte Karte, 2 = Filter davor.
        ("InterfaceAndOperStatusFlags", ctypes.c_ubyte),
        ("OperStatus", ctypes.c_ulong),
        ("AdminStatus", ctypes.c_ulong),
        ("MediaConnectState", ctypes.c_ulong),
        ("NetworkGuid", _GUID),
        ("ConnectionType", ctypes.c_ulong),
        ("TransmitLinkSpeed", _ULONG64),
        ("ReceiveLinkSpeed", _ULONG64),
        ("InOctets", _ULONG64),
        ("InUcastPkts", _ULONG64),
        ("InNUcastPkts", _ULONG64),
        ("InDiscards", _ULONG64),
        ("InErrors", _ULONG64),
        ("InUnknownProtos", _ULONG64),
        ("InUcastOctets", _ULONG64),
        ("InMulticastOctets", _ULONG64),
        ("InBroadcastOctets", _ULONG64),
        ("OutOctets", _ULONG64),
        ("OutUcastPkts", _ULONG64),
        ("OutNUcastPkts", _ULONG64),
        ("OutDiscards", _ULONG64),
        ("OutErrors", _ULONG64),
        ("OutUcastOctets", _ULONG64),
        ("OutMulticastOctets", _ULONG64),
        ("OutBroadcastOctets", _ULONG64),
        ("OutQLen", _ULONG64),
    ]


class _MIB_IF_TABLE2(ctypes.Structure):
    _fields_ = [("NumEntries", ctypes.c_ulong), ("Table", _MIB_IF_ROW2 * 1)]


# So gross ist eine Zeile wirklich. Steht hier als Zahl, damit ein Fehler
# in der Struktur oben auffaellt, bevor er als Durchsatz auf der Karte
# landet.
ZEILENGROESSE = 1352

_IF_TYPE_LOOPBACK = 24      # dasselbe "lo", das die Linux-Seite auslaesst
_IF_OPER_UP = 1
_FLAG_ECHTE_KARTE = 0x01
_FLAG_FILTER = 0x02


def _schnittstellen() -> list[tuple[int, int]] | None:
    """Ein- und ausgehende Bytes je Netzwerkkarte, seit dem Systemstart.

    **Gezaehlt wird nur, was eine echte Karte ist.** Windows fuehrt neben
    jeder Karte ihre NDIS-Filter als eigene Zeilen -- Paketplaner,
    WFP-Schichten, der Filter von VirtualBox --, und **jede davon traegt
    dieselben Byte-Zahlen.** Wer stumpf aufsummiert, meldet auf dieser
    Maschine den fuenffachen Durchsatz; genau so ist es beim Bauen
    aufgefallen, und die Zahl sah dabei nicht falsch aus.

    Unterschieden wird an den Bitschaltern: ``echte Karte`` gesetzt,
    ``Filter`` nicht. **Damit ist diese Seite strenger als die Linux-Seite**
    (die nur die Rueckschleife auslaesst) -- und sie muss es sein: Unter
    Linux gibt es diese Doppelzeilen nicht.
    """
    if _IPHLP is None:
        return None
    _IPHLP.GetIfTable2.argtypes = [
        ctypes.POINTER(ctypes.POINTER(_MIB_IF_TABLE2))]
    _IPHLP.GetIfTable2.restype = ctypes.c_ulong
    _IPHLP.FreeMibTable.argtypes = [ctypes.c_void_p]
    _IPHLP.FreeMibTable.restype = None

    zeiger = ctypes.POINTER(_MIB_IF_TABLE2)()
    try:
        if _IPHLP.GetIfTable2(ctypes.byref(zeiger)) != 0:
            return None
    except OSError:
        return None
    gefunden: list[tuple[int, int]] = []
    try:
        tabelle = zeiger.contents
        anzahl = int(tabelle.NumEntries)
        # Die Tabelle traegt EINE Zeile in der Struktur und in Wahrheit
        # beliebig viele dahinter -- das ist die Bauart dieser
        # Schnittstelle. Der Zeiger wird deshalb auf ein Feld der
        # gemeldeten Laenge umgedeutet.
        zeilen = ctypes.cast(
            ctypes.byref(tabelle.Table),
            ctypes.POINTER(_MIB_IF_ROW2 * anzahl)).contents
        for z in zeilen:
            schalter = z.InterfaceAndOperStatusFlags
            if (z.Type == _IF_TYPE_LOOPBACK
                    or z.OperStatus != _IF_OPER_UP
                    or not schalter & _FLAG_ECHTE_KARTE
                    or schalter & _FLAG_FILTER):
                continue
            gefunden.append((int(z.InOctets), int(z.OutOctets)))
    finally:
        _IPHLP.FreeMibTable(zeiger)
    return gefunden


def netz() -> dict:
    """Durchsatz seit der letzten Abfrage, in Byte je Sekunde.

    Alle Karten zusammen -- dieselbe Auskunft und derselbe Aufbau wie
    unter Linux: Ohne Vergleichswert, zu kurz nach der letzten Messung
    oder nach einem Ruecksprung der Zaehler kommt nichts zurueck.

    **Findet sich keine echte Karte, bleibt es leer.** Auf einer Maschine,
    deren Netz nur ueber virtuelle Karten laeuft, ist das der Fall -- und
    eine fehlende Kachel ist dort richtiger als eine Zahl, die denselben
    Verkehr zweimal zaehlt.
    """
    zeilen = _schnittstellen()
    if not zeilen:
        return {}
    rein = sum(z[0] for z in zeilen)
    raus = sum(z[1] for z in zeilen)

    jetzt = time.monotonic()
    alt = _vorher.get("netz")
    _vorher["netz"] = (rein, raus, jetzt)
    if alt is None or jetzt - alt[2] < 0.5 or rein < alt[0]:
        return {}
    dauer = jetzt - alt[2]
    return {"rein": int((rein - alt[0]) / dauer),
            "raus": int((raus - alt[1]) / dauer)}


# --------------------------------------------------------------------------
# Dieser Dienst und diese Maschine
# --------------------------------------------------------------------------

class _PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", DWORD),
        ("PageFaultCount", DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def _eigener_griff():
    """Der Griff auf den eigenen Prozess.

    **Die Typen muessen dastehen, und das ist keine Formsache.** Ohne
    ``restype`` behandelt ctypes den Rueckgabewert als 32-Bit-``int``; der
    Griff auf den eigenen Prozess ist aber ``(HANDLE)-1``, und abgeschnitten
    kommt er als falscher Wert an. Beide Aufrufe darunter meldeten dann
    sauber einen Fehlschlag -- also **keine Zahl, aber auch keine
    Meldung.** Genau so stand die Karte beim ersten Versuch stumm da.
    """
    if _K32 is None:
        return None
    _K32.GetCurrentProcess.argtypes = []
    _K32.GetCurrentProcess.restype = HANDLE
    return _K32.GetCurrentProcess()


def dienst() -> dict:
    """Seit wann dieser Dienst laeuft, und was er selbst belegt.

    ``betrieb`` sind Sekunden seit dem Start **dieses Prozesses**;
    ``speicher`` ist der wirklich belegte Arbeitsspeicher -- unter Windows
    heisst er *Working Set* und ist das, was Linux ``VmRSS`` nennt. Beide
    Zahlen beantworten damit dieselbe Frage wie auf der anderen Seite und
    sind mit dem Speicher der Maschine vergleichbar.

    **Gerechnet wird in der Zeitrechnung des Kernels, nicht in Pythons.**
    Der Startzeitpunkt kommt als FILETIME; verglichen wird er mit
    ``GetSystemTimeAsFileTime`` und nicht mit ``time.time()``. Sonst
    stuenden zwei Uhren gegeneinander, und die Betriebszeit spraenge,
    sobald eine von ihnen gestellt wird.
    """
    griff = _eigener_griff()
    if griff is None:
        return {}
    werte: dict = {}

    erzeugt, beendet, kern, nutzer = (_FILETIME(), _FILETIME(),
                                      _FILETIME(), _FILETIME())
    _K32.GetProcessTimes.argtypes = [
        HANDLE, ctypes.POINTER(_FILETIME), ctypes.POINTER(_FILETIME),
        ctypes.POINTER(_FILETIME), ctypes.POINTER(_FILETIME)]
    _K32.GetProcessTimes.restype = BOOL
    jetzt = _FILETIME()
    _K32.GetSystemTimeAsFileTime.argtypes = [ctypes.POINTER(_FILETIME)]
    _K32.GetSystemTimeAsFileTime.restype = None
    try:
        if _K32.GetProcessTimes(griff, ctypes.byref(erzeugt),
                                ctypes.byref(beendet), ctypes.byref(kern),
                                ctypes.byref(nutzer)):
            _K32.GetSystemTimeAsFileTime(ctypes.byref(jetzt))
            seit_start = (_zahl(jetzt) - _zahl(erzeugt)) / _HNS
            if seit_start >= 0:
                werte["betrieb"] = int(seit_start)
    except OSError:
        pass

    if _PSAPI is not None:
        zaehler = _PROCESS_MEMORY_COUNTERS()
        zaehler.cb = ctypes.sizeof(zaehler)
        _PSAPI.GetProcessMemoryInfo.argtypes = [
            HANDLE, ctypes.POINTER(_PROCESS_MEMORY_COUNTERS),
            DWORD]
        _PSAPI.GetProcessMemoryInfo.restype = BOOL
        try:
            if _PSAPI.GetProcessMemoryInfo(griff, ctypes.byref(zaehler),
                                           zaehler.cb):
                werte["speicher"] = int(zaehler.WorkingSetSize)
        except OSError:
            pass

    return werte


def laufzeit_sekunden() -> int | None:
    """Wie lange die MASCHINE laeuft -- Sekunden, oder nichts.

    Das Gegenstueck zu ``/proc/uptime``. Nicht zu verwechseln mit
    ``dienst()``: Gehen die beiden auseinander, ist der Dienst
    zwischendurch neu gestartet, und genau das will man bei einer
    Fehlersuche wissen.
    """
    if _K32 is None:
        return None
    try:
        _K32.GetTickCount64.argtypes = []
        _K32.GetTickCount64.restype = ctypes.c_ulonglong
        return int(_K32.GetTickCount64() // 1000)
    except (OSError, AttributeError):
        return None


# --------------------------------------------------------------------------
# Was in der Registry steht
# --------------------------------------------------------------------------
#
# **Als eigene Funktion, damit die Testreihe sie ersetzen kann.** Eine
# Pruefung darf nicht davon abhaengen, was auf DIESER Maschine in der
# Registry steht -- so wie die Linux-Seite ihre ufw.conf ueber eine
# Umgebungsvariable umbiegen laesst.

WINREG_SYSTEM = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
WINREG_BIOS = r"HARDWARE\DESCRIPTION\System\BIOS"

# Die drei Profile der Windows-Firewall, und der Schluessel, den
# "netsh advfirewall set ... state on" umschreibt. Er ist ohne
# Administratorrechte lesbar -- dieselbe Lage wie bei /etc/ufw/ufw.conf.
WINREG_FIREWALL = (
    r"SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters"
    r"\FirewallPolicy")
FIREWALL_PROFILE = (
    ("DomainProfile", "Domäne"),
    ("StandardProfile", "Privat"),
    ("PublicProfile", "Öffentlich"),
)


def registrywert(pfad: str, name: str):
    """Ein Wert aus HKEY_LOCAL_MACHINE -- oder None.

    ``None`` heisst: nicht da, nicht lesbar, oder kein Windows. **Es heisst
    nie „aus" oder „null".** Was ein fehlender Wert bedeutet, entscheidet
    der Aufrufer; hier wird nichts gedeutet.
    """
    if not IST_WINDOWS:
        return None
    try:
        import winreg
    except ImportError:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, pfad) as schluessel:
            return winreg.QueryValueEx(schluessel, name)[0]
    except OSError:
        return None


def systemname() -> str:
    """Welches Windows das ist -- die Zeile *Distribution* im Bericht.

    **``ProductName`` aus der Registry allein waere falsch, und zwar
    vorhersehbar:** Auf einem Windows 11 steht dort weiter *Windows 10
    Pro* -- auf dieser Maschine nachgesehen, Build 22631. Microsoft hat
    den Wert stehen gelassen, damit alte Programme weiter funktionieren.

    Zusammengesetzt wird deshalb aus drei Quellen, die je fuer sich
    stimmen: die Fassung aus ``platform`` (die rechnet sie aus der
    Build-Nummer), die Ausgabe (*Professional*) und die Fassung des Jahres
    (*23H2*) samt Build aus der Registry.
    """
    if not IST_WINDOWS:
        return ""
    teile = ["Windows %s" % platform.release()]
    ausgabe = getattr(platform, "win32_edition", lambda: "")() or ""
    if ausgabe:
        teile.append(ausgabe)
    fassung = registrywert(WINREG_SYSTEM, "DisplayVersion")
    if fassung:
        teile.append(str(fassung))
    build = registrywert(WINREG_SYSTEM, "CurrentBuild")
    name = " ".join(teile)
    return "%s (Build %s)" % (name, build) if build else name


# Woran eine Maschine zu erkennen ist, wenn sie keine ist. Gelesen wird,
# was das BIOS meldet -- derselbe Weg, den systemd-detect-virt unter
# Linux zuerst geht.
#
# **Der Hersteller steht in der Ausgabe, nicht das Produkt** -- dieselbe
# Falle wie bei Boots "oracle": Wer "innotek GmbH" liest und nicht weiss,
# dass das VirtualBox ist, sucht eine Firma.
VIRT_BIOS = (
    ("innotek", "VirtualBox"),
    ("virtualbox", "VirtualBox"),
    ("vmware", "VMware"),
    ("qemu", "QEMU"),
    ("kvm", "KVM"),
    ("bochs", "QEMU/Bochs"),
    ("xen", "Xen"),
    ("parallels", "Parallels"),
    ("hyper-v", "Hyper-V"),
    ("virtual machine", "Hyper-V"),
    ("proxmox", "Proxmox"),
)


def virtualisierung() -> str:
    """Laeuft dieses Windows in einer VM, und wenn ja, in welcher?

    **Die Antwort ist ein Hinweis und keine Feststellung**, und der Text
    sagt das auch: Gelesen werden Hersteller und Produktname aus dem
    BIOS. Eine VM, die beides auf die Werte einer echten Maschine stellt,
    ist von hier aus nicht zu erkennen -- dafuer braeuchte es, was
    ``systemd-detect-virt`` tut, und das gibt es hier nicht.

    Steht nichts Verdaechtiges da, heisst die Antwort **nicht** „keine":
    Sie nennt Hersteller und Modell und laesst den Leser schliessen. Der
    Unterschied ist derselbe wie unter Linux zwischen *„none"* und *„nicht
    feststellbar"* -- nur liegt die Grenze hier woanders.
    """
    hersteller = str(registrywert(WINREG_BIOS, "SystemManufacturer") or "")
    produkt = str(registrywert(WINREG_BIOS, "SystemProductName") or "")
    zusammen = ("%s %s" % (hersteller, produkt)).strip()
    if not zusammen:
        return "nicht feststellbar"
    klein = zusammen.lower()
    for muster, name in VIRT_BIOS:
        if muster in klein:
            return "%s (BIOS: %s)" % (name, zusammen)
    return "%s — dem BIOS nach keine VM" % zusammen


def firewall() -> dict:
    """Was die Windows-Firewall meldet -- je Profil an oder aus.

    **Gemeldet, nicht geprueft**, genau wie unter Linux: Gelesen wird der
    Schalter, den ``netsh advfirewall set`` umschreibt. Ob eine Regel
    diesen Dienst durchlaesst, steht hier nicht -- das waere eine
    Behauptung ueber ein Regelwerk, das aus mehreren Speichern
    zusammenkommt (lokal, Gruppenrichtlinie) und dessen Auswertung
    niemand ohne Administratorrechte nachvollziehen kann.

    ``an`` ist ``True``, ``False`` **oder ``None``**. Das Dritte ist neu
    gegenueber der Linux-Seite und noetig: Fehlt der Wert, ist die
    ehrliche Auskunft *nicht feststellbar*. Windows laeuft von Haus aus
    mit eingeschalteter Firewall -- daraus „also an" zu schliessen, waere
    geraten, und zwar an der Stelle, an der es am meisten kostet.
    """
    gefunden = []
    for schluessel, name in FIREWALL_PROFILE:
        wert = registrywert("%s\\%s" % (WINREG_FIREWALL, schluessel),
                            "EnableFirewall")
        gefunden.append({
            "name": "Windows-Firewall — %s" % name,
            # Fuer das Abzeichen im Kartenkopf: Dort stehen drei Namen
            # nebeneinander, und dreimal "Windows-Firewall" davor waere
            # eine Zeile, die niemand liest.
            "kurz": name,
            "an": None if wert is None else bool(wert),
        })
    return {"gefunden": gefunden,
            "quelle": "HKLM\\%s" % WINREG_FIREWALL}
