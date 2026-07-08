# OSL Incubator Project Applications

This repository manages applications and lifecycle reviews for projects that
want to join, progress through, graduate from, pause, or reactivate within the
[Open Science Labs (OSL) Incubator Program](https://opensciencelabs.org/projects/incubation/).

The Incubator Program is a structured pathway for open-source projects that need
active support to become sustainable. It helps projects define milestones,
improve documentation and contributor onboarding, build maintainer practices,
and prepare for graduation.

## Purpose

Use this repository for operational program work:

- Proof of Concept (PoC) applications;
- incubation applications;
- stage-change and graduation requests;
- pause, at-risk, archive, and reactivation reviews;
- review checklists and public decision records;
- labels, validation scripts, and bot workflows.

The OSL website remains the public policy and orientation layer. This repository
holds detailed evidence, review workflow, templates, and automation.

## What incubation means

Incubation is a growth pathway for projects that need structure, mentoring, and
review before they can operate sustainably. It is deeper than affiliation:
affiliation is a relationship for independent projects, while incubation adds
milestones, maintenance review, contributor-readiness work, and graduation
criteria.

Incubation does **not** mean that OSL owns, maintains, certifies, funds, or
permanently supports a project. Day-to-day maintenance, roadmap decisions, and
releases remain the responsibility of project maintainers.

## Who should apply

This repository is for open-source projects that are:

- early-stage or validating a new idea;
- restarting after a pause;
- transitioning from an individual effort to a community project;
- growing and needing documentation, contributor onboarding, governance, or
  sustainability help;
- aligned with open science, research, education, public-interest technology,
  open-source infrastructure, or another OSL value.

## Lifecycle stages

| Stage | Purpose | Typical outcome |
| --- | --- | --- |
| Proof of Concept (PoC) | Validate feasibility, usefulness, and OSL alignment. | Move to incubation, continue PoC, pause, or end review. |
| Incubation | Build sustainable maintenance, documentation, governance, quality, and community practices. | Graduate, continue with new milestones, pause, or archive/remove. |
| Graduated | Operate with less direct OSL incubation support after completing milestones. | Continue as an independent or OSL-associated project. |
| Inactive / Archived | Stop directing contributors to abandoned, unsafe, or unsupported projects. | Reactivate after criteria and maintenance plan are restored. |

See [docs/lifecycle.md](docs/lifecycle.md) for detailed stage expectations.

## Before applying

Applications should include evidence that the project:

- has a clear purpose aligned with OSL values;
- uses an OSI-approved open-source license;
- includes a public `LICENSE` file;
- includes a `CODE_OF_CONDUCT.md` or equivalent public Code of Conduct with a
  reporting path;
- has at least one active and reachable maintainer;
- has a public repository or public proposal repository;
- has a public issue tracker, project board, discussion channel, or documented
  way to discuss work;
- has a public communication channel or contact path for users and contributors;
- can be maintained in public and welcome contributors respectfully;
- has maintainers willing to communicate with OSL mentors/reviewers;
- will add an OSL status acknowledgement to `README.md` and public docs if
  accepted.

Recommended readiness items include contributor instructions, a 3-6 month
roadmap, starter issues, user/developer docs, tests or a testing plan, a
technical overview, release/versioning plans, security reporting when relevant,
and evidence of users, adopters, contributors, pilots, citations, or community
interest where available.

See [docs/criteria.md](docs/criteria.md) for the full criteria.

## How to apply

Open a new issue using the appropriate template:

- **Proof of Concept application** for ideas, prototypes, or proposals that need
  validation before full incubation.
- **Incubation application** for projects ready for structured milestones and
  sustainability work.
- **Stage-change request** for PoC to Incubation or other lifecycle updates.
- **Graduation request** when an incubated project has met its milestones.
- **Pause, archive, or reactivation request** for lifecycle maintenance.

Please provide links to evidence wherever possible. If GitHub issue forms are
not accessible to you, contact OSL through the website or email path listed in
[`.github/ISSUE_TEMPLATE/config.yml`](.github/ISSUE_TEMPLATE/config.yml).

## Review workflow

A typical application review includes:

1. Applicant opens an issue using a template.
2. Bot applies type/stage/status labels and posts an intake reminder.
3. OSL reviewer checks completeness.
4. If information is missing, reviewer adds `status: needs-info`.
5. Applicant updates the issue with links or explanations.
6. Reviewer performs eligibility and due-diligence review.
7. OSL confirms mentor/reviewer capacity.
8. OSL records a decision: approved, needs changes, declined, or deferred.
9. If approved, onboarding tasks, acknowledgement text, milestones, and website
   updates are coordinated.

See [docs/workflow.md](docs/workflow.md) and
[docs/reviewer-guide.md](docs/reviewer-guide.md).

## Graduation

Graduation means a project completed its OSL incubation milestones and can
operate with less direct incubation support. Graduation review looks for stable
maintenance, documented governance, contributor onboarding, documentation,
release practices, security reporting where relevant, adoption or usefulness
evidence where available, and a future roadmap.

Scientific software may need external or equivalent review before graduation.
Scientific Python projects in pyOpenSci scope must be accepted by pyOpenSci;
scientific R projects in rOpenSci scope must be accepted by rOpenSci; other
scientific projects should agree with OSL on an equivalent review path during
incubation.

See [docs/graduation-guide.md](docs/graduation-guide.md) and
[docs/scientific-review.md](docs/scientific-review.md).

## GSoC, internships, grants, and limited programs

Incubated projects may prepare ideas for Google Summer of Code (GSoC),
internships, grants, or similar programs when OSL is participating and when the
project has enough mentor capacity. Participation is not guaranteed. External
selection, OSL capacity, mentor availability, project readiness, and limited
contributor slots all affect whether an idea can be selected or funded.

See [docs/gsoc-and-limited-programs.md](docs/gsoc-and-limited-programs.md).

## Acknowledgement requirement

Accepted projects should acknowledge their OSL status in `README.md` and, where
applicable, public documentation. Suggested incubation wording:

```markdown
## Open Science Labs Incubation

This project is incubated by Open Science Labs (OSL). Incubation means that OSL
supports the project through mentorship, structure, community connection, and
sustainability guidance, while day-to-day maintenance, roadmap decisions, and
releases remain the responsibility of the project maintainers.
```

Projects should update the acknowledgement when status changes, including PoC to
Incubation, Graduation, pause/at-risk, removal from public lists, or archive.
See [docs/acknowledgement.md](docs/acknowledgement.md).

## Maintenance reviews

OSL may open maintenance reviews when a project becomes unreachable, archived,
unsafe for contributors, missing required license or Code of Conduct materials,
stale without a maintenance note, missing required acknowledgement, or blocked on
critical graduation requirements. Reviews are human decisions supported by bot
checks; bots do not archive or remove projects automatically.

See [docs/bot-workflows.md](docs/bot-workflows.md).

## Useful links

- [Open Science Labs](https://opensciencelabs.org/)
- [OSL Incubator Program](https://opensciencelabs.org/projects/incubation/)
- [OSL project list](https://opensciencelabs.org/projects/list/)
- [OSL Discord](https://opensciencelabs.org/discord)
- [pyOpenSci](https://www.pyopensci.org/)
- [pyOpenSci Python Package Guide](https://www.pyopensci.org/python-package-guide/)
- [pyOpenSci Peer Review Process](https://www.pyopensci.org/about-peer-review/index.html)
- [rOpenSci](https://ropensci.org/)
- [rOpenSci Software Peer Review](https://ropensci.org/software-review/)
- [rOpenSci Dev Guide](https://devguide.ropensci.org/)
