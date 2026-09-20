#!/usr/bin/env bash
# ===========================================================================
# Entfernt MARLEI Tasks von diesem Server.
#
# Aufruf als root:
#     sudo ./setup/linux/uninstall.sh
#
# **Der Bestand bleibt.** Weg sind danach die Anwendung, die Einheit und
# der nginx-vhost; die Ablage, die Einstellungen und der Ausgang bleiben
# liegen, und das Skript sagt am Ende, wo. Wer auch die weghaben will,
# verlangt es -- und schreibt das Wort dann ein zweites Mal:
#
#     sudo ./setup/linux/uninstall.sh --bestand
#
# ---------------------------------------------------------------------------
# WAS NICHT ANGEFASST WIRD, UND WARUM
#
# **nginx bleibt stehen.** Auf einer Maschine mit MARLEI Boot waere ein
# "apt-get remove nginx" genau der Griff, der den Bootserver mitnimmt --
# und auch ohne Boot gehoert ein Dienst, den andere benutzen koennen, nicht
# diesem Werkzeug. Entfernt wird der eigene vhost, nichts weiter.
#
# **Und aus demselben Grund wird nginx NEU GELADEN und nicht neu
# gestartet:** Ein restart reisst die Verbindungen aller anderen Seiten
# hinter demselben nginx ab. Dasselbe tut install.sh.
#
# **Das Dienstkonto bleibt, SOLANGE DER BESTAND BLEIBT.** Das ist keine
# Vorsicht, sondern eine Notwendigkeit: Die Dateien unter /var/lib gehoeren
# diesem Konto. Wer es entfernt und die Dateien liegen laesst, hat
# Dateien, deren Besitzer eine Zahl ohne Namen ist -- und nach der
# naechsten useradd-Vergabe gehoeren sie jemand anderem. Geht der Bestand
# mit weg, geht das Konto mit.
# ===========================================================================
set -euo pipefail

APP_DIR=/opt/marlei-tasks
DATA_DIR=/var/lib/marlei-tasks
ENV_DATEI=/etc/marlei-tasks.env
DIENST=marlei-tasks
EINHEIT=/etc/systemd/system/marlei-tasks.service
VHOST=/etc/nginx/sites-available/marlei-tasks
VHOST_AN=/etc/nginx/sites-enabled/marlei-tasks

# Das Wort, das beim Loeschen des Bestands getippt werden muss.
LOSUNG=Bestand

BESTAND=nein
for arg in "$@"; do
  case "$arg" in
    --bestand) BESTAND=ja ;;
    -h|--help)
      sed -n '2,32p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) printf 'Unbekannte Angabe: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

