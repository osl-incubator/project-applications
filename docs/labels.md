# Labels

Labels make application state, review checks, lifecycle stage, and automation
activity visible. The script `scripts/create-labels.sh` creates or updates these
labels with the GitHub CLI.

## Type labels

- `type: poc-application` — Application for Proof of Concept stage.
- `type: incubation-application` — Application for Incubation stage.
- `type: stage-change` — Request to change lifecycle stage.
- `type: graduation-request` — Request to graduate from incubation.
- `type: maintenance-review` — Review of project maintenance status.
- `type: pause-request` — Request to pause incubation.
- `type: archive-review` — Review archive/removal outcome.
- `type: reactivation-request` — Request to reactivate a project.
- `type: documentation` — Documentation changes.
- `type: automation` — Automation, scripts, or workflows.

## Status labels

- `status: needs-triage` — Needs initial review.
- `status: needs-info` — Waiting for applicant or maintainer information.
- `status: in-review` — Under OSL review.
- `status: approved` — Approved by OSL.
- `status: declined` — Declined by OSL.
- `status: deferred` — Deferred for later review.
- `status: paused` — Paused pending changes or maintainer response.
- `status: at-risk` — Project may be paused, removed, or archived if unresolved.
- `status: archived` — Archived or no longer active.
- `status: graduated` — Graduated from incubation.
- `status: reactivated` — Project reactivated.

## Stage labels

- `stage: poc`
- `stage: incubation`
- `stage: graduated`
- `stage: inactive`
- `stage: archived`

## Check labels

- `check: license`
- `check: code-of-conduct`
- `check: maintainers`
- `check: public-repo`
- `check: roadmap`
- `check: documentation`
- `check: tests`
- `check: security`
- `check: governance`
- `check: acknowledgement`
- `check: scientific-review`
- `check: gsoc-readiness`
- `check: metadata`
- `check: links`

## Review labels

- `review: maintainer-readiness`
- `review: contributor-readiness`
- `review: technical-readiness`
- `review: governance`
- `review: security`
- `review: adoption`
- `review: pyopensci`
- `review: ropensci`
- `review: equivalent-review`

## Priority labels

- `priority: low`
- `priority: medium`
- `priority: high`

## Decision labels

- `decision: accepted`
- `decision: declined`
- `decision: deferred`
- `decision: needs-changes`

## Bot labels

- `bot: intake`
- `bot: health-check`
- `bot: stale`
- `bot: link-check`
