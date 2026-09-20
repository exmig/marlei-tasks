#!/usr/bin/env bash
# ===========================================================================
# Installiert MARLEI Tasks auf Debian, Ubuntu oder Raspberry Pi OS.
#
# Aufruf im geklonten Projekt, als root:
#     sudo ./setup/linux/install.sh
#
# Die Oberflaeche hoert auf **Port 8081**. Das ist der Produktport dieses
# Werkzeugs, nicht die 80: Auf einer Maschine mit MARLEI Boot ist die 80
# vergeben, und ein Port, der mal so und mal so ist, gehoert in kein
# Lesezeichen. Anders geht auch:
#     sudo MARLEI_PORT=80 ./setup/linux/install.sh
#
# Das Skript ist wiederholbar: ein zweiter Aufruf aktualisiert nur.
#
# ---------------------------------------------------------------------------
# NEBEN MARLEI BOOT AUF DERSELBEN MASCHINE
#
# Das geht, und alles Trennbare ist getrennt: eigener Benutzer, eigenes
# Verzeichnis, eigene Einheit, eigene Umgebungsdatei, eigenes venv, eigener
# Anwendungsport (18081 gegen Boots 8080, siehe docs/ports.md).
#
# **Der Weg von aussen ist der einzige, den es nur einmal gibt.** Boots
# vhost traegt "listen 80 default_server" und faengt damit alles ab, was
# auf 80 hereinkommt. Ein zweiter vhost auf demselben Port waere still
# unerreichbar -- oder, mit einem zweiten default_server, das Ende von
# nginx und damit des Bootservers.
#
# Dieses Skript fasst Boots Dateien deshalb nicht an und bricht lieber ab,
# als einen belegten Port zu ueberschreiben.
# ===========================================================================
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

APP_DIR=/opt/marlei-tasks
DATA_DIR=/var/lib/marlei-tasks
ENV_DATEI=/etc/marlei-tasks.env
DIENST=marlei-tasks
VHOST=/etc/nginx/sites-available/marlei-tasks

log()  { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[X]\033[0m %s\n' "$*" >&2; exit 1; }

[[ -d "$SRC_DIR/webui" ]] || die "$SRC_DIR ist kein Projektordner (webui/ fehlt).
    Aufrufen aus dem geklonten Projekt:  sudo <projekt>/setup/linux/install.sh"

[[ $EUID -eq 0 ]] || die "Bitte als root ausfuehren:  sudo $0"

# --------------------------------------------------------------------------
# Laeuft das hier auf einem System, das dieses Skript kennt?
# --------------------------------------------------------------------------
# Es kennt eine Familie: Debian und was davon abstammt. Es benutzt
# apt-get, systemd und die Paketnamen dieser Familie. Auf allem anderen
# bricht es ab, statt auf halbem Weg liegenzubleiben.
OS_ID=""; OS_LIKE=""; OS_NAME="unbekannt"
if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  OS_ID="${ID:-}"; OS_LIKE="${ID_LIKE:-}"; OS_NAME="${PRETTY_NAME:-$OS_ID}"
fi
case " $OS_ID $OS_LIKE " in
  *" debian "*|*" ubuntu "*|*" raspbian "*) ;;
  *) die "Dieses Skript kennt Debian und was davon abstammt -- hier laeuft:
    $OS_NAME
    Auf anderen Systemen sind Paketnamen und Dienstverwaltung andere; ein
    Lauf wuerde auf halbem Weg abbrechen und Reste hinterlassen." ;;
esac

command -v systemctl >/dev/null || die "systemd fehlt -- dieses Skript legt eine
    Dienst-Einheit an und kann sie sonst nicht starten."

echo "    System        : $OS_NAME"

# --------------------------------------------------------------------------
# Adresse und Port
# --------------------------------------------------------------------------
IFACE="${MARLEI_IFACE:-$(ip -4 route show default | awk '{print $5; exit}')}"
[[ -n "$IFACE" ]] || die "Keine Netzwerkkarte mit Standardroute gefunden.
    Ueberschreiben mit:  sudo MARLEI_IFACE=enp0s3 $0"
SERVER_IP="${MARLEI_IP:-$(ip -4 -o addr show dev "$IFACE" | awk '{split($4,a,"/"); print a[1]; exit}')}"
[[ -n "$SERVER_IP" ]] || die "Auf $IFACE liegt keine IPv4-Adresse.
    Ueberschreiben mit:  sudo MARLEI_IP=192.168.178.31 $0"

