#!/usr/bin/env bash
# ===========================================================================
# Holt auf dem Server den neuesten Stand und uebernimmt ihn.
#
#     ./setup/linux/update.sh
#
# Bewusst OHNE sudo aufrufen: "git pull" soll mit deinem Benutzer und
# deinem SSH-Schluessel laufen, nicht als root. Fuer install.sh fragt das
# Skript selbst nach dem Passwort.
#
# ---------------------------------------------------------------------------
# DER PORT WIRD GEMERKT, NICHT ERFRAGT
#
# install.sh nimmt den Port aus MARLEI_PORT und faellt sonst auf 80
# zurueck. Auf einer Maschine mit MARLEI Boot ist die 80 belegt -- ein
# Update ohne die Angabe braeche also ab, obwohl die Installation laengst
# steht und laeuft.
#
# Deshalb liest dieses Skript den Port aus dem installierten vhost:
# **Ein zweiter Lauf soll nicht anders ausfallen als der erste.**
#
# ---------------------------------------------------------------------------
# INSTALLIERT WIRD, WENN DIE INSTALLATION ZURUECKLIEGT -- NICHT, WENN DER
# PULL ETWAS GEBRACHT HAT
#
# Bis zum 19.09.2026 hing es am Pull: vorher und nachher derselbe Commit,
# also "Schon aktuell". Das stimmte nur, solange Repository und Installation
# immer gemeinsam weiterruecken. Drei Faelle, in denen sie es nicht tun:
# ein "git pull" von Hand vor dem Update, ein Update, dessen Installation
# abbrach, und der Rechner, auf dem entwickelt wird. Jedes Mal lief der
# alte Stand weiter, und das Skript sagte, alles sei aktuell.
#
# Verglichen wird deshalb der Stempel der Installation ($VERSION_DATEI)
# mit dem, den install.sh jetzt schreiben wuerde -- **mit demselben Befehl,
# damit beide Seiten dieselbe Sprache sprechen.** Ein Stand mit "-dirty"
# wird immer uebernommen: Was darin geaendert ist, sagt der Stempel nicht.
# ===========================================================================
set -euo pipefail

PROJEKT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VHOST=/etc/nginx/sites-available/marlei-tasks
# Der Stempel, den install.sh schreibt -- dort APP_DIR/VERSION.
VERSION_DATEI=/opt/marlei-tasks/VERSION

