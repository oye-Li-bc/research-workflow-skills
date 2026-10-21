---
name: paper-beamer
description: "Turn an academic paper into editable Beamer source with traceable claims, usable figures, and checked compilation when a compiler is available."
license: MIT
---

# Paper to Beamer

Use when the requested deliverable is a Beamer presentation. Establish audience,
talk duration, output language, and any supplied theme from the request. For a
general paper explanation, answer inline instead of creating a deck.

1. Obtain the actual paper. Prefer supplied TeX when useful; for arXiv sources,
   use an available trusted fetcher or retrieve the source explicitly. Distinguish
   PDF-only content, missing figures, and unverified metadata.
2. Read the overview, method, experiments, and limitations. Build a claim ledger
   using the [outline](references/outline.md). Map each reported result to a page,
   table, figure, or source section. Preserve the experimental scope.
3. Fit the outline to the talk. Typical sections are motivation, problem setup,
   method/data flow, main results, limitations, and discussion. Do not force an
   eleven-section structure or speculative historical claims onto every paper.
4. Create a dedicated editable project. Use the user's supplied theme if its
   files and rights are available; otherwise start from standard Beamer. Keep
   figure files and supporting TeX within the project, with relative paths.
5. Compile using the available compiler. Inspect missing references/assets,
   undefined commands, and overfull boxes. View the rendered slides when a viewer
   is available and repair dense or clipped frames. Without a compiler, deliver
   source and state that compilation and layout remain unverified.

Do not execute source-bundled shell programs or enable shell escape without a
specific need. Do not fabricate a compile result, acceptance category, venue,
author, result, or unavailable figure. Record figure placeholders for follow-up.

Deliver the project location, PDF if compiled, verification performed, and any
remaining limitations. A successful compiler exit alone does not verify visual
layout or scientific accuracy.