# 8081 UND NICHT 80, entschieden am 07.09.2026. Die 80 waere die
# naheliegende Wahl -- und auf jeder Maschine mit MARLEI Boot die
# falsche. Ein fester Produktport ist an beiden Stellen richtig und muss
# nirgends erklaert werden; wer die 80 will, sagt es. Die Tabelle aller
# Module: docs/ports.md.
#
# **Ohne MARLEI_PORT gilt der Port der bestehenden Installation, erst
# dann die Vorgabe.** Bis September 2026 hiess ohne Angabe immer 8081 --
# ein erneuter Aufruf auf einer Installation mit anderem Port stellte sie
# still zurueck. update.sh las den Port schon immer aus dem vhost; jetzt
# tut es dieses Skript selbst, damit der direkte Aufruf dasselbe tut.
if [[ -n "${MARLEI_PORT:-}" ]]; then
  PORT="$MARLEI_PORT"; PORT_HER="angegeben"
else
  PORT="$(sed -n 's/^[[:space:]]*listen[[:space:]]\+\([0-9]\+\);.*/\1/p' \
          "$VHOST" 2>/dev/null | head -1)"
  if [[ -n "$PORT" ]]; then
    PORT_HER="wie bisher, aus dem vhost"
  else
    PORT=8081; PORT_HER="Vorgabe, docs/ports.md"
  fi
fi
[[ "$PORT" =~ ^[0-9]+$ ]] && (( PORT > 0 && PORT < 65536 )) \
  || die "MARLEI_PORT=$PORT ist keine Portnummer."

echo "    Netzwerkkarte : $IFACE"
echo "    Server-IP     : $SERVER_IP"
echo "    Port          : $PORT  ($PORT_HER)"

