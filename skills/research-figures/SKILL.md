---
name: research-figures
description: "Produce scientific or study figures from supplied measurements, with source labels, suitable fonts, and inspected exported layout."
license: MIT
---

# Research figures

Use when the output should be a chart or exported research figure. Establish the
data, units, comparison, and intended medium before choosing a plotting style.

- Read supplied data and distinguish measured, reported, derived, and missing
  values. Do not invent a missing baseline to complete a comparison.
- Use standard plotting libraries for scientific figures. Check installed
  dependencies and available fonts before proposing installation.
- For Chinese labels, select an available CJK font and inspect missing-glyph
  warnings. Replace decorative symbols if the chosen font cannot render them.
- Include axis units, legend meanings, uncertainty when supplied, and a short
  source label. Preserve the experimental scope inside a figure that may be
  reused without its surrounding chat.
- Export a shareable file and retain the plotting source. Open the exported
  image or PDF and inspect labels, clipped content, annotation collisions, and
  readability at the target size. Revise based on the rendered result.

Report whether data checks and visual inspection were actually performed. The
library's structural validation does not render figures or prove their accuracy.
