---
name: obsidian-research-notes
description: "Write source-grounded Markdown research notes into a confirmed Obsidian vault, checking wikilinks and attachments without changing vault settings."
license: MIT
---

# Obsidian research notes

Use when the user wants actual notes in Obsidian. Resolve the vault and destination
from an explicitly supplied path or established context. If neither is available,
prepare Markdown in the task workspace and request the missing destination.

- Read existing note conventions near the intended folder. Preserve the user's
  organization; do not impose a personal folder taxonomy on another vault.
- Read the paper or repository that supports the note. Link specific sources and
  distinguish author reports, reproduction results, and interpretations. Leave
  unknown metadata explicit rather than filling plausible titles or IDs.
- Use meaningful note names. Check for ambiguous existing basenames before adding
  `[[wikilinks]]`; use a folder-qualified target when needed.
- Keep diagrams and attachments in the chosen attachment directory. In Markdown
  table cells, write an aliased link as `[[folder/note\|label]]` so the table's
  columns remain intact.
- Check edited notes and their referenced assets. The read-only
  [link checker](scripts/check_links.py) detects missing and ambiguous targets:

  ```sh
  python scripts/check_links.py --vault ./notes
  ```

The helper checks targets, not whether a heading/block anchor exists or whether
a claim is correct. It skips fenced and inline code examples. It does not load
plugins, edit `.obsidian`, or rewrite links. Report its scope and any existing
errors separately from new errors. Deliver `.md` files; a Word document alone
does not fulfill an Obsidian request.
