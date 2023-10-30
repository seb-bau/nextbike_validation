# Nextbike - WOWIPORT / OPENWOWI Validator
## Allgemein
Dies ist ein Flask Webservice, der prüft, ob eine angegebene Vertragsnummer in Wowiport vorhanden ist.  
In unserem Fall wurde der Fahrrad-Verleihdienst Nextbike angebunden. Der Validator wird benötigt, wenn z.B.  
die eigenen Kunden des Unternehmens bestimmte Angebote bei Nextbike in Anspruch nehmen dürfen und sich hierfür  
mit der Mietvertragsnummer "ausweisen" müssen.  

Grundsätzlich ist es jedoch ein generischer Connector, der sich mit beliebigen Diensten nutzen lässt. Man kann ihn  
auch als Vorlage für eigene Zwecke nutzen.

## Aufruf

```
https://<host>/nextbike/v1/validate?contract=<vertragsnummer>
# Beispiel
https://api.example.org/nextbike/v1/validate?contract=009.09.09
```

## Format
In den Einstellungen kann das Format des Mietvertrags eingestellt werden:
````
# Format of contract num
contract_mask="xxxxx.xxx.xxx.xx"
````

Die Benutzer haben daher einen gewissen Spielraum bei der Eingabe des Nummer:  
* Führende Nullen (nur am Anfang) können weggelassen werden
* Trennzeichen können weggelassen werden

Beispiel: 0009.08.7 = 9087 = 9.08.7

## Installation
Es handelt sich beim Validator um eine Flask-Anwendung. Getestet wurde per WSGI mit Apache2
Grundsätzlich:
* Projekt klonen
* Voraussetzungen per pip und requirements.txt installieren
* Apache2 mit WSGI konfigurieren (bei Bedarf app.wsgi.example nutzen)
* .env.example zu .env kopieren und Variablen füllen (u.A. OPENWOWI-Zugangsdaten und API-Key)