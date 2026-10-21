# Compatibility and dependencies

The distributed format uses `SKILL.md` with `name`, `description`, and `license`.
Descriptions determine routing; scripts and references remain relative to each
skill folder. No instruction depends on a proprietary tool name or another skill
being installed.

| Layer | Status in v0.1.0 |
|---|---|
| Frontmatter and local references | Automated static checks |
| Helper functions and CLI packaging | Offline regression tests |
| Codex/Hermes directory copies | Installer preserves complete skill folders |
| Automatic discovery in a particular application version | Not end-to-end tested |
| Instruction-following quality | Manual cases supplied; not yet run |
| Network retrieval, TeX compilation, GUI output | Requires separate live checks |

Codex directory conventions and host capabilities may evolve. Hermes can load a
profile-specific library. Confirm the actual destination from your environment
instead of hardcoding the maintainer's machine layout. A successful installation
means files were copied, not that an application loaded or followed them.

Helper requirements: Python 3.11+, no third-party packages. Additional workflow
requirements are listed in catalog.json: a compiler for compiled Beamer output,
a plotting library for figures, a viewer for visual QA, and source access for
paper-specific claims. These are not installed automatically.

### Adapting to another host

Use the host's available tools to read sources, execute local scripts, compile,
and inspect rendered results. If a capability is absent, deliver the useful
intermediate result and state the missing validation. Preserve the user's actual
requested task and their authorization for external writes or installations.
