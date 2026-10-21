---
name: jupyter-environment
description: "Diagnose notebook interface, kernel, package-version, and extension mismatches before changing a Jupyter or Conda environment."
license: MIT
---

# Jupyter environment diagnosis

Start with the symptom and the interpreter that runs the failing notebook. A
terminal's active Python and the notebook kernel may differ.

Run [env_report.py](scripts/env_report.py) with the suspected kernel interpreter:

```sh
python scripts/env_report.py --notebook ./lesson.ipynb
```

The report reads package metadata and notebook metadata; it does not import ML
packages, execute cells, install extensions, or read server tokens. If another
interpreter is suspected, run the same script with that interpreter and compare.

- Identify Notebook 7/JupyterLab versus Notebook 6/nbclassic before proposing
  an extension. A tutorial's interface may use a different extension system.
- For a binary import failure, preserve the original error, Python version,
  package versions, and kernel identity. A missing button and a NumPy ABI error
  need different fixes.
- For GPU requests, inspect the framework and driver evidence relevant to the
  current kernel. This helper does not prove CUDA availability.
- Make the smallest change that addresses the observed mismatch. Work in the
  requested environment; do not upgrade every Conda environment.
- Verify the failing operation after any authorized change. Package installation,
  command success, and a visible working UI are distinct pieces of evidence.

For slideshow boundaries use `notebook-slides` if available, or edit only the
notebook's slideshow metadata. Do not rerun or rewrite lesson code just to make
its toolbar resemble a screenshot.