log()  { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[X]\033[0m %s\n' "$*" >&2; exit 1; }

[[ $EUID -ne 0 ]] || die "Bitte OHNE sudo aufrufen -- git soll deinem Benutzer gehoeren."

cd "$PROJEKT"
git rev-parse --git-dir >/dev/null 2>&1 \
  || die "$PROJEKT ist kein Git-Repository. Erst klonen -- siehe docs/installation.md."

VORHER="$(git rev-parse HEAD)"

log "Neuen Stand holen"
# --ff-only: lieber sauber abbrechen als einen Merge-Commit erzeugen. Der
# Server soll nur nachziehen; entwickelt wird auf dem Arbeitsplatz.
if ! git pull --ff-only; then
  echo
  echo "Der Stand laesst sich nicht ohne Weiteres uebernehmen."
  echo "Meist wurde hier auf dem Server etwas veraendert. Was, zeigt:"
  echo "    git -C $PROJEKT status"
  echo
  echo "Wegwerfen und stur den Stand aus dem Repository nehmen:"
  echo "    git -C $PROJEKT fetch origin && git -C $PROJEKT reset --hard origin/main"
  exit 1
fi

NACHHER="$(git rev-parse HEAD)"

# Was laeuft, und was wuerde jetzt installiert? Dieselbe Formel wie in
# install.sh, sonst sprechen die beiden Stempel nie dieselbe Sprache.
#
# GELESEN WIRD DAS FELD "stand", nicht die ganze Datei. Seit dem
# 22.09.2026 stehen dort vier Felder (stand, commit, zweig, installiert),
# weil die Karte "Stand" in der Oberflaeche den Commit braucht. Hier stand
# bis dahin ein "tr -d", das alle Zeichen ohne Leerraum zusammenzog -- mit
# der neuen Datei ergaebe das eine Zeichenkette aus Kommentar und allen
# vier Feldern, und die ist mit keinem "git describe" je gleich. Die
# Folgen waeren still: "Schon aktuell" griffe nie mehr, und gezaehlt
# wuerde vom Stand vor dem Pull statt vom installierten.
#
# Die alte einzeilige Datei wird weiter gelesen -- dieselbe Ruecksicht wie
# in webui/versionsstand.py: Eine Installation von vor diesem Tag traegt
# sie noch, und genau die will ja aktualisiert werden.
INSTALLIERT=""
if [[ -r "$VERSION_DATEI" ]]; then
  INSTALLIERT="$(sed -n 's/^stand=//p' "$VERSION_DATEI" | head -1 \
                 | tr -d '[:space:]')"
  if [[ -z "$INSTALLIERT" ]]; then
    # Keine Feldzeile gefunden: die alte Fassung, in der nur der Stand
    # steht. Kommentarzeilen faellt sie nicht an, aber sicher ist sicher.
    INSTALLIERT="$(grep -v '^[[:space:]]*#' "$VERSION_DATEI" \
                   | tr -d '[:space:]' || true)"
  fi
fi
JETZT="$(git describe --tags --always --dirty 2>/dev/null || echo unbekannt)"

if [[ "$INSTALLIERT" == "$JETZT" && "$JETZT" != *-dirty ]]; then
  log "Schon aktuell ($(git log -1 --format='%h %s'))"
  echo "    Installiert ist genau dieser Stand."
  echo "    install.sh trotzdem ausfuehren? Dann direkt:"
  echo "      sudo ${MARLEI_PORT:+MARLEI_PORT=$MARLEI_PORT }$PROJEKT/setup/linux/install.sh"
  exit 0
fi

# Von wo aus gezaehlt wird, was dazukommt: vom installierten Stand, wenn
# Git ihn kennt -- sonst vom Stand vor dem Pull. Der Stempel ist eine
# Ausgabe von "git describe" und laesst sich deshalb zurueckuebersetzen;
# nur das "-dirty" kennt Git nicht.
BASIS="$VORHER"
if [[ -n "$INSTALLIERT" ]]    && git rev-parse -q --verify "${INSTALLIERT%-dirty}^{commit}" >/dev/null; then
  BASIS="$(git rev-parse "${INSTALLIERT%-dirty}^{commit}")"
fi

if [[ "$VORHER" == "$NACHHER" ]]; then
  log "Nichts Neues geholt -- aber die Installation liegt zurueck"
  echo "    installiert: ${INSTALLIERT:-unbekannt}"
  echo "    im Projekt:  $JETZT"
fi

if [[ "$BASIS" != "$NACHHER" ]]; then
  log "Diese Aenderungen sind dazugekommen"
  git --no-pager log --oneline "$BASIS..$NACHHER"
  echo
  git --no-pager diff --stat "$BASIS..$NACHHER"
fi

# Aendert sich die Ablage, ist eine Kopie vorher billig -- und hinterher
# unmoeglich. Beim Start zieht die Anwendung fehlende Spalten nach und
# entfernt entfallene; das ist gewollt und laesst sich nicht rueckgaengig
# machen. GESAGT, NICHT GETAN: Wohin eine Sicherung gehoert, weiss der
# Betreiber, nicht dieses Skript.
if git diff --name-only "$BASIS..$NACHHER" | grep -q 'webui/datenbank.py'; then
  cat <<HINWEIS

---------------------------------------------------------------------------
 An der Ablage hat sich etwas geaendert. Beim naechsten Start zieht die
 Anwendung Spalten nach oder entfernt entfallene -- eine Kopie vorher
 kostet eine Sekunde:

   sudo cp /var/lib/marlei-tasks/tasks.db ~/tasks-$(date +%Y%m%d).db

---------------------------------------------------------------------------
HINWEIS
fi

# Welcher Port gilt hier? Aus dem installierten vhost gelesen, damit ein
# Update nicht an der Portpruefung scheitert. Eine Angabe von aussen
# gewinnt: Wer MARLEI_PORT setzt, will genau das.
if [[ -z "${MARLEI_PORT:-}" && -r "$VHOST" ]]; then
  GEFUNDEN="$(sed -n 's/^[[:space:]]*listen[[:space:]]\+\([0-9]\+\);.*/\1/p' \
              "$VHOST" | head -1)"
  if [[ -n "$GEFUNDEN" ]]; then
    export MARLEI_PORT="$GEFUNDEN"
    echo
    echo "    Port aus $VHOST: $MARLEI_PORT"
  fi
fi
if [[ -z "${MARLEI_PORT:-}" ]]; then
  warn "Kein Port gefunden -- install.sh nimmt die 80. Laeuft auf dieser
    Maschine MARLEI Boot, bricht es dort ab und sagt es."
fi

log "Uebernehmen"
chmod +x "$PROJEKT"/setup/linux/*.sh
sudo ${MARLEI_PORT:+MARLEI_PORT="$MARLEI_PORT"} "$PROJEKT/setup/linux/install.sh"
