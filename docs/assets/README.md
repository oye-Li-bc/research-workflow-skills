# README visuals

The original SVG artwork in this directory is covered by the repository's MIT
license. It uses system font stacks; no font files, stock images, external images,
scripts or third-party icon sets are embedded.

- [cover.svg](cover.svg): the project cover, 1440 × 520. It depicts paper,
  notebook and note cards as an illustration, not a product screenshot.
- [workflow-map.svg](workflow-map.svg): all seven skills grouped by research task,
  1440 × 730. The groups describe possible uses, not an automated pipeline or
  completed end-to-end evaluation.
- [workflow-map-mobile.svg](workflow-map-mobile.svg): a 660 × 1110 compact version
  with larger labels. README uses a `picture` source for viewports up to 600 px.

Edit the SVG source directly. Keep skill identifiers in sync with `catalog.json`,
update counts on the cover when the library changes, and retain accessible titles,
descriptions and README alt text. The English labels keep the diagrams readable
across systems without bundling a Chinese font; the README explains them in Chinese.

Before publishing, preview at GitHub's normal README width and a narrow browser
width. Check text clipping, legibility and both light and dark surrounding themes.
