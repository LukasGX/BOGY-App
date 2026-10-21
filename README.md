# BOGY App

Eine mobile Web-App für Schüler und Lehrkräfte des Bodensee-Gymnasiums Lindau (BOGY).

## Features

- Nachhilfevermittlung
- Automatisches Senden von WLAN-Voucher-Codes von Lehrern an Schüler
- Interaktive Elternbriefe
- Passwort-Manager für Schul-Apps
- Push-Benachrichtigungen (Web Push)
- Admin-Dashboard für Klassen, Benutzer, WLAN-Codes, Nachhilfe und Elternbriefe

## Rollen

| Rolle | ID | Berechtigung |
|---|---|---|
| Schüler | 1 | eigene Daten, WLAN-Codes, Nachhilfe, Elternbriefe |
| Lehrer | 2 | wie Schüler |
| Elternteil | 3 | wie Schüler |
| Verwaltung | 4 | Vollzugriff auf das Admin-Dashboard |

Rollen werden serverseitig geprüft (`api/v1/deps.py`, `require_role(...)`). Endpunkte,
die Nutzer-, Klassen- oder Elternbrief-Daten verwalten, sind ausschließlich der
Verwaltung zugänglich.

## Konfiguration (`.env`)

| Variable | Bedeutung |
|---|---|
| `SESSION_SECRET_KEY` | Secret zum Signieren der Session-Cookies (**Pflicht**) |
| `ADMIN_PASSWORD` | Passwort für den Admin-Account `admin`. Wird beim ersten Start genutzt. Ohne diese Variable wird ein zufälliges Passwort erzeugt und beim Start ausgegeben. |
| `DB_PATH` | Pfad zur SQLite-Datenbank (Standard: `data.db`) |
| `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` / `VAPID_EMAIL` | Push-Benachrichtigungen |
| `UNTIS_USERNAME` / `UNTIS_PASSWORD` | Zugang zu WebUntis (Import von Klassen/Benutzern) |
| `UNTIS_DEFAULT_PASSWORD` | Optionales gemeinsames Startpasswort für importierte Benutzer. Ohne diese Variable erhält jeder importierte Nutzer ein eigenes Zufallspasswort, das nach dem Import im Dashboard angezeigt und heruntergeladen werden kann. |
| `CORS_ORIGINS` | Optionale, kommagetrennte Liste erlaubter Origins. Standard: keine (die App läuft same-origin). |
| `ENV` | `production` aktiviert HTTPS-only-Session-Cookies |

Beispiel:

```
SESSION_SECRET_KEY=<zufaelliger-langer-string>
ADMIN_PASSWORD=<passwort-fuer-den-admin>
VAPID_PUBLIC_KEY=...
VAPID_PRIVATE_KEY=...
VAPID_EMAIL=mail@bogy.de
UNTIS_USERNAME=...
UNTIS_PASSWORD=...
```

## Starten

Lokal:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Docker:

```bash
docker compose up -d
```

Das Projektverzeichnis wird in den Container gemountet, die SQLite-Datei
(`data.db`) liegt damit persistent auf dem Host. Über `DB_PATH` kann ein
anderer Pfad gesetzt werden (z. B. `/app/data/data.db` in das Volume `data`).

## Hinweise zum Zeitverhalten

WLAN-Codes haben ein Ablaufdatum, das als lokale Zeit gespeichert wird. Der
Vergleich mit „jetzt“ passiert serverseitig in Python (`services/wlan_service.py`),
damit Codes in der Sommerzeit nicht um zwei Stunden zu spät ablaufen.

## Geplante Features
