# ads.txt-Editor: Einrichtung und kontrollierte Umschaltung

Stand: 29.10.2026. Diese Anleitung beschreibt den vorgesehenen Betrieb. Eine geprüfte Implementierung oder ein erfolgreicher Build beweist noch keine Live-Umschaltung. Dafür sind authentifizierter Serverzugang und die unten beschriebenen Rückleseprüfungen erforderlich.

## Datenquelle und Zuständigkeit

Die bisher öffentlich ausgelieferte Datei liegt im bestehenden Container `nginx-proxy` unter `/usr/share/nginx/html/ads.txt`. Sie ist nicht aus einem Hostverzeichnis eingebunden. `deploy/ads.txt` ist eine historische Referenz und keine Quelle für die Migration. Auch der alte Backend-Handler `/ads.txt`, der Inhalte von Vermarktern zusammenstellt, ist keine bytegleiche Datenquelle.

Der neue Editor unter `/ads-txt-editor` verwaltet ausschließlich ads.txt. Seine eigene Passwortanmeldung aktiviert keine Website-Administratoren und verwendet weder deren Konten noch JWT-Schlüssel. Die bestehenden Mongo-Daten, Container, Proxy-Netzwerke und deaktivierten Backupdienste bleiben erhalten. Revisionen sind eine Funktion des Editors, kein Schutz gegen Verlust des Hosts oder Datenträgers.

Der am 29.10.2026 um 18:08 UTC erfasste öffentliche Ausgangsstand hatte 44.584 Bytes, 994 Zeilen und SHA-256 `d616b1a85a6cf60ed623bb2994d31d3c91b448e3bf22182abf4494cee912ae44`. Vor der tatsächlichen Umschaltung erneut erfassen; dieser historische Wert ersetzt keinen aktuellen Abgleich.

## Konfiguration und persistenter Speicher

Im vorhandenen Coolify-Backend werden diese Werte verwendet:

| Einstellung | Wert im Container |
| --- | --- |
| `ADS_TXT_EDITOR_DB_PATH` | `/app/ads_txt/editor.sqlite3` |
| `ADS_TXT_EDITOR_PASSWORD_HASH_FILE` | `/run/secrets/ads_txt_editor_password_hash` |
| `ADS_TXT_EDITOR_ORIGIN` | `https://transfernews.de` |

Einbinden:

```text
/opt/transfernews-runtime/ads_txt:/app/ads_txt
/opt/transfernews-runtime/secrets/ads_txt_editor_password_hash:/run/secrets/ads_txt_editor_password_hash:ro
```

Das gesamte SQLite-Verzeichnis muss persistent sein, damit Journal-/WAL-Dateien dieselbe Lebensdauer und denselben Dateisystemkontext wie die Datenbank haben. Keine einzelne SQLite-Datei über mehrere voneinander unabhängige Hosts teilen. Das Verzeichnis gehört dem tatsächlich verwendeten Backend-UID und ist nur für diesen zugänglich; beim derzeitigen Root-Container entspricht das Host-root. Verzeichnis-Modus700, Datenbank und Geheimnisdatei600. Die bereits vorhandenen JWT-/OpenAI-Dateien werden nicht geändert.

Die Passwort-Hash-Datei vor einem Deployment mit diesem Dateimount anlegen; andernfalls kann Docker aus einem fehlenden Dateipfad ein Verzeichnis machen. Mit dem geprüften Modul in einer vorbereiteten Laufzeit erzeugen:

```text
python ads_txt_editor.py hash-password --output <geschützte-Hashdatei>
```

Das Passwort wird interaktiv mit `getpass` eingegeben, niemals als Kommandozeilenargument, Git-Datei oder Protokolltext. Nur die erzeugte Hash-Datei an den genannten Hostpfad installieren. Die CLI ohne `--output` schreibt den Hash nach stdout; für den Betrieb die Dateiausgabe verwenden. Keine normale `server.py`-Instanz zum Einrichten starten. Eine fehlende oder ungültige Hash-Konfiguration darf keinen Standardzugang öffnen.

Die editorbezogene `www`-Route führt zur kanonischen HTTPS-Origin ohne `www`. Sitzungen sind acht Stunden gültig, hostgebunden und mit `Secure`/`HttpOnly` geschützt. Schreibaufrufe benötigen zusätzlich CSRF-Nachweis und die exakt erlaubte Origin. Geheimnisse, Sitzungs-Cookies und CSRF-Werte gehören nicht in Prüfberichte.

