# Contributing

Thank you for helping maintain the OSL Incubator Project Applications
repository. This repository contains operational documentation, issue forms,
workflow automation, label definitions, and optional project records for the OSL
Incubator Program.

## Scope

Changes should keep the OSL website and this repository complementary:

- website: public policy, orientation, and high-level requirements;
- this repository: application forms, evidence collection, review workflow,
  automation, labels, and public decision records.

Policy changes should match the public OSL website incubation page. Do not make
this repository imply new guarantees that are not reflected in public policy.

## Editing documentation

Documentation lives in `README.md` and `docs/`.

When editing docs:

- keep wording transparent, specific, and kind;
- link to evidence or public policy where useful;
- preserve OSI license, Code of Conduct, maintainer reachability, public
  collaboration, scientific review, and acknowledgement requirements;
- avoid implying OSL guarantees funding, GSoC slots, contributors, interns,
  mentors, external review acceptance, or long-term maintenance.

## Editing issue forms

Issue forms live in `.github/ISSUE_TEMPLATE/`.

When editing forms:

- keep required evidence fields required when they reflect baseline criteria;
- preserve the GSoC/limited-program no-guarantee confirmation;
- preserve acknowledgement confirmation fields;
- quote labels containing colons, such as `"status: needs-triage"`;
- check that YAML remains valid before opening a pull request.

## Editing workflows

Workflows live in `.github/workflows/`. Bots should support human review, not
replace it. Do not add automation that archives, removes, or publicly changes a
project's lifecycle status without human review.

## Editing scripts

Scripts live in `scripts/` and should use the Python standard library or common
CLI tools already documented in this repository.

Run these checks before opening a pull request:

```bash
bash -n scripts/create-labels.sh
python -m py_compile scripts/*.py
python scripts/validate-project-records.py data/projects.example.json
```

If `data/projects.json` exists in a future version, validate it too:

```bash
python scripts/validate-project-records.py data/projects.json
```

## Pull request checklist

Before requesting review, confirm:

- Markdown renders correctly.
- YAML syntax is valid.
- Shell scripts pass `bash -n`.
- Python scripts pass `python -m py_compile`.
- New wording does not promise funding, GSoC, contributors, mentors, or
  indefinite OSL maintenance.
- Required criteria and acknowledgement language remain intact.

## Review expectations

Reviewers should be transparent, specific, and kind. Prefer asking for links or
clarifying information when missing information is easy to fix. Decline or defer
when baseline requirements cannot be met, when maintainers are unreachable, or
when OSL lacks capacity to support review.
