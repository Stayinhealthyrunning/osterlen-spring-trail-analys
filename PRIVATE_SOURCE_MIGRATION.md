# Privat källhämtning

ÖST:s frysta Sportstiming-databas och kuraterade analysdatabas lagras i
`Stayinhealthyrunning/loppanalys-private-data`. De återställs till en tillfällig
Actions-arbetsyta och verifieras byte för byte innan tester eller export körs.

Produktionskrav:

- `LOPPANALYS_SOURCE_APP_ID`
- `LOPPANALYS_SOURCE_APP_PRIVATE_KEY`

GitHub-appen ska endast ha `Contents: read` på det privata källrepot. Saknas
credentials, manifest, fil eller korrekt SHA-256 stoppas jobbet. Den privata
checkouten tas bort innan Pages- eller andra publika artefakter skapas.

Lokalt återställningsprov:

```text
python tools/restore_private_sources.py --private-root ../loppanalys-private-data
```

Workflowet `freeze-sportstiming-results.yml` får inte återaktiveras för publik
commit. En framtida källuppdatering ska använda separat skrivbehörig GitHub App
och skapa en granskningsbar ändring endast i det privata arkivet.