Beim Wechsel zwischen normalen Seiten und Editor wird ein neues Dokument geladen, damit die Editor-CSP gilt und vorher geladene Werbeskripte nicht in dieses Dokument übernommen werden. Die gemeinsame Origin bleibt dennoch eine Vertrauensgrenze: JavaScript in einem anderen gleichzeitig geöffneten `transfernews.de`-Tab kann grundsätzlich dieselbe API mit der dort gültigen Sitzung ansprechen. Eine vollständige Trennung von Drittanbieterskripten erfordert einen eigenen Editor-Origin; Pfadtrennung und CSRF allein leisten das nicht.

Die Login-Begrenzung verwendet die vom Server ermittelte Clientadresse. Der Backend-Docker-CMD setzt seit Commit `c889a89` ausdrücklich `--no-proxy-headers`, damit ungeprüfte Forwarding-Header diese Adresse nicht überschreiben. Vor Betrieb auch die wirksame Startkonfiguration auf abweichende Overrides prüfen. Ohne Proxyheader-Auswertung teilen Anfragen über denselben Reverse Proxy dessen Loginlimit; das ist eine bewusste Verfügbarkeitsgrenze, kein Authentifizierungs-Bypass.

Die Editor-API hat den Präfix `/api/ads-txt-editor`:

| Aufruf | Vertrag |
| --- | --- |
| `GET /session` | Anmeldestatus, CSRF-Token und Ablaufzeit; legt auch vor der Anmeldung eine geschützte Vorsession an |
| `POST /login` | `{password}` mit Origin und CSRF-Header |
| `POST /logout` | `{}`; widerruft die Sitzung |
| `GET /document` | Aktuelle Revision mit Inhalt, SHA-256, Bytezahl und Erstellzeit |
| `GET /history` | Revisionsmetadaten und `next_before` für weitere Seiten |
| `GET /revisions/{id}` | Inhalt einer bestimmten Revision |
| `POST /preview` | `{text, expected_revision}`; gibt Vorschau, erkannte Dubletten und Ergänzungszahlen zurück |
| `POST /append` | Dieselben Felder; schreibt nur gegen die erwartete aktuelle Revision |
| `POST /rollback` | `{target_revision, expected_revision}`; stellt Inhalt durch eine neue Revision wieder her |

Alle POSTs verlangen `Origin: https://transfernews.de` und `X-CSRF-Token`. Sitzung/Anmeldung sind die ausdrücklich vorgesehenen Zugangswege; Dokument und Historie benötigen eine angemeldete Sitzung. Die öffentliche Ausgabe liegt getrennt unter `GET`/`HEAD /api/ads-txt/public`. Erwartete Fehler sind401 bei fehlender Anmeldung,403 bei ungültiger Origin/CSRF,409 bei Revisionskonflikt,422 bei ungültigen Zeilen,413 bei Größenüberschreitung,429 bei Zugriffslimit und503 bei fehlender Initialisierung/Konfiguration. Ein Fehler darf nicht als gespeicherte Änderung dargestellt werden.

Die Vorschau überspringt vorhandene Datensätze, erhält bestehende Bytes und vereinheitlicht ausschließlich die Zeilenenden neuer Ergänzungen auf den vorhandenen Stil. Kommentare und Leerzeilen bleiben Ergänzungen, auch wenn sämtliche Verkäuferdatensätze bereits vorkommen. Unterstützt werden außerdem `CONTACT`, `SUBDOMAIN`, `INVENTORYPARTNERDOMAIN`, `OWNERDOMAIN` und `MANAGERDOMAIN`. Widersprüchliche neue Eigentümer-/Managerangaben werden abgewiesen. Vor dem Speichern daher immer die tatsächliche Ergänzung und ihre Zähler prüfen. Der Verlauf wird in Seiten geladen; ältere Revisionen bleiben über „Ältere Versionen laden“ erreichbar.

## Ausgangsstand übernehmen, öffentliche Route zuletzt ändern

