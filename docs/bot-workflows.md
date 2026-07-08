# Bot Workflows

Bots should support human review, not replace it. Automation may label, remind,
validate, and report, but lifecycle decisions require human OSL review.

## Intake bot

Triggered on issue open, edit, or reopen.

Responsibilities:

- apply labels from issue forms;
- add `status: needs-triage`;
- post acknowledgement comment;
- remind applicants about license, Code of Conduct, GSoC/no-guarantee, and
  acknowledgement requirements;
- optionally add `status: needs-info` if obvious required fields are missing.

## Health-check bot

Runs monthly for PoC/Incubation, quarterly for Graduated, and every 2 weeks for
At-Risk projects when configured.

Checks may include:

- repository reachable;
- repository public;
- repository not archived;
- license exists;
- Code of Conduct exists;
- README exists;
- acknowledgement exists or is tracked;
- maintainers listed;
- documentation links work;
- recent activity or stable-maintenance note;
- stale PRs/issues;
- roadmap/milestones present for incubating projects;
- pyOpenSci/rOpenSci/equivalent review status where applicable.

The first version is report-only and does not open archive/removal issues
automatically.

## Stale bot

For application requests:

- 30 days waiting on applicant: comment and keep `status: needs-info`;
- 60 days waiting on applicant: pause or close as incomplete;
- allow reapplication.

For maintenance reviews:

- Day 0: concern detected;
- Day 1: issue opened and maintainers pinged;
- Day 30: mark at risk;
- Day 60: pause or removal/archive review;
- Day 90: human decision on archive/removal.

## Link-check bot

Runs on pull requests and weekly or monthly schedules. Checks links in docs,
issue templates, workflows, and project records.

## Label-check bot

Manual workflow that verifies label setup tooling and lists repository labels.
Use `scripts/create-labels.sh` to create or update labels when authenticated
with the GitHub CLI.
