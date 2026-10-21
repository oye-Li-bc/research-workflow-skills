# Contributing

Issues are welcome for a reproducible failure, unclear trigger, wrong instruction,
or a host compatibility observation. Include a minimal sanitized input and what
was actually tested. Do not include authentication files, private vault content,
or proprietary paper figures.

A change should improve one workflow. Keep name/description precise, supporting
resources discoverable, and paths configurable. New skills need a catalog entry,
source/license information, one positive and one boundary evaluation case.

Run:

```sh
python tools/skillctl.py validate
python -m unittest discover -s tests -v
```

Report helper checks separately from actual agent runs, GUI inspection, live
network use, or compilation. Add tests for meaningful failures rather than
matching instruction wording. See [maintenance](docs/maintenance.md).
