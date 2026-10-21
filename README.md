# BOGY App

Eine mobile Web-App für Schüler und Lehrkräfte des Bodensee-Gymnasiums Lindau (BOGY).

## Features

- Nachhilfevermittlung
- Automatisches Senden von WLAN-Voucher-Codes von Lehrern an Schüler
- Interaktive Elternbriefe
- Passwort-Manager für Schul-Apps

## Konfiguration (`.env`)

| Variable | Bedeutung |
|---|---|
| `SESSION_SECRET_KEY` | Secret zum Signieren der Session-Cookies (**Pflicht**) |
| `ADMIN_PASSWORD` | Passwort für den Admin-Account `admin`. Wird beim ersten Start genutzt. Ohne diese Variable wird ein zufälliges Passwort erzeugt und beim Start ausgegeben. |
| `DB_PATH` | Pfad zur SQLite-Datenbank (Standard: `data.db`) |
| `CORS_ORIGINS` | Optionale, kommagetrennte Liste erlaubter Origins. Standard: keine (die App läuft same-origin). |
| `ENV` | `production` aktiviert HTTPS-only-Session-Cookies |

## Geplante Features
