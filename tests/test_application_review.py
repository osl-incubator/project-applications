from __future__ import annotations

import base64
import datetime as dt
import json
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import application_review  # noqa: E402


POC_BODY = """### Project name

Example Science

### Repository or proposal URL

https://github.com/example/science

### Maintainers

Example Maintainer (@example), maintainer@example.org

### Problem statement

Researchers need a public tool.

### Design details

This heading is part of the answer, not an issue-form field.

### Intended users or beneficiaries

Researchers and students.

### Current concept, prototype, or proposal status

A public prototype exists.

### License link

https://github.com/example/science/blob/main/LICENSE

### Code of Conduct link

https://github.com/example/science/blob/main/CODE_OF_CONDUCT.md

### Initial tasks or validation questions

Validate installation and contributor onboarding.

### 1-3 month exploration plan

Onboard two contributors and merge one external pull request.

### Expected OSL support

Mentorship and contributor outreach guidance.

### Confirmations

- [x] The project uses or will use an OSI-approved open-source license.
- [x] The project has or will add a public LICENSE file.
- [x] The project has or will add a Code of Conduct with a reporting path.
- [x] At least one maintainer is reachable and can participate in PoC.
- [x] The project can be developed in public and welcome contributors respectfully.
- [x] If accepted, we will acknowledge OSL PoC/incubation status in README/docs where applicable.
- [x] I understand OSL does not guarantee funding or contributors.
"""


class FakeGitHubClient:
    def __init__(self) -> None:
        now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        self.repo = {
            "html_url": "https://github.com/example/science",
            "private": False,
            "visibility": "public",
            "archived": False,
            "default_branch": "main",
            "pushed_at": now,
            "has_issues": True,
            "license": {"spdx_id": "MIT"},
        }
        self.files = {
            "LICENSE": "MIT License",
            "CODE_OF_CONDUCT.md": "## Reporting\nReport concerns to conduct@example.org.",
            "README.md": "# Example Science\nA research tool.",
            "CONTRIBUTING.md": "# Contributing\nRun the tests.",
            "SECURITY.md": "# Security\nEmail security@example.org.",
            "package.json": json.dumps({"scripts": {"test": "node --test"}}),
            ".github/workflows/test.yml": "name: test",
            "tests/example.test.js": "test('example', () => {});",
        }

    def get_json(
        self,
        url: str,
        *,
        allow_anonymous_retry: bool = False,
    ) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
        del allow_anonymous_retry
        if url == "https://api.github.com/repos/example/science":
            return self.repo, None
        if "/git/trees/main?recursive=1" in url:
            return {
                "tree": [{"type": "blob", "path": path} for path in self.files],
                "truncated": False,
            }, None
        if "/issues?state=open" in url:
            return [{"number": 1}], None
        marker = "/contents/"
        if marker in url:
            path = url.split(marker, 1)[1]
            if path in self.files:
                encoded = base64.b64encode(self.files[path].encode()).decode()
                return {"type": "file", "encoding": "base64", "content": encoded}, None
            return None, "HTTP 404: Not Found"
        raise AssertionError(f"Unexpected URL: {url}")

    def get_text(self, url: str, *, allow_anonymous_retry: bool = False) -> tuple[str | None, str | None]:
        raise AssertionError(f"Unexpected text URL: {url} ({allow_anonymous_retry})")


class ApplicationReviewTests(unittest.TestCase):
    def test_parse_issue_form_preserves_unknown_heading_in_answer(self) -> None:
        fields = application_review.parse_issue_form(POC_BODY)
        self.assertIn("### Design details", fields["Problem statement"])
        self.assertEqual(fields["Project name"], "Example Science")

    def test_complete_poc_routes_to_human_review(self) -> None:
        issue = {
            "number": 7,
            "title": "PoC application: Example Science",
            "body": POC_BODY,
            "html_url": "https://github.com/osl-incubator/project-applications/issues/7",
            "labels": [{"name": "type: poc-application"}, {"name": "status: needs-triage"}],
            "user": {"login": "applicant"},
        }
        report = application_review.build_report(
            issue,
            "osl-incubator/project-applications",
            FakeGitHubClient(),
        )
        self.assertFalse(report["routing"]["skip"])
        self.assertEqual(report["routing"]["status_label"], "status: in-review")
        self.assertEqual(report["routing"]["obvious_missing"], [])
        check_by_id = {check["id"]: check for check in report["checks"]}
        self.assertEqual(check_by_id["repository.license"]["status"], "pass")
        self.assertEqual(check_by_id["repository.code_of_conduct"]["status"], "pass")
        self.assertEqual(check_by_id["repository.quality_signals"]["status"], "pass")

    def test_obvious_missing_answer_routes_to_needs_info(self) -> None:
        fields = application_review.parse_issue_form(POC_BODY.replace("Researchers and students.", ""))
        checks, missing = application_review.application_checks("poc", fields)
        self.assertIn("Intended users or beneficiaries", missing)
        self.assertTrue(next(check for check in checks if check.id == "form.required_fields").blocking)

    def test_terminal_status_skips_publication(self) -> None:
        issue = {
            "number": 8,
            "title": "PoC application: Example Science",
            "body": POC_BODY,
            "labels": ["type: poc-application", "status: approved"],
            "user": {"login": "applicant"},
        }
        report = application_review.build_report(
            issue,
            "osl-incubator/project-applications",
            FakeGitHubClient(),
            no_network=True,
        )
        self.assertTrue(report["routing"]["skip"])

    def test_repository_url_rejects_markdown_injection(self) -> None:
        self.assertFalse(application_review.is_https_url("https://example.org/repo\n@reviewer"))
        self.assertIsNone(application_review.parse_github_repo("https://github.com/example/repo%29%5D"))


if __name__ == "__main__":
    unittest.main()
