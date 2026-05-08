# Workflow Patterns

Extraherade mönster från arkiverade Claude Code-sessioner. Uppdateras allteftersom fler sessioner städas och sammanfattas.

## Sessionsmarkörer

Dessa markörer dyker upp i råa transkript (efter `.docx → .txt`-konvertering) och är användbara när parsern för JSONL skrivs:

| Markör | Betydelse |
|--------|-----------|
| `Ran` följt av en rad | Claude anropade ett verktyg (typiskt Bash) |
| `Read`, `Read N files` | Filläsning via Read-verktyget |
| `Searched code`, `Searched codebase` | Grep/Glob-verktyg |
| `updated todos` | TodoWrite-verktyg |
| Kodblock med språktagg (```python, ```bash) | Bevaras ordagrant i `turns[].text` |

## Språkmönster

- Inledande svenska frågor, senare engelska svar — vanligt. Sätt `language: "mixed"`.
- Rena svenska sessioner — typiskt korta, uppgiftsorienterade (commit, navigering).
- Rena engelska sessioner — typiskt nya repo-sättningar eller interaktioner med externa API:er.

## Anti-mönster som ska filtreras bort under cleaning

- Upprepade tomma action-markörer utan följande innehåll.
- Renderingsartefakter från `.docx → .txt` (dubbla mellanslag, lösa bindestreck som listpunkter).
- Miljöspecifika tokens eller API-nycklar som läckt in i transkriptet.
- Autogenererade loggrader utan kontextvärde (t.ex. fullständiga `git log`-dumpar om de inte refereras senare i sessionen).

## Tagg-vokabulär (levande)

Taggar tilldelas per session vid strukturering. Existerande observerade domäner från sessionsfilnamn:

`dashboard`, `rag`, `docker`, `yolo`, `eo-satellites`, `imint`, `space-cluster`, `pax`, `lime`, `biofinans`, `ecosystem`, `leo`, `github`, `commit`, `training`, `h100`, `fetch`

Lägg till nya taggar här när de används för första gången, för att hålla vokabulären konsistent.

## Återkommande agentiska mönster (att identifiera över tid)

När fler sessioner distilleras, dokumentera här:
- Vanliga felaktiga första-försök och hur de korrigerades
- Gemensamma verktygsval för liknande problem
- "Sessions-startare" — öppningsmönster som konsekvent leder till produktivt arbete
- Cross-repo-beroenden (när en uppgift i repo A kräver kontext från repo B)
