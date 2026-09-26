# Screenshot inventory

Screenshots in this directory must be captured from the running CropPilot
application, with no DOM injection, seeded fixtures, secrets or browser
chrome. Provider-backed values may legitimately be unavailable. Inspect
each image before publication.

| File | Route | Viewport | Language | Notes |
|---|---|---:|---|---|
| `desktop/03-markets.png` | `/markets` | 1440×900 | English | Genuine AGMARKNET latest-reported rows with date/source. |
| `desktop/05-disease-detection.png` | `/disease-detection` | 1440×900 | English | Idle state; no fake diagnosis. |
| `desktop/06-schemes.png` | `/schemes` | 1440×900 | English | Retrieved scheme cards. |
| `desktop/08-maps.png` | `/maps?lat=17.05&lng=79.27` | 1440×900 | English | Real location context and explicit unavailable sections. |
| `desktop/09-ai-assistant.png` | `/ai-assistant` | 1440×900 | English | Empty state; no fake conversation or fabricated citation. |
| `desktop/10-login.png` | `/auth/login` | 1440×900 | English | Plain login form. |
| `mobile/02-markets.png` | `/markets` | 390×844 | English | Same data as desktop markets. |
| `mobile/04-disease-detection.png` | `/disease-detection` | 390×844 | English | Idle state. |
| `mobile/05-maps.png` | `/maps?lat=17.05&lng=79.27` | 390×844 | English | Bottom-sheet layout. |
| `mobile/06-ai-assistant.png` | `/ai-assistant` | 390×844 | English | Empty state. |
| `localized/hi-markets.png` | `/markets` | 1440×900 | Hindi | Labels translated; source data loaded. |

The old `docs/assets/screenshot-*.png` set contains demo/sample content and
is not reused as release evidence. Urdu is not in the currently shipped UI
catalog set, so no Urdu RTL screenshot is claimed. Mobile screenshots should
be added only after fresh 390×844 captures pass visual inspection.
