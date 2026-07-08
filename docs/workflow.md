# Operational Workflow

This repository records the operational workflow for OSL Incubator Program
applications, lifecycle reviews, and maintenance checks. Bots assist with labels
and reminders, but OSL reviewers make decisions.

## Application workflow

```text
1. Applicant opens issue using PoC or Incubation template.
2. Bot applies type/status labels.
3. Bot posts intake comment with reminders.
4. OSL reviewer checks completeness.
5. If incomplete, reviewer adds `status: needs-info`.
6. Applicant updates request.
7. Reviewer performs eligibility/due-diligence review.
8. Reviewer confirms mentor/reviewer capacity.
9. Decision:
   - approved for PoC
   - approved for Incubation
   - needs changes
   - declined
   - deferred
10. If approved:
   - issue gets approved label;
   - onboarding checklist is created;
   - website/project list update is prepared when appropriate;
   - acknowledgement requirement is confirmed;
   - milestones are recorded.
```

### Completeness check

Reviewers should confirm that required fields contain links or clear evidence.
Applications missing license, Code of Conduct, reachable maintainers, public
repository/proposal repository, or project purpose should not be approved until
fixed.

### Due-diligence review

Reviewers should inspect the public repository and linked materials for:

- license and Code of Conduct presence;
- maintainer reachability;
- public collaboration path;
- alignment with OSL values;
- respectful community environment;
- roadmap and contributor readiness;
- scientific review path where relevant;
- no overstatement of OSL guarantees or ownership.

### Capacity check

Approval depends on OSL capacity as well as project readiness. Reviewers should
confirm that OSL has enough reviewer or mentor capacity to support the requested
stage. If capacity is unavailable, defer transparently.

## Graduation workflow

```text
1. Maintainer opens graduation request.
2. Bot labels request and posts checklist.
3. OSL checks evidence.
4. Reviewers evaluate maintenance, governance, docs, security, adoption,
   scientific review acceptance where relevant.
5. Optional public comment period, usually ~2 weeks.
6. Decision:
   - approved graduation
   - needs more work
   - deferred
   - declined for now
7. If approved:
   - status changes to graduated;
   - website listing is updated;
   - repository move is coordinated if needed;
   - README/docs acknowledgement is updated.
```

## Maintenance workflow

```text
Day 0: bot/reviewer detects concern and opens maintenance review.
Day 1: maintainers and OSL mentors are pinged.
Day 30: unresolved issue may be marked at-risk.
Day 60: OSL may pause incubation or stop directing contributors to project.
Day 90: OSL may archive OSL-hosted repo after human review or remove external
        project from public lists.
```

Maintenance review concerns can include missing license, missing Code of
Conduct, archived or unreachable repository, unreachable maintainers, stale
milestones, unsafe behavior, missing acknowledgement, broken documentation, or
blocked scientific review.

## Reactivation workflow

```text
1. Maintainer opens reactivation request.
2. Reviewer checks prior pause/archive/removal issue.
3. Maintainer provides evidence that baseline criteria are restored.
4. Reviewer checks maintenance plan, roadmap, communication, and acknowledgement.
5. OSL decides requested stage and records decision.
6. Public listings or labels are updated if approved.
```

## Decision records

Decision comments should be clear enough that future reviewers can understand:

- what was requested;
- what evidence was reviewed;
- what decision was made;
- which labels were applied;
- what next steps remain;
- which limitations apply, especially around GSoC, funding, and OSL capacity.
