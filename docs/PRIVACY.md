# Deploy Relay Agent — Datenschutz & sensible Daten

## Grundsatz

DRA soll nur die Daten verarbeiten, die für Deployment, Recovery und Diagnose technisch notwendig sind.

## GitHub-Tokens

Projekt-Tokens sollen möglichst nur folgende Rechte besitzen:

```text
Metadata: Read
Contents: Read
```

Der optionale Diagnose-Git-Export verwendet einen getrennten, gezielt berechtigten Schreibtoken.

## Diagnose

Secrets werden vor Persistenz und Export redigiert.

Dazu gehören insbesondere:

- GitHub-Tokens;
- Authorization-Header;
- bekannte Passwort-/API-Key-Muster;
- private Schlüssel.

## V2

Für das geplante V2-Diagnosemodell sind ausdrücklich **keine** dauerhaften Clientprofile vorgesehen.

Nicht als Diagnosemerkmal benötigt:

- Client-IP;
- MAC-Adresse;
- IMEI;
- Standort;
- VPN-Endpunkt;
- Browser-Fingerprinting.

Reconnect soll über die serverseitige Operation erfolgen, nicht über ein dauerhaftes Geräteprofil.
