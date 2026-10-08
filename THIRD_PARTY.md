# Third-party components and platform dependencies

Deploy Relay Agent V1 does not vendor or bundle third-party source-code
libraries into its integration source tree.

The integration runs inside Home Assistant and uses platform/runtime
components that are provided by the Home Assistant environment.

## Runtime platform / dependencies

| Component | Role | Distribution in DRA |
| --- | --- | --- |
| Home Assistant Core | host platform and integration APIs | not bundled by DRA |
| aiohttp | HTTP client/runtime component provided by the HA environment | not bundled by DRA |
| probatio | schema/validation helper available in the HA runtime | not bundled by DRA |

These components remain subject to their respective upstream licenses.

DRA's `manifest.json` currently declares:

```json
"requirements": []
```

Therefore DRA V1 does not request installation of an additional Python
package for the integration itself.

## Development and CI dependencies

The private development/test environment additionally uses tools such as:

- pytest;
- jsonschema;
- aiohttp.

These are development/test dependencies and are not copied into the public
DRA integration package.

## Frontend

The DRA frontend does not bundle a third-party JavaScript framework or load a
runtime library from a public CDN. Its JavaScript modules are part of the DRA
source itself.

## Branding and project artwork

Official DRA logos, icons, roadmap artwork and the visual identity are
project-owned reserved materials and are governed by `BRANDING.md`, not by
GPL-3.0-only.

## External services and badges

References to Home Assistant, HACS, GitHub or externally rendered repository
badges identify services/platforms and do not transfer ownership of their
names, logos or trademarks to the DRA project.

## Audit status

Repository audit performed for the DRA V1 release preparation on
**2026-10-07**.

No vendored third-party code, third-party font package, external JavaScript
framework, copied icon library or separately licensed image package was
identified in the DRA V1 release candidate.
