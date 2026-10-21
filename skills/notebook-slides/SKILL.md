---
name: notebook-slides
description: "Set Jupyter notebook slideshow boundaries while preserving code, outputs, kernel metadata, and existing manual slide choices."
license: MIT
---

# Notebook slide boundaries

Distinguish RISE/Reveal presentation boundaries from the notebook UI and execution
environment. First read the notebook's existing `metadata.slideshow.slide_type`.

Use [mark_slides.py](scripts/mark_slides.py) to create a separate notebook:

```sh
python scripts/mark_slides.py lesson.ipynb lesson.slides.ipynb --mode headings
```

`headings` marks level-one markdown headings as slides and level-two headings as
subslides. `cells` marks nonempty cells as slides. Existing manual choices win;
other cell types receive `-` (stay in the current slide). The input is never
overwritten. Review boundaries because a heading-based rule cannot infer every
teaching transition.

Inspect representative slides in the user's presentation tool when available.
Report separately whether metadata was changed, a presenter opened it, or the
visual result was verified. Do not claim a working RISE installation from a valid
notebook file alone. Leave code and outputs untouched and do not restart a kernel
as part of presentation formatting.
