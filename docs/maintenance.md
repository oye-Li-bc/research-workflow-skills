# Maintain from real use

1. Record the task, input shape, observed failure, host/version, and expected
   behavior. Reduce the example and remove identifiers, credentials, private
   paths, paper assets, and unrelated conversation text.
2. Decide whether the defect is routing, missing procedural knowledge, helper
   behavior, or an unavailable host capability. Change the smallest relevant part.
3. For a helper bug add a regression that observes its behavior. For an instruction
   defect add a realistic case and reviewer rubric in evals/cases.json.
4. Run validation and tests. For instruction changes, run the relevant manual
   agent cases and record what the agent actually did. A case file alone is not
   a completed evaluation.
5. Update catalog lineage if source material changed. Check its redistribution
   rights before importing text/code/assets. Built-in installed skills need not
   be vendored merely to reference a workflow.
6. Update VERSION, catalog.json's version, CHANGELOG, and release notes together.
   Tag a tested commit as vX.Y.Z. The release workflow checks the tag, reruns
   validation/tests, builds the archive, and creates a release with checksums.

## Manual evaluation record

Keep private run logs locally. A publishable record can contain:

```json
{
  "case_id": "arxiv-source-positive",
  "skill_version": "0.1.0",
  "agent_and_model": "record actual settings",
  "date": "record actual date",
  "observed_actions": ["summarize actions actually observed"],
  "review_result": "pass, fail, or not-run",
  "review_notes": "evidence and remaining limits"
}
```

Do not copy local profiles or sessions into releases. Review each proposed change;
this repository does not automatically sync an entire local skill store.

## Release commands

```sh
python tools/skillctl.py validate
python -m unittest discover -s tests -v
python tools/skillctl.py build
git tag -a v0.1.0 -m "Research workflow skills v0.1.0"
git push origin v0.1.0
```

Use the current VERSION, not this initial version, for later releases. Review
the archive and the tag's commit before pushing. Public releases do not establish
external adoption or a performance claim.
