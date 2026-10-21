# Repository work

The library lives in skills/. catalog.json is the maintained index. Keep skills
useful independently: common SKILL.md fields, relative references, configurable
paths, and no assumed access to another skill or proprietary tool.

Run `python tools/skillctl.py validate` and `python -m unittest discover -s tests -v`
after changes. For helper changes add a regression case for an observable failure.
`evals/cases.json` is a manual agent-behavior suite; do not call its cases passed
unless an actual agent run and reviewer evidence are recorded.

Do not copy local profiles, secrets, personal notes, sessions, or installed
third-party skills into the project. Explain provenance and test boundaries.
Do not alter a user's notebook code/output when adjusting presentation metadata.