1. Den tatsächlichen bestehenden Coolify-Stack, Backend-Container, Image-Revision, Mongo-Mount und Proxy-Container feststellen. Kein zweites Compose-Projekt starten. Für diese Änderung einen rootgeschützten Arbeitsordner mit UTC-Zeit anlegen und die aktuelle Proxykonfiguration als Rückweg behalten. Keine Backup-Timer aktivieren.
2. `https://transfernews.de/ads.txt` als unveränderte Bytes abrufen, ohne Texteditor, Zeilenumbruchkonvertierung oder HTML-Decodierung. Parallel die vorhandene Datei aus `nginx-proxy:/usr/share/nginx/html/ads.txt` lesen. HTTP200, Bytezahl und SHA-256 beider Kopien müssen übereinstimmen. Bei Abweichung erst die tatsächlich ausgelieferte Quelle klären.
3. Den identischen Inhalt als eingeschränkt lesbare Seeddatei in das neue persistente Verzeichnis übertragen. Baseline und Original-Proxydatei behalten. Niemals eine Vermarkter-Neuabfrage oder ein Repository-Sample als Ersatz einsetzen.
4. Die geprüfte Anwendung über die vorhandene Coolify-Anwendung deployen. Die externe exakte `/ads.txt`-Location bleibt währenddessen unverändert statisch. Alle App-Container müssen die erwartete Revision verwenden und bereit sein. Fehlende Editorinitialisierung darf keine leere öffentliche ads.txt mit HTTP200 erzeugen.
5. Im bereits bestehenden Backend-Container ausschließlich die Seed-CLI ausführen; sie importiert keinen Server und startet keinen Scheduler:

   ```text
   python /app/ads_txt_editor.py seed --baseline /app/ads_txt/seed-baseline.txt --expected-sha256 <aktuell-verifizierter-SHA256> --db /app/ads_txt/editor.sqlite3
   ```

   Nur eine leere Datenbank darf initialisiert werden. Existierende Revisionen sind ein Abbruchgrund, keine Einladung zum Überschreiben oder Löschen. Nach einem unterbrochenen Versuch zunächst den vorhandenen Zustand lesen.
6. Die neue öffentliche API `/api/ads-txt/public` abrufen. Sie muss exakt dieselben Bytes wie die aktuelle statische `/ads.txt` liefern, mit HTTP200 und `text/plain`. Uninitialisiert oder bei nicht lesbarem Speicher muss sie fehlschlagen statt auf einen Generator oder eine leere Datei zurückzufallen. Unmittelbar vor Umschaltung den alten öffentlichen Inhalt nochmals gegen die Baseline prüfen.
7. Editoranmeldung, Nur-Lese-Anzeige und Revision prüfen. Ohne gültige Sitzung dürfen nur die ausdrücklich öffentlichen Ressourcen erreichbar sein. Die Website-Admin-Anmeldung bleibt deaktiviert. Erst nach diesen Prüfungen die einzelne externe `/ads.txt`-Location umstellen.

## Proxykonfiguration und bestehende Zugriffssperre

Die aktive externe Konfiguration liegt unter `/opt/nginx-proxy/nginx.conf`. Vor Änderung den tatsächlich geladenen Volltext und die Container-Mounts lesen. Die vorhandene Sperre für `/api/auth/` muss erhalten bleiben. Sowohl `/api/ads-txt-editor/` als auch die öffentliche `/api/ads-txt/public` sind andere Pfadpräfixe; sie benötigen keinen Zugriff auf `/api/auth/`. Breitere aktive Regex-/IP-Regeln trotzdem anhand der echten Konfiguration prüfen.

Bei bestehendem Upstream-Namen `backend` ist die eng begrenzte Zielkonfiguration:

```nginx
location = /ads.txt {
    proxy_pass http://backend/api/ads-txt/public;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Connection "";
    proxy_cache off;
    proxy_hide_header Cache-Control;
    add_header Cache-Control "no-store" always;
}
```

Den vorhandenen dynamisch auflösenden Docker-Upstream weiterverwenden; keinen zweiten Upstream oder Proxy anlegen. Der interne Frontend-Proxy muss ebenfalls ausdrücklich `/api/ads-txt/public` verwenden. Editor-HTML und geschützte API-Antworten dürfen nicht gecacht werden; Editor-HTML erhält `noindex` und eine restriktive CSP ohne Werbe-/CMP-Skripte. Die öffentliche Datei enthält ausschließlich den freigegebenen ads.txt-Inhalt, keine Sessiondaten.