# --------------------------------------------------------------------------
log "Ist der Port frei?"
# --------------------------------------------------------------------------
# ZWEI PRUEFUNGEN, WEIL ES ZWEI ARTEN GIBT, DENSELBEN PORT ZU BELEGEN.
#
# Die erste findet einen fremden Dienst, der schon auf dem Port sitzt --
# der faellt beim Start von nginx auf, aber dann ist die halbe
# Installation gelaufen.
#
# Die zweite findet den Fall, den man NICHT sieht: einen anderen
# nginx-vhost auf demselben Port. nginx startet damit klaglos, nennt die
# doppelte Verwendung eine Warnung im Log -- und diese Oberflaeche waere
# unerreichbar, ohne dass irgendwo ein Fehler stuende. Genau so liegt es
# auf einer Maschine, auf der MARLEI Boot laeuft.
port_frei_pruefen() {
  local belegt="" datei=""

  if command -v ss >/dev/null; then
    # Nur unsere eigene Einheit und nginx zaehlen nicht als fremd: Beim
    # zweiten Lauf haelt nginx den Port ja selbst.
    belegt="$(ss -lntpH "sport = :$PORT" 2>/dev/null \
              | grep -v 'users:(("nginx"' || true)"
    if [[ -n "$belegt" ]]; then
      die "Auf Port $PORT hoert bereits etwas anderes:
    $(echo "$belegt" | head -1)
    Einen anderen Port waehlen:  sudo MARLEI_PORT=9090 $0"
    fi
  else
    warn "ss fehlt -- der Port wurde nicht geprueft."
  fi

  # Ein anderer vhost auf demselben Port. Gesucht wird in allen
  # eingeschalteten Seiten ausser unserer eigenen.
  shopt -s nullglob
  for datei in /etc/nginx/sites-enabled/*; do
    [[ "$(readlink -f "$datei")" == "$(readlink -f "$VHOST")" ]] && continue
    if grep -Eq "^[[:space:]]*listen[[:space:]]+(\[::\]:)?$PORT([[:space:]]|;)" "$datei"; then
      die "Ein anderer nginx-vhost hoert schon auf Port $PORT:
    $datei
    Zwei vhosts auf einem Port heisst: einer davon ist unerreichbar, und
    nginx sagt es nur im Log. Liegt dort MARLEI Boot, waere es dieser hier.
    Einen anderen Port waehlen:  sudo MARLEI_PORT=9090 $0"
    fi
  done
  shopt -u nullglob
  echo "    Port $PORT ist frei."
}
port_frei_pruefen

# --------------------------------------------------------------------------
log "Pakete installieren"
# --------------------------------------------------------------------------
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y --no-install-recommends \
  nginx curl ca-certificates rsync \
  python3 python3-venv python3-pip

# --------------------------------------------------------------------------
log "Verzeichnisse und Dienstkonto anlegen"
# --------------------------------------------------------------------------
id "$DIENST" &>/dev/null \
  || useradd --system --home-dir "$DATA_DIR" --shell /usr/sbin/nologin "$DIENST"

mkdir -p "$APP_DIR" "$DATA_DIR"
chown -R "$DIENST:$DIENST" "$DATA_DIR"
# Die Ablage darf niemand sonst lesen: In einer Aufgabenverwaltung steht,
# woran eine Firma arbeitet.
chmod 0750 "$DATA_DIR"

# --------------------------------------------------------------------------
log "Anwendung kopieren"
# --------------------------------------------------------------------------
rsync -a --delete \
      --exclude '__pycache__' --exclude '*.db' --exclude 'venv' \
      "$SRC_DIR/webui/" "$APP_DIR/"

# Welcher Stand hier eingebaut wurde. Die Anwendung liegt als rsync-Kopie
# ohne .git und kann nicht selbst nachsehen. Der Stempel muss NACH dem
# rsync entstehen: der laeuft mit --delete und raeumte die Datei sonst bei
# jedem Lauf wieder weg.
#
# "safe.directory": Dieses Skript laeuft als root, der Projektordner
# gehoert einem normalen Benutzer. Ohne die Angabe verweigert Git die
# Auskunft ("detected dubious ownership").
git_im_projekt() {
  git -C "$SRC_DIR" -c safe.directory="$SRC_DIR" "$@" 2>/dev/null
}

if command -v git >/dev/null && git_im_projekt rev-parse --git-dir >/dev/null; then
  STAND="$(git_im_projekt describe --tags --always --dirty || echo unbekannt)"
else
  # Kein Git -- etwa ein entpacktes Archiv. Kein Fehler, nur weniger
  # Auskunft. LIEBER KEINE ANGABE ALS EINE ERFUNDENE: Eine Versionsnummer,
  # die niemand nachvollziehen kann, ist schlimmer als gar keine.
  STAND="ohne Git"
fi
printf '%s\n' "$STAND" > "$APP_DIR/VERSION"
chmod 0644 "$APP_DIR/VERSION"
echo "    Stand: $STAND"

if [[ ! -d "$APP_DIR/venv" ]]; then
  python3 -m venv "$APP_DIR/venv"
fi
"$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

# --------------------------------------------------------------------------
log "Einstellungen schreiben"
# --------------------------------------------------------------------------
# Eine vorhandene Datei wird nur in der Basis-URL angepasst, damit eigene
# Aenderungen (Ausgang, Kennzeichnung) einen erneuten Lauf ueberleben.
VORLAGE="$SRC_DIR/setup/linux/files/marlei-tasks.env.example"
ADRESSE="http://$SERVER_IP"
[[ "$PORT" == "80" ]] || ADRESSE="http://$SERVER_IP:$PORT"

if [[ -f "$ENV_DATEI" ]]; then
  sed -i "s|^MARLEI_BASE_URL=.*|MARLEI_BASE_URL=$ADRESSE|" "$ENV_DATEI"
else
  sed -e "s|^MARLEI_BASE_URL=.*|MARLEI_BASE_URL=$ADRESSE|" \
      "$VORLAGE" > "$ENV_DATEI"
fi
chown root:"$DIENST" "$ENV_DATEI"
# Lesbar fuer den Dienst, schreibbar nur fuer root -- die Karte
# "Einstellungen" zeigt sie an und aendert nichts, und das ist Absicht.
chmod 0640 "$ENV_DATEI"

# Was die Vorlage kennt und die Datei nicht, wird nachgetragen -- mit dem
# Wert und den Kommentarzeilen aus der Vorlage.
#
# **Der dritte Fall.** Oben stehen zwei: Datei fehlt (aus der Vorlage
# erzeugen) und Datei ist da (nur die Adresse anfassen). Dazwischen fehlt
# einer: Ein Name, den die Vorlage kennt und die Datei nicht, ist keine
# eigene Aenderung, sondern eine Luecke -- die entsteht, sobald der Code
# einen Wert dazubekommt. Ueberschrieben wird dabei nichts.
#
# Aus MARLEI Boot uebernommen, wo genau das auf der produktiven Maschine
# aufgefallen ist.
nachtragen_aus_vorlage() {
  local zeile schluessel kommentar="" nachgetragen=0
  [[ -r "$VORLAGE" ]] || return 0
  while IFS= read -r zeile; do
    if [[ "$zeile" =~ ^# ]]; then
      kommentar+="${zeile}"$'\n'
      continue
    fi
    if [[ -z "$zeile" ]]; then
      kommentar=""
      continue
    fi
    if [[ "$zeile" =~ ^([A-Z][A-Z0-9_]*)= ]]; then
      schluessel="${BASH_REMATCH[1]}"
      if ! grep -q "^$schluessel=" "$ENV_DATEI"; then
        {
          echo ""
          [[ -n "$kommentar" ]] && printf '%s' "$kommentar"
          echo "$zeile"
        } >> "$ENV_DATEI"
        echo "    nachgetragen: $schluessel"
        nachgetragen=$((nachgetragen + 1))
      fi
    fi
    kommentar=""
  done < "$VORLAGE"
  [[ $nachgetragen -gt 0 ]] && echo "    $nachgetragen Wert(e) nachgetragen"
  return 0
}
nachtragen_aus_vorlage

# --------------------------------------------------------------------------
log "Kennwort der Oberflaeche"
# --------------------------------------------------------------------------
# Gefragt wird, wenn keines gesetzt ist oder MARLEI_KENNWORT=neu dasteht.
# Ist eines gesetzt, bleibt es -- ein Update fragt nicht jedes Mal.
#
# **Das Kennwort steht nie auf einer Befehlszeile.** Es wird verdeckt
# gelesen und ueber die Standardeingabe an anmeldung.py gegeben, das den
# Hash ausrechnet; in die Datei kommt nur der. Eine Befehlszeile saehe
# jeder, der auf der Maschine "ps" tippt, und die Shell merkte sie sich.
#
# **Leer lassen heisst: ohne Kennwort.** Das ist erlaubt, aber es wird
# gesagt -- hier und danach im Band auf jeder Seite.
HASH_JETZT="$(sed -n 's|^MARLEI_KENNWORT_HASH=||p' "$ENV_DATEI" | head -1)"
if [[ -n "$HASH_JETZT" && "${MARLEI_KENNWORT:-}" != "neu" ]]; then
  echo "    gesetzt. Neu setzen:  sudo MARLEI_KENNWORT=neu $0"
elif [[ ! -t 0 ]]; then
  # Ohne Terminal kann niemand antworten. Abbrechen waere hier zu hart:
  # Ein Update, das in einer Pipeline laeuft, bliebe sonst halb stehen.
  warn "Kein Terminal -- das Kennwort bleibt, wie es ist$( [[ -z "$HASH_JETZT" ]] && echo ' (keines)')."
else
  while :; do
    read -rs -p "    Kennwort (mind. 8 Zeichen, leer = ohne): " KW1; echo
    if [[ -z "$KW1" ]]; then
      if [[ -n "$HASH_JETZT" ]]; then
        echo "    Nichts eingegeben -- das bisherige bleibt."
      else
        warn "Ohne Kennwort: Wer die Oberflaeche im Netz erreicht, darf alles."
      fi
      break
    fi
    read -rs -p "    noch einmal: " KW2; echo
    if [[ "$KW1" != "$KW2" ]]; then
      warn "Die beiden Eingaben sind verschieden -- noch einmal."
      continue
    fi
    # Zu kurz meldet anmeldung.py selbst, mit Rueckgabewert 2.
    if HASH_NEU="$(printf '%s\n' "$KW1" | "$APP_DIR/venv/bin/python" "$APP_DIR/anmeldung.py")"; then
      sed -i "s|^MARLEI_KENNWORT_HASH=.*|MARLEI_KENNWORT_HASH=$HASH_NEU|" "$ENV_DATEI"
      echo "    gesetzt. Bestehende Anmeldungen enden damit."
      break
    fi
  done
  unset KW1 KW2
fi

# Der Ausgang des Exports. Er steht in der Umgebungsdatei und darf
# woanders liegen -- etwa in einem Git-Repository; dann bekommt der
# Bestand eine Versionsgeschichte. Angelegt wird er hier nur, wenn er
# unterhalb des Datenverzeichnisses liegt: Ein fremder Pfad gehoert
# jemand anderem, und dieses Skript legt dort nichts an.
AUSGANG="$(sed -n 's|^MARLEI_EXPORT=||p' "$ENV_DATEI" | head -1)"
if [[ -n "$AUSGANG" && "$AUSGANG" == "$DATA_DIR"/* ]]; then
  mkdir -p "$AUSGANG"
  chown -R "$DIENST:$DIENST" "$AUSGANG"
elif [[ -n "$AUSGANG" && ! -d "$AUSGANG" ]]; then
  warn "Der Ausgang $AUSGANG gibt es nicht -- er gehoert nicht unter
    $DATA_DIR, deshalb legt dieses Skript ihn nicht an. Die Karte
    'Ablageorte' sagt es ebenfalls."
fi

# Liegt der Ausgang ausserhalb, muss die Einheit ihn ausdruecklich
# freigeben: ProtectSystem=strict macht sonst alles ausser
# /var/lib/marlei-tasks schreibgeschuetzt.
install -m 0644 "$SRC_DIR/setup/linux/files/marlei-tasks.service" \
        /etc/systemd/system/$DIENST.service
if [[ -n "$AUSGANG" && "$AUSGANG" != "$DATA_DIR"/* ]]; then
  sed -i "s|^ReadWritePaths=-.*|ReadWritePaths=-$AUSGANG|" \
      /etc/systemd/system/$DIENST.service
  echo "    Ausgang ausserhalb der Ablage -- freigegeben: $AUSGANG"
fi

# --------------------------------------------------------------------------
log "nginx einrichten"
# --------------------------------------------------------------------------
sed -e "s|@@PORT@@|$PORT|g" \
    "$SRC_DIR/setup/linux/files/nginx-marlei-tasks.conf" > "$VHOST"
ln -sf "$VHOST" /etc/nginx/sites-enabled/marlei-tasks

# Die mitgelieferte Standardseite von nginx belegt Port 80 mit einem
# "default_server". Weg damit -- ABER NUR, wenn wir selbst auf 80 sind:
# Auf einem anderen Port stoert sie nicht, und eine Datei zu entfernen,
# die einem nicht im Weg steht, ist ein Uebergriff.
if [[ "$PORT" == "80" && -e /etc/nginx/sites-enabled/default ]]; then
  rm -f /etc/nginx/sites-enabled/default
  echo "    nginx-Standardseite abgeschaltet (sie belegte Port 80)."
fi

nginx -t

# --------------------------------------------------------------------------
log "Dienste starten"
# --------------------------------------------------------------------------
systemctl daemon-reload
systemctl enable --now nginx "$DIENST" >/dev/null
systemctl restart "$DIENST"
# RELOAD statt restart: Laeuft auf dieser Maschine noch etwas anderes
# hinter demselben nginx -- MARLEI Boot etwa --, dann faellt es bei einem
# restart kurz aus. Ein reload wechselt die Konfiguration, ohne die
# laufenden Verbindungen abzureissen.
systemctl reload nginx

sleep 2
for unit in nginx "$DIENST"; do
  if systemctl is-active --quiet "$unit"; then
    echo "    $unit: laeuft"
  else
    warn "$unit laeuft NICHT -- 'sudo journalctl -u $unit -n 40' zeigt warum."
  fi
done

# --------------------------------------------------------------------------
log "Selbsttest"
# --------------------------------------------------------------------------
if curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null; then
  echo "    Die Oberflaeche antwortet."
else
  warn "Die Oberflaeche antwortet nicht auf http://127.0.0.1:$PORT/health"
fi

cat <<INFO

===========================================================================
 Fertig.

   Oberflaeche :  $ADRESSE/
   Ablage      :  $DATA_DIR/tasks.db
   Einstellung :  $ENV_DATEI

 Der erste Schritt steht auf dem Reiter Projekte: ein Projekt anlegen --
 und dazu mindestens einen Bereich, sonst nimmt die Sammlung nichts an.

===========================================================================
INFO

if [[ "$PORT" != "80" ]]; then
  cat <<HINWEIS
 Dieses Werkzeug hoert auf Port $PORT und nicht auf 80. Der Port gehoert
 damit in jedes Lesezeichen -- und in eine Firewallregel, falls hier eine
 laeuft. Was zu oeffnen waere, sagt die Karte "Firewall" unter
 Einrichtung; eingerichtet wird sie von diesem Server nicht.

 Aendern heisst: erneut installieren, mit der Zahl daneben --
   sudo MARLEI_PORT=80 $0

===========================================================================
HINWEIS
fi
