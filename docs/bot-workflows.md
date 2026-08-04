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

## Preliminary-review bot

Triggered when a PoC or Incubation application is opened, edited, or reopened.
It can also be run manually with an existing issue number.

Responsibilities:

- parse required issue-form sections and confirmations;
- inspect public GitHub repository metadata without cloning or executing code;
- report repository visibility, archive status, recent activity, and issue
  tracker availability;
- check for standard LICENSE, Code of Conduct, README, CONTRIBUTING, SECURITY,
  test, and GitHub Actions paths;
- identify an apparent Code of Conduct reporting path;
- use the OpenAI Responses API, when configured, to synthesize a
  schema-constrained advisory assessment of the application answers;
- update one marked issue comment instead of creating a new comment after every
  edit;
- route obviously incomplete forms to `status: needs-info`, otherwise route to
  `status: in-review`;
- add `bot: initial-review`, attempt to assign `xmnlab`, and mention `@xmnlab`
  for required human review.

The model receives only public issue answers, deterministic check results, and
bounded excerpts from public repository documents. Applicant content is treated
as untrusted data. The model has no tools and its output cannot directly control
labels, assignments, or decisions. Applicant repository code is never executed
by the secret-bearing workflow.

The generated report is advisory. It must not approve, decline, or promise OSL
support. Maintainer reachability, community safety, legal conclusions, OSL fit,
scientific-review requirements, reviewer capacity, and lifecycle decisions stay
with human reviewers.

### Configuration

Configure the following repository setting before expecting AI synthesis:

- Actions secret `OPENAI_API_KEY` — OpenAI Platform API key.

Optional Actions variables:

- `OPENAI_REVIEW_MODEL` — defaults to `gpt-5.6-terra`;
- `OPENAI_REVIEW_REASONING_EFFORT` — defaults to `low`.

If the secret is absent or the OpenAI API is unavailable, deterministic checks
still run and the comment explains that AI synthesis was unavailable.

To review an existing application such as issue 1:

```bash
gh workflow run application-review.yml -f issue_number=1
```

Keep model choice, prompt changes, and routing rules covered by representative
fixtures and human evaluation. API usage and spend limits should be monitored at
the OpenAI project level.

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