log()  { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[X]\033[0m %s\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "Bitte als root ausfuehren:  sudo $0"

# --------------------------------------------------------------------------
log "Was ist hier ueberhaupt da?"
# --------------------------------------------------------------------------
# ERST NACHSEHEN, DANN ANFASSEN -- und es hinschreiben. Ein Skript, das
# schweigend durchlaeuft, laesst einen im Zweifel, ob es etwas gefunden hat
# oder nur nichts gesagt.
groesse() { [[ -e "$1" ]] && du -sh "$1" 2>/dev/null | cut -f1 || echo "-"; }

EINHEIT_DA=nein; [[ -e "$EINHEIT" ]] && EINHEIT_DA=ja
VHOST_DA=nein;   [[ -e "$VHOST" || -L "$VHOST_AN" ]] && VHOST_DA=ja
APP_DA=nein;     [[ -d "$APP_DIR" ]] && APP_DA=ja
DATEN_DA=nein;   [[ -d "$DATA_DIR" ]] && DATEN_DA=ja
KONTO_DA=nein;   id "$DIENST" &>/dev/null && KONTO_DA=ja

printf '    Einheit       : %s\n' "$([[ $EINHEIT_DA == ja ]] && echo "$EINHEIT" || echo "nicht da")"
printf '    nginx-vhost   : %s\n' "$([[ $VHOST_DA == ja ]] && echo "$VHOST" || echo "nicht da")"
printf '    Anwendung     : %s\n' "$([[ $APP_DA == ja ]] && echo "$APP_DIR  ($(groesse "$APP_DIR"))" || echo "nicht da")"
printf '    Ablage        : %s\n' "$([[ -f $DATA_DIR/tasks.db ]] && echo "$DATA_DIR/tasks.db  ($(groesse "$DATA_DIR"))" || echo "nicht da")"
printf '    Dienstkonto   : %s\n' "$([[ $KONTO_DA == ja ]] && echo "$DIENST" || echo "nicht da")"

if [[ $EINHEIT_DA == nein && $VHOST_DA == nein && $APP_DA == nein \
      && $DATEN_DA == nein && $KONTO_DA == nein ]]; then
  echo
  echo "Hier ist nichts von MARLEI Tasks installiert. Nichts zu tun."
  exit 0
fi

# --------------------------------------------------------------------------
# Das Losungswort -- nur wenn der Bestand mit weg soll
# --------------------------------------------------------------------------
# **Ein Schalter sagt, DASS etwas geloescht wird; das Wort bestaetigt,
# dass man es gelesen hat.** Dieselbe Ueberlegung wie bei der
# Werkseinstellung in der Anwendung, wo der Projektname getippt werden muss.
#
# Ohne Terminal wird nicht gefragt, sondern abgebrochen: Ein Skript, das in
# einer Pipeline auf eine Eingabe wartet, haengt -- und eines, das ohne
# Antwort einfach loescht, ist schlimmer.
if [[ $BESTAND == ja && $DATEN_DA == ja ]]; then
  if [[ ! -t 0 ]]; then
    die "--bestand braucht eine Rueckfrage, und hier kann niemand antworten.
    In einer gewoehnlichen Sitzung erneut aufrufen."
  fi
  cat <<HINWEIS

  Mit --bestand wird auch das geloescht:
      $DATA_DIR
      $ENV_DATEI
    also die Ablage, die Einstellungen und der Ausgang.
    Ein Abbild holt man erneut, einen eingetragenen Gedanken nicht:
    Wer den Bestand noch braucht, bricht hier ab (Strg+C) und gibt ihn
    vorher unter Einrichtung aus.

HINWEIS
  read -r -p "  Zum Loeschen bitte »$LOSUNG« eingeben: " ANTWORT
  [[ "$ANTWORT" == "$LOSUNG" ]] \
    || die "Das Wort stimmt nicht -- es ist nichts geloescht worden."
fi

# --------------------------------------------------------------------------
log "Dienst anhalten und Einheit entfernen"
# --------------------------------------------------------------------------
if command -v systemctl >/dev/null; then
  systemctl disable --now "$DIENST" >/dev/null 2>&1 || true
fi
if [[ $EINHEIT_DA == ja ]]; then
  rm -f "$EINHEIT"
  command -v systemctl >/dev/null && systemctl daemon-reload || true
  echo "    weg."
else
  echo "    war nicht da."
fi

# --------------------------------------------------------------------------
log "nginx-vhost entfernen"
# --------------------------------------------------------------------------
if [[ $VHOST_DA == ja ]]; then
  rm -f "$VHOST_AN" "$VHOST"
  # NUR NEU LADEN, UND NUR WENN DIE KONFIGURATION HAELT: Ein reload mit
  # kaputter Konfiguration laesst nginx stehen, wie er ist -- ein restart
  # nicht, und dann stuende auf einer Maschine mit MARLEI Boot der
  # Bootserver still.
  if command -v nginx >/dev/null && nginx -t >/dev/null 2>&1; then
    systemctl reload nginx >/dev/null 2>&1 || true
    echo "    weg, nginx neu geladen (nicht neu gestartet)."
  else
    warn "Der vhost ist weg, aber 'nginx -t' meldet einen Fehler -- nginx
    wurde deshalb NICHT neu geladen. Was nicht stimmt, sagt:  nginx -t"
  fi
else
  echo "    war keiner da."
fi

# --------------------------------------------------------------------------
log "Anwendung entfernen"
# --------------------------------------------------------------------------
if [[ $APP_DA == ja ]]; then
  rm -rf "$APP_DIR"
  echo "    $APP_DIR -- weg (Anwendung, venv, VERSION)."
else
  echo "    war nicht da."
fi

# --------------------------------------------------------------------------
log "Der Bestand"
# --------------------------------------------------------------------------
BESTAND_WEG=nein
if [[ $BESTAND == ja && $DATEN_DA == ja ]]; then
  rm -rf "$DATA_DIR"
  rm -f "$ENV_DATEI"
  BESTAND_WEG=ja
  echo "    $DATA_DIR -- weg."
  echo "    $ENV_DATEI -- weg."
elif [[ $DATEN_DA == ja ]]; then
  echo "    BLEIBT LIEGEN: $DATA_DIR"
  echo "                   $ENV_DATEI"
  echo "    Darin die Ablage (tasks.db), die Einstellungen und der Ausgang."
  echo "    Eine erneute Installation nimmt alles wieder auf -- der Bestand"
  echo "    und die Einstellungen ueberleben."
else
  echo "    war nichts da."
fi

# --------------------------------------------------------------------------
log "Das Dienstkonto"
# --------------------------------------------------------------------------
# SOLANGE ETWAS LIEGT, MUSS SEIN BESITZER BENENNBAR BLEIBEN. Ein geloeschtes
# Konto laesst Dateien zurueck, deren Besitzer eine Zahl ohne Namen ist --
# und die naechste useradd-Vergabe macht daraus jemand anderen.
if [[ $KONTO_DA == ja ]]; then
  if [[ $BESTAND_WEG == ja ]]; then
    userdel "$DIENST" >/dev/null 2>&1 \
      && echo "    $DIENST -- weg (es gehoerte nichts mehr)." \
      || warn "userdel $DIENST ging nicht -- von Hand:  sudo userdel $DIENST"
  else
    echo "    BLEIBT: $DIENST -- ihm gehoeren die Dateien unter $DATA_DIR."
    echo "    Es geht mit, sobald der Bestand mitgeht (--bestand)."
  fi
else
  echo "    war keins da."
fi

cat <<INFO

===========================================================================
 Fertig.

 Weg sind: die Anwendung, die Einheit, der vhost$([[ $BESTAND_WEG == ja ]] && echo ", der Bestand, das Dienstkonto").
INFO

if [[ $BESTAND_WEG == nein && $DATEN_DA == ja ]]; then
  cat <<INFO
 Liegen bleibt: $DATA_DIR und $ENV_DATEI
 Loeschen mit:  sudo ./setup/linux/uninstall.sh --bestand
INFO
fi

cat <<INFO

 **nginx bleibt stehen** -- es koennte auf dieser Maschine noch jemand
 anderes brauchen. Auf einer mit MARLEI Boot waere ein
 'apt-get remove nginx' genau der Griff, der den Bootserver mitnimmt.

===========================================================================
INFO
