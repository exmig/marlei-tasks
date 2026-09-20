# Sicherheitslücken melden

**Bitte nicht als Issue.** Ein offenes Issue ist ab der ersten Sekunde für
alle lesbar — auch für die, die den Fehler ausnutzen wollen, und zwar
bevor er behoben ist.

## Der Weg

**Am liebsten über GitHub:** *Security → Report a vulnerability* in diesem
Repository. Die Meldung ist dann nur für uns sichtbar, und die
Unterhaltung darüber bleibt privat, bis eine Lösung da ist.

**Oder per Mail an [kontakt@exmig.de](mailto:kontakt@exmig.de).** Auch das
genügt — schreib nur dazu, dass es um eine Sicherheitslücke geht.

## Was in die Meldung gehört

- Was passiert, und was stattdessen passieren sollte.
- **Wie man es auslöst.** Ohne diesen Teil lässt sich der Fehler nicht
  nachstellen und damit nicht beheben.
- Auf welchem System es läuft und seit welchem Stand.

*Zugangsdaten, Adressen aus deinem Netz, Namen deiner Rechner oder Inhalte
aus deinem Bestand brauchen wir nicht — bitte schwärze sie, bevor du etwas
schickst.*

## Was du erwarten kannst

Dieses Projekt wird von **einer Person** in ihrer Freizeit gepflegt. Es
gibt keine Bereitschaft und keine zugesagte Frist, und es wäre unredlich,
eine zu versprechen. Was zugesagt wird:

- **Eine Antwort, dass die Meldung angekommen ist.** Sie kann ein paar
  Tage dauern.
- **Eine ehrliche Einschätzung**, ob und wann es behoben wird — auch
  dann, wenn die Antwort *„auf absehbare Zeit nicht"* lautet.
- **Eine Nennung**, wenn du sie möchtest, sobald die Sache behoben ist.

## Was diese Anwendung von Haus aus nicht kann

Damit niemand eine Lücke meldet, die als solche gar nicht gemeint ist —
das steht so auch in der Dokumentation:

- **Die Weboberfläche hat ein Kennwort und sonst nichts.** Es gibt keine
  Benutzer, keine Rollen und keine Rechte: Wer angemeldet ist, darf alles,
  was sie kann — lesen, ändern, löschen. Ist bei der Installation kein
  Kennwort gesetzt worden, gibt es keine Anmeldung; die Oberfläche sagt
  das auf jeder Seite.
- **Die Oberfläche spricht http, nicht https.** Das Kennwort geht
  unverschlüsselt durchs Netz. Sie gehört deshalb in ein Netz, dem du
  vertraust, nicht ins offene Internet.
- **Wer auf der Maschine Administrator ist, kommt an Tasks vorbei.** Er
  kann das Kennwort neu setzen und die Ablage direkt lesen. Das Kennwort
  hält das Netz draußen, nicht die Maschine.
- **Der Bestand liegt unverschlüsselt.** Eine SQLite-Datei auf der Platte
  des Servers; wer auf der Maschine Zugriff hat, liest sie. Das ist keine
  Lücke, sondern die Bauart.
- **Es gibt keine Mandanten.** Mehrere Projekte sind eine Ordnung, keine
  Trennung: Wer die Oberfläche bedienen darf, sieht alle.

Etwas davon zu ändern ist eine Frage der Weiterentwicklung, keine
Sicherheitsmeldung — dafür ist ein Issue der richtige Ort.

## Welche Stände gepflegt werden

Der jeweils **aktuelle Stand auf `main`**. Ältere Fassungen bekommen keine
Nachbesserungen; wer eine Lücke geschlossen haben will, aktualisiert.