Den vollständigen Kandidaten zuerst als separate Datei im vorhandenen Proxy mit `nginx -t -c <Kandidatenpfad>` prüfen. Ein einzelner read-only Dateimount von nginx.conf kann nach atomarem Umbenennen der Hostdatei weiter am alten Inode hängen. Deshalb nach erfolgreicher Kandidatenprüfung den Inhalt der bestehenden Hostdatei unter Erhalt von Inode, Besitzer und Rechten ersetzen; anschließend den im Container sichtbaren Hash mit dem Kandidaten vergleichen. Nochmals `docker exec nginx-proxy nginx -t`, dann ausschließlich `docker exec nginx-proxy nginx -s reload`. Nicht den Proxy neu erstellen oder den Host neu starten. Bei fehlgeschlagener Prüfung Originalinhalt wiederherstellen und nicht reloaden.

## Eng begrenzter Funktionsnachweis

Nach der Umschaltung die Ergebnisse getrennt dokumentieren:

- `/ads.txt` und `/api/ads-txt/public`: HTTP200, `text/plain`, gleiche Bytezahl und SHA-256 wie die aktuelle Baseline; auch den vorgesehenen `www`-Weiterleitungsweg prüfen.
- `/ads-txt-editor`: sichtbare Passwortanmeldung über HTTPS, kanonische Origin, keine Werbeskripte, keine Zugangsdaten im HTML. Ungültiges Passwort öffnet keine Sitzung; gültige Anmeldung liefert die bestehenden Inhalte und Revisionen. Passwortschutz und Login-Begrenzung lokal testen, nicht mit einer Produktions-Bruteforceprobe.
- Geschützte API ohne Sitzung abgelehnt; schreibender Aufruf ohne CSRF oder mit fremder Origin abgelehnt. Eine alte `expected_revision` muss409 liefern und darf keine Revision erzeugen.
- Einmal ausschließlich einen eindeutig markierten Kommentar ergänzen, beispielsweise `# transfernews ads.txt editor verification <UTC-Zeit>`. Keine erfundene Verkäuferzeile hinzufügen. Vorschau prüfen, dann mit aktueller Revision speichern. Der öffentliche Inhalt muss aus dem unveränderten Ausgangsinhalt plus der dokumentierten Trennzeile und exakt diesem Kommentar bestehen.
- Über die Editor-Rücknahme die Ausgangsrevision wiederherstellen. Die Rücknahme erzeugt eine neue Historienrevision. Der anschließend öffentlich abgerufene Inhalt muss **bytegenau** wieder der Baseline entsprechen. Bei zwischenzeitlicher Fremdänderung409 respektieren und zuerst neu lesen; keine erzwungene Rücknahme.
- Logout widerruft die Sitzung; ein weiterer geschützter Zugriff mit derselben Sitzung wird abgelehnt. Keine Cookies/Passwörter im Beleg speichern.
- Homepage, `/api/ready`, tatsächliches Artikel-HTML, Sitemap, vorhandene Werbeplätze und Coolify-HTTPS prüfen. Den bereits bekannten Publikationsstopp getrennt bewerten; eine funktionierende ads.txt-Verwaltung ist kein Beleg für die Reparatur der Nachrichtenpipeline.

Die Liveprüfung erst als erfolgreich markieren, wenn sowohl Ergänzung als auch öffentliche exakte Rücknahme beobachtet wurden. Persistenz zusätzlich durch den festgestellten Hostmount und einen kontrollierten späteren App-Containerwechsel belegen; lokale SQLite-Tests allein beweisen das nicht.

## Rückweg bei fehlgeschlagenem Cutover

Die alte Datei im Proxy bleibt während der gesamten Migration unangetastet. Vor Freigabe regulärer Editoränderungen kann die exakte frühere Proxykonfiguration zurückgeschrieben, getestet und per Reload aktiviert werden. Danach öffentliche Bytes erneut mit der Seed-Baseline vergleichen. Weder SQLite noch dessen Revisionen löschen; sie bleiben zur Diagnose erhalten. Die gesonderte neue Passwortanmeldung kann deaktiviert werden, ohne Website-Admins zu aktivieren oder andere Schlüssel zu entfernen.

Nach späteren echten Editoränderungen ist die alte statische Datei nicht mehr aktuell. Für einen späteren Infrastruktur-Rollback zuerst die jüngste gültige freigegebene Revision mit Bytezahl und Hash aus dem Editor lesen und als statische Datei bereitstellen; sonst würden neue Verkäuferfreigaben verschwinden. Eine gewünschte inhaltliche Rücknahme erfolgt über eine neue Editorrevision mit Konfliktprüfung. Nie eine aktive SQLite-Datenbank durch Kopieren einzelner DB-/WAL-Dateien zurücksetzen.
