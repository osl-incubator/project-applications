# Reviewer Guide

Reviewers help OSL make consistent, transparent, and kind decisions about
incubation applications and lifecycle reviews.

## Principles

- Be transparent, specific, and kind.
- Ask for evidence links.
- Do not approve projects missing license or Code of Conduct.
- Do not approve projects with unreachable maintainers.
- Do not imply GSoC, funding, contributor, mentor, internship, grant, external
  review, or long-term maintenance guarantees.
- Do not create expectations that OSL will maintain the project indefinitely.
- For scientific Python/R projects, identify the review path early.
- Prefer `status: needs-info` over rejection when missing information is easy to
  fix.
- Leave a clear decision comment.

## Review steps

1. Confirm the issue template matches the request type.
2. Check required fields for links and concrete evidence.
3. Inspect the public repository or proposal repository.
4. Confirm license, Code of Conduct, maintainer contact, and public discussion
   path.
5. Assess alignment with OSL values and program scope.
6. Confirm reviewer or mentor capacity.
7. Add labels for missing checks or review areas.
8. Request missing information, defer, decline, or approve.
9. Record a decision comment with next steps.

## Baseline blockers

Do not approve until resolved:

- no OSI-approved open-source license;
- no public `LICENSE` file;
- no Code of Conduct with reporting path;
- no active/reachable maintainer;
- private, archived, or unavailable repository;
- unsafe or hostile community behavior;
- unclear ownership or license status;
- inability to collaborate publicly.

## Suggested approval comment

```markdown
Thanks for your application. OSL has approved this project for the Incubator
Program at the following stage: **<PoC/Incubation>**.

Next steps:

- Add the OSL incubation acknowledgement to README/docs.
- Confirm maintainers and communication channel.
- Confirm milestones for the next review period.
- If you want to prepare GSoC/internship ideas, please provide scoped ideas,
  mentors, and issue links. Participation and slots are not guaranteed.
```

## Suggested needs-info comment

```markdown
Thanks for your application. OSL needs the following information before review
can continue:

- ...

Please update this issue with links/evidence. If we do not hear back, the
request may be paused or closed as incomplete, but you may reapply later.
```

## Suggested declined comment

```markdown
Thanks for your application. OSL cannot accept this project into incubation at
this time because:

- ...

You are welcome to apply again after addressing these points.
```

## Suggested graduation approval comment

```markdown
Thanks for the graduation request. OSL has approved graduation for
**<project>**.

Next steps:

- Update README/docs with the graduation acknowledgement.
- Confirm the repository location and ownership after graduation.
- Update public listings and project metadata.
- Keep maintainer, security, and contact information current.
```
