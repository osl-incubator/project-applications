#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-osl-incubator/project-applications}"

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: gh CLI is required." >&2
  exit 1
fi

create_label() {
  local name="$1"
  local color="$2"
  local description="$3"
  echo "Creating/updating label: ${name}"
  gh label create "$name" \
    --repo "$REPO" \
    --color "$color" \
    --description "$description" \
    --force
}

# Type labels
create_label "type: poc-application" "0E8A16" "Application for Proof of Concept stage"
create_label "type: incubation-application" "0E8A16" "Application for Incubation stage"
create_label "type: stage-change" "1D76DB" "Request to change project lifecycle stage"
create_label "type: graduation-request" "5319E7" "Request to graduate from incubation"
create_label "type: maintenance-review" "FBCA04" "Review of project maintenance status"
create_label "type: pause-request" "FEF2C0" "Request to pause incubation"
create_label "type: archive-review" "B60205" "Review archive/removal outcome"
create_label "type: reactivation-request" "0E8A16" "Request to reactivate a project"
create_label "type: documentation" "0075CA" "Documentation changes"
create_label "type: automation" "1D76DB" "Automation, scripts, or workflows"

# Status labels
create_label "status: needs-triage" "D4C5F9" "Needs initial review"
create_label "status: needs-info" "F9D0C4" "Waiting for applicant or maintainer information"
create_label "status: in-review" "C2E0C6" "Under OSL review"
create_label "status: approved" "0E8A16" "Approved by OSL"
create_label "status: declined" "B60205" "Declined by OSL"
create_label "status: deferred" "FBCA04" "Deferred for later review"
create_label "status: paused" "FEF2C0" "Paused pending changes or maintainer response"
create_label "status: at-risk" "D93F0B" "Project may be paused, removed, or archived if unresolved"
create_label "status: archived" "5319E7" "Archived or no longer active"
create_label "status: graduated" "5319E7" "Graduated from incubation"
create_label "status: reactivated" "0E8A16" "Project reactivated"

# Stage labels
create_label "stage: poc" "C5DEF5" "Proof of Concept stage"
create_label "stage: incubation" "BFD4F2" "Incubation stage"
create_label "stage: graduated" "D4C5F9" "Graduated stage"
create_label "stage: inactive" "E4E669" "Inactive stage"
create_label "stage: archived" "EDEDED" "Archived stage"

# Check labels
create_label "check: license" "BFDADC" "License needs review"
create_label "check: code-of-conduct" "BFDADC" "Code of Conduct needs review"
create_label "check: maintainers" "BFDADC" "Maintainer readiness needs review"
create_label "check: public-repo" "BFDADC" "Repository visibility needs review"
create_label "check: roadmap" "BFDADC" "Roadmap or milestones need review"
create_label "check: documentation" "BFDADC" "Documentation needs review"
create_label "check: tests" "BFDADC" "Tests or validation need review"
create_label "check: security" "BFDADC" "Security reporting needs review"
create_label "check: governance" "BFDADC" "Governance needs review"
create_label "check: acknowledgement" "BFDADC" "README/docs acknowledgement needs review"
create_label "check: scientific-review" "BFDADC" "Scientific review path needs review"
create_label "check: gsoc-readiness" "BFDADC" "GSoC/internship readiness needs review"
create_label "check: metadata" "BFDADC" "Project metadata needs review"
create_label "check: links" "BFDADC" "Links need review"

# Review labels
create_label "review: maintainer-readiness" "F9D0C4" "Maintainer readiness review"
create_label "review: contributor-readiness" "F9D0C4" "Contributor readiness review"
create_label "review: technical-readiness" "F9D0C4" "Technical readiness review"
create_label "review: governance" "F9D0C4" "Governance review"
create_label "review: security" "F9D0C4" "Security review"
create_label "review: adoption" "F9D0C4" "Adoption or usefulness review"
create_label "review: pyopensci" "F9D0C4" "pyOpenSci review tracking"
create_label "review: ropensci" "F9D0C4" "rOpenSci review tracking"
create_label "review: equivalent-review" "F9D0C4" "Equivalent scientific review tracking"

# Priority labels
create_label "priority: low" "C5DEF5" "Low priority"
create_label "priority: medium" "FBCA04" "Medium priority"
create_label "priority: high" "B60205" "High priority"

# Decision labels
create_label "decision: accepted" "0E8A16" "Accepted decision"
create_label "decision: declined" "B60205" "Declined decision"
create_label "decision: deferred" "FBCA04" "Deferred decision"
create_label "decision: needs-changes" "D93F0B" "Needs changes before approval"

# Bot labels
create_label "bot: intake" "EDEDED" "Created or updated by intake automation"
create_label "bot: health-check" "EDEDED" "Created or updated by health-check automation"
create_label "bot: stale" "EDEDED" "Created or updated by stale automation"
create_label "bot: link-check" "EDEDED" "Created or updated by link-check automation"

echo "Done."
