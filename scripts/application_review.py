#!/usr/bin/env python3
"""Collect a deterministic, read-only preliminary review of an application issue.

The script reads issue data and public repository metadata through the GitHub API.
It never clones or executes applicant code. Its JSON output is suitable for human
review and for the separately constrained OpenAI synthesis step.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.parse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from github_evidence import HTTPClient, github_content, parse_datetime, parse_github_repo


POC_FIELDS = (
    "Project name",
    "Repository or proposal URL",
    "Maintainers",
    "Problem statement",
    "Intended users or beneficiaries",
    "Current concept, prototype, or proposal status",
    "License link",
    "Code of Conduct link",
    "Initial tasks or validation questions",
    "1-3 month exploration plan",
    "Expected OSL support",
    "Confirmations",
)

INCUBATION_FIELDS = (
    "Project name",
    "Repository URL",
    "Short description",
    "Alignment with OSL",
    "License link",
    "Code of Conduct link",
    "Maintainers",
    "Public communication channel or contact path",
    "Current maintenance status",
    "Maintenance context",
    "Roadmap and milestones",
    "Contributor readiness",
    "Documentation, tests, releases, and quality practices",
    "Governance and maintainer model",
    "Users, adopters, citations, deployments, pilots, or community interest",
    "Scientific software review path",
    "Scientific review plan, if applicable",
    "GSoC/internship readiness, if applicable",
    "Expected OSL support",
    "Confirmations",
)

EXPECTED_CONFIRMATIONS = {"poc": 7, "incubation": 10}

OPTIONAL_FIELDS = (
    "Website or documentation URL",
    "Security policy or vulnerability reporting URL",
)

TERMINAL_STATUS_LABELS = {
    "status: approved",
    "status: declined",
    "status: deferred",
    "status: paused",
    "status: archived",
    "status: graduated",
}

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
URL_RE = re.compile(r"https://[^\s<>\])]+", re.IGNORECASE)
HANDLE_RE = re.compile(r"(?<![\w@])@([A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?)\b")
CHECKBOX_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s+(.+?)\s*$", re.MULTILINE)
HEADING_RE = re.compile(r"^###\s+(.+?)\s*$")

DOCUMENT_CANDIDATES = {
    "license": ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"),
    "code_of_conduct": ("CODE_OF_CONDUCT.md", ".github/CODE_OF_CONDUCT.md"),
    "readme": ("README.md", "README.rst", "README.txt"),
    "contributing": ("CONTRIBUTING.md", ".github/CONTRIBUTING.md"),
    "security": ("SECURITY.md", ".github/SECURITY.md"),
}

DOCUMENT_LIMITS = {
    "license": 1_500,
    "code_of_conduct": 8_000,
    "readme": 12_000,
    "contributing": 10_000,
    "security": 5_000,
}


@dataclass
class Check:
    id: str
    category: str
    status: str
    summary: str
    detail: str
    blocking: bool = False
    evidence: list[dict[str, str]] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["evidence"] = self.evidence or []
        return result


def normalize_label(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


KNOWN_FIELD_LABELS = {
    normalize_label(label): label for label in (*POC_FIELDS, *INCUBATION_FIELDS, *OPTIONAL_FIELDS)
}


def parse_issue_form(body: str) -> dict[str, str]:
    """Parse known GitHub issue-form H3 sections while preserving headings in answers."""

    fields: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        match = HEADING_RE.match(line)
        if match:
            canonical = KNOWN_FIELD_LABELS.get(normalize_label(match.group(1)))
            if canonical:
                current = canonical
                fields.setdefault(current, [])
                continue
        if current is not None:
            fields[current].append(line)
    return {label: "\n".join(lines).strip() for label, lines in fields.items()}


def is_meaningful(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip().casefold()
    if not normalized:
        return False
    if normalized in {"_no response_", "no response", "none provided", "tbd", "todo"}:
        return False
    return not bool(re.fullmatch(r"<[^>]+>", normalized))


def issue_labels(issue: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for label in issue.get("labels") or []:
        if isinstance(label, str):
            result.append(label)
        elif isinstance(label, dict) and isinstance(label.get("name"), str):
            result.append(label["name"])
    return result


def application_type(labels: Iterable[str], title: str = "") -> str | None:
    label_set = set(labels)
    if "type: poc-application" in label_set:
        return "poc"
    if "type: incubation-application" in label_set:
        return "incubation"
    lowered = title.casefold()
    if lowered.startswith("poc application:"):
        return "poc"
    if lowered.startswith("incubation application:"):
        return "incubation"
    return None


def checkbox_state(value: str) -> tuple[list[str], list[str]]:
    checked: list[str] = []
    unchecked: list[str] = []
    for marker, label in CHECKBOX_RE.findall(value):
        (checked if marker.casefold() == "x" else unchecked).append(label.strip())
    return checked, unchecked


def extract_urls(value: str) -> list[str]:
    return list(dict.fromkeys(URL_RE.findall(value)))


def repository_field(fields: dict[str, str]) -> str:
    return fields.get("Repository URL") or fields.get("Repository or proposal URL") or ""


def is_https_url(value: str) -> bool:
    if not value or len(value) > 2_048 or any(character.isspace() for character in value):
        return False
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def application_checks(kind: str, fields: dict[str, str]) -> tuple[list[Check], list[str]]:
    required = POC_FIELDS if kind == "poc" else INCUBATION_FIELDS
    checks: list[Check] = []
    obvious_missing: list[str] = []

    missing = [label for label in required if not is_meaningful(fields.get(label))]
    if missing:
        obvious_missing.extend(missing)
        checks.append(
            Check(
                id="form.required_fields",
                category="application",
                status="fail",
                summary="Required application answers are missing",
                detail=", ".join(missing),
                blocking=True,
            )
        )
    else:
        checks.append(
            Check(
                id="form.required_fields",
                category="application",
                status="pass",
                summary="All required application sections contain an answer",
                detail=f"Checked {len(required)} required sections for the {kind} form.",
            )
        )

    confirmations = fields.get("Confirmations", "")
    checked, unchecked = checkbox_state(confirmations)
    expected_confirmations = EXPECTED_CONFIRMATIONS[kind]
    if unchecked or len(checked) < expected_confirmations:
        if unchecked:
            detail = ", ".join(unchecked)
        else:
            detail = f"Parsed {len(checked)} of {expected_confirmations} expected confirmations."
        obvious_missing.append("Confirmations")
        checks.append(
            Check(
                id="form.confirmations",
                category="application",
                status="fail",
                summary="One or more required confirmations are unchecked",
                detail=detail,
                blocking=True,
            )
        )
    else:
        checks.append(
            Check(
                id="form.confirmations",
                category="application",
                status="pass",
                summary="All rendered confirmations are checked",
                detail=f"Parsed {len(checked)} checked confirmations.",
            )
        )

    repo_value = repository_field(fields)
    if is_https_url(repo_value.strip()):
        checks.append(
            Check(
                id="form.repository_url",
                category="application",
                status="pass",
                summary="Repository or proposal URL is syntactically valid",
                detail=repo_value.strip(),
                evidence=[{"label": "Application repository URL", "url": repo_value.strip()}],
            )
        )
    else:
        obvious_missing.append("Valid repository or proposal URL")
        checks.append(
            Check(
                id="form.repository_url",
                category="application",
                status="fail",
                summary="Repository or proposal URL is missing or invalid",
                detail="Provide a complete https:// URL.",
                blocking=True,
            )
        )

    maintainers = fields.get("Maintainers", "")
    contact_kinds = []
    if EMAIL_RE.search(maintainers):
        contact_kinds.append("email")
    if extract_urls(maintainers):
        contact_kinds.append("URL")
    if HANDLE_RE.search(maintainers):
        contact_kinds.append("GitHub handle")
    if contact_kinds:
        checks.append(
            Check(
                id="form.maintainer_contact",
                category="maintainers",
                status="pass",
                summary="A maintainer contact path is listed",
                detail=f"Detected: {', '.join(contact_kinds)}. Reachability still requires human confirmation.",
            )
        )
    else:
        checks.append(
            Check(
                id="form.maintainer_contact",
                category="maintainers",
                status="warn",
                summary="No obvious maintainer contact path was detected",
                detail="A reviewer should confirm a GitHub handle, email, or public contact URL.",
            )
        )

    all_urls = []
    for value in fields.values():
        all_urls.extend(extract_urls(value))
    checks.append(
        Check(
            id="form.evidence_links",
            category="application",
            status="info",
            summary=f"Found {len(set(all_urls))} unique HTTPS evidence link(s)",
            detail="Only GitHub repository evidence is fetched automatically; other links remain for human review.",
        )
    )
    return checks, list(dict.fromkeys(obvious_missing))


def github_blob_url(owner: str, repo: str, branch: str, path: str) -> str:
    return f"https://github.com/{owner}/{repo}/blob/{urllib.parse.quote(branch, safe='')}/{urllib.parse.quote(path, safe='/')}"


def reporting_path_detected(content: str) -> bool:
    lowered = content.casefold()
    positions = [match.start() for match in re.finditer(r"report(?:ing|s|ed)?", lowered)]
    for position in positions:
        window = content[position : position + 1_500]
        if EMAIL_RE.search(window) or URL_RE.search(window):
            return True
    return False


def find_path(paths: dict[str, str], candidates: Iterable[str]) -> str | None:
    for candidate in candidates:
        actual = paths.get(candidate.casefold())
        if actual:
            return actual
    return None


def repository_checks(
    repository_url: str,
    client: HTTPClient,
) -> tuple[list[Check], list[dict[str, str]], dict[str, Any]]:
    checks: list[Check] = []
    documents: list[dict[str, str]] = []
    metadata: dict[str, Any] = {"url": repository_url}
    parsed = parse_github_repo(repository_url)
    if not parsed:
        checks.append(
            Check(
                id="repository.github",
                category="repository",
                status="manual",
                summary="Repository is not hosted on github.com",
                detail="Automated GitHub checks were skipped; a reviewer must inspect the linked public repository or proposal.",
                evidence=[{"label": "Repository or proposal", "url": repository_url}],
            )
        )
        return checks, documents, metadata

    owner, repo = parsed
    full_name = f"{owner}/{repo}"
    metadata["full_name"] = full_name
    repo_api = f"https://api.github.com/repos/{owner}/{repo}"
    payload, error = client.get_json(repo_api, allow_anonymous_retry=True)
    if error or not isinstance(payload, dict):
        unavailable = not (error or "").startswith("HTTP 404")
        checks.append(
            Check(
                id="repository.reachable",
                category="repository",
                status="warn" if unavailable else "fail",
                summary="Repository metadata could not be retrieved",
                detail=error or "Unexpected GitHub API response.",
                blocking=not unavailable,
                evidence=[{"label": full_name, "url": f"https://github.com/{full_name}"}],
            )
        )
        return checks, documents, metadata

    html_url = str(payload.get("html_url") or f"https://github.com/{full_name}")
    evidence = [{"label": full_name, "url": html_url}]
    checks.append(
        Check(
            id="repository.reachable",
            category="repository",
            status="pass",
            summary="GitHub repository is reachable",
            detail=full_name,
            evidence=evidence,
        )
    )

    is_private = payload.get("private") is True
    checks.append(
        Check(
            id="repository.public",
            category="repository",
            status="fail" if is_private else "pass",
            summary="Repository is private" if is_private else "Repository is public",
            detail=str(payload.get("visibility") or ("private" if is_private else "public")),
            blocking=is_private,
            evidence=evidence,
        )
    )

    is_archived = payload.get("archived") is True
    checks.append(
        Check(
            id="repository.archived",
            category="repository",
            status="fail" if is_archived else "pass",
            summary="Repository is archived" if is_archived else "Repository is not archived",
            detail="Archived repositories require human follow-up." if is_archived else "GitHub reports archived=false.",
            blocking=is_archived,
            evidence=evidence,
        )
    )

    default_branch = str(payload.get("default_branch") or "")
    metadata.update(
        {
            "default_branch": default_branch,
            "archived": is_archived,
            "private": is_private,
            "has_issues": payload.get("has_issues"),
            "pushed_at": payload.get("pushed_at"),
            "license_spdx": (payload.get("license") or {}).get("spdx_id")
            if isinstance(payload.get("license"), dict)
            else None,
        }
    )

    pushed_at = parse_datetime(payload.get("pushed_at"))
    if pushed_at:
        age = (dt.datetime.now(dt.timezone.utc) - pushed_at).days
        checks.append(
            Check(
                id="repository.activity",
                category="repository",
                status="pass" if age <= 120 else "warn",
                summary="Repository activity was detected" if age <= 120 else "Repository has limited recent activity",
                detail=f"Last push was {age} day(s) ago on {pushed_at.date()}.",
                evidence=evidence,
            )
        )
    else:
        checks.append(
            Check(
                id="repository.activity",
                category="repository",
                status="warn",
                summary="Repository activity date is unavailable",
                detail="A reviewer should inspect the commit and release history.",
                evidence=evidence,
            )
        )

    tree_paths: dict[str, str] = {}
    if default_branch:
        encoded_branch = urllib.parse.quote(default_branch, safe="")
        tree_payload, tree_error = client.get_json(
            f"{repo_api}/git/trees/{encoded_branch}?recursive=1",
            allow_anonymous_retry=True,
        )
        if isinstance(tree_payload, dict) and isinstance(tree_payload.get("tree"), list):
            for item in tree_payload["tree"]:
                if isinstance(item, dict) and item.get("type") == "blob" and isinstance(item.get("path"), str):
                    tree_paths[item["path"].casefold()] = item["path"]
            if tree_payload.get("truncated"):
                checks.append(
                    Check(
                        id="repository.file_index",
                        category="repository",
                        status="warn",
                        summary="GitHub returned a truncated repository file index",
                        detail="Some document and test-presence checks may be incomplete.",
                        evidence=evidence,
                    )
                )
        elif tree_error:
            checks.append(
                Check(
                    id="repository.file_index",
                    category="repository",
                    status="warn",
                    summary="Repository file index could not be retrieved",
                    detail=tree_error,
                    evidence=evidence,
                )
            )

    found_documents: dict[str, tuple[str, str]] = {}
    for document_id, candidates in DOCUMENT_CANDIDATES.items():
        path = find_path(tree_paths, candidates) if tree_paths else None
        content: str | None = None
        error: str | None = None
        if path:
            content, error = github_content(client, owner, repo, path, allow_anonymous_retry=True)
        elif not tree_paths:
            for candidate in candidates:
                content, error = github_content(client, owner, repo, candidate, allow_anonymous_retry=True)
                if error is None:
                    path = candidate
                    break
        if path and error is None:
            found_documents[document_id] = (path, content or "")
            url = github_blob_url(owner, repo, default_branch or "HEAD", path)
            documents.append(
                {
                    "id": f"document.{document_id}",
                    "path": path,
                    "url": url,
                    "content": (content or "")[: DOCUMENT_LIMITS[document_id]],
                }
            )

    license_doc = found_documents.get("license")
    spdx = metadata.get("license_spdx")
    if license_doc:
        license_url = github_blob_url(owner, repo, default_branch or "HEAD", license_doc[0])
        checks.append(
            Check(
                id="repository.license",
                category="license",
                status="pass" if spdx and spdx != "NOASSERTION" else "manual",
                summary="Public LICENSE file found",
                detail=f"Found `{license_doc[0]}`; GitHub SPDX identifier: {spdx or 'not detected'}. OSI status and suitability require verification.",
                evidence=[{"label": license_doc[0], "url": license_url}],
            )
        )
    else:
        checks.append(
            Check(
                id="repository.license",
                category="license",
                status="fail",
                summary="No standard LICENSE file was found",
                detail="Checked LICENSE, LICENSE.md, LICENSE.txt, and COPYING on the default branch.",
                evidence=evidence,
            )
        )

    coc_doc = found_documents.get("code_of_conduct")
    if coc_doc:
        coc_url = github_blob_url(owner, repo, default_branch or "HEAD", coc_doc[0])
        has_reporting = reporting_path_detected(coc_doc[1])
        checks.append(
            Check(
                id="repository.code_of_conduct",
                category="code-of-conduct",
                status="pass" if has_reporting else "warn",
                summary="Code of Conduct with an apparent reporting path found"
                if has_reporting
                else "Code of Conduct found; reporting path was not detected",
                detail=f"Found `{coc_doc[0]}`. Human review should confirm that the reporting process is appropriate.",
                evidence=[{"label": coc_doc[0], "url": coc_url}],
            )
        )
    else:
        checks.append(
            Check(
                id="repository.code_of_conduct",
                category="code-of-conduct",
                status="fail",
                summary="No standard Code of Conduct file was found",
                detail="Checked CODE_OF_CONDUCT.md and .github/CODE_OF_CONDUCT.md on the default branch.",
                evidence=evidence,
            )
        )

    for document_id, friendly, missing_status in (
        ("readme", "README", "warn"),
        ("contributing", "contributor guide", "warn"),
        ("security", "security policy", "info"),
    ):
        document = found_documents.get(document_id)
        if document:
            url = github_blob_url(owner, repo, default_branch or "HEAD", document[0])
            checks.append(
                Check(
                    id=f"repository.{document_id}",
                    category="documentation",
                    status="pass",
                    summary=f"Public {friendly} found",
                    detail=f"Found `{document[0]}`.",
                    evidence=[{"label": document[0], "url": url}],
                )
            )
        else:
            checks.append(
                Check(
                    id=f"repository.{document_id}",
                    category="documentation",
                    status=missing_status,
                    summary=f"No standard {friendly} file was found",
                    detail="This may be acceptable for an early PoC but should be considered during human review.",
                    evidence=evidence,
                )
            )

    if payload.get("has_issues") is True:
        checks.append(
            Check(
                id="repository.issues",
                category="collaboration",
                status="pass",
                summary="GitHub Issues are enabled",
                detail="A public issue tracker is available.",
                evidence=[{"label": "Issue tracker", "url": f"{html_url}/issues"}],
            )
        )
        starter_payload, _ = client.get_json(
            f"{repo_api}/issues?state=open&labels=good%20first%20issue&per_page=1",
            allow_anonymous_retry=True,
        )
        has_starter = isinstance(starter_payload, list) and bool(starter_payload)
        checks.append(
            Check(
                id="repository.starter_issues",
                category="collaboration",
                status="pass" if has_starter else "info",
                summary="At least one open good first issue was found"
                if has_starter
                else "No open good first issue was found by the automated query",
                detail="Starter work is recommended and may also be described in the application.",
                evidence=[{"label": "Good first issues", "url": f"{html_url}/issues?q=is%3Aopen+label%3A%22good+first+issue%22"}],
            )
        )
    else:
        checks.append(
            Check(
                id="repository.issues",
                category="collaboration",
                status="warn",
                summary="GitHub Issues are not enabled",
                detail="A reviewer should confirm another public collaboration path.",
                evidence=evidence,
            )
        )

    workflow_present = any(path.startswith(".github/workflows/") for path in tree_paths)
    test_present = any(
        path.startswith(("test/", "tests/", "spec/", "specs/"))
        or re.search(r"(?:^|/)(?:test_.+|.+_test|.+\.test|.+\.spec)\.[a-z0-9]+$", path)
        for path in tree_paths
    )
    package_path = find_path(tree_paths, ("package.json",))
    if package_path:
        package_content, package_error = github_content(
            client,
            owner,
            repo,
            package_path,
            allow_anonymous_retry=True,
        )
        if package_error is None:
            try:
                package_data = json.loads(package_content or "{}")
                scripts = package_data.get("scripts") if isinstance(package_data, dict) else None
                test_present = test_present or (isinstance(scripts, dict) and "test" in scripts)
            except json.JSONDecodeError:
                pass
    checks.append(
        Check(
            id="repository.quality_signals",
            category="quality",
            status="pass" if test_present or workflow_present else "info",
            summary="Automated quality signals were found"
            if test_present or workflow_present
            else "No conventional test or CI paths were detected",
            detail=f"Tests detected: {'yes' if test_present else 'no'}; GitHub Actions workflows detected: {'yes' if workflow_present else 'no'}. Presence does not establish test quality or passing status.",
            evidence=evidence,
        )
    )
    return checks, documents, metadata


def fetch_issue(client: HTTPClient, repository: str, issue_number: int) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise SystemExit("--repository must be in owner/name form")
    payload, error = client.get_json(f"https://api.github.com/repos/{repository}/issues/{issue_number}")
    if error or not isinstance(payload, dict):
        raise SystemExit(f"Could not fetch issue {repository}#{issue_number}: {error or 'unexpected response'}")
    return payload


def load_event(path: Path) -> tuple[dict[str, Any], str | None]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("issue"), dict):
        raise SystemExit(f"{path}: event must contain an issue object")
    repository = payload.get("repository")
    full_name = repository.get("full_name") if isinstance(repository, dict) else None
    return payload["issue"], full_name if isinstance(full_name, str) else None


def build_report(
    issue: dict[str, Any],
    source_repository: str | None,
    client: HTTPClient,
    *,
    no_network: bool = False,
) -> dict[str, Any]:
    labels = issue_labels(issue)
    kind = application_type(labels, str(issue.get("title") or ""))
    skip_reason: str | None = None
    if kind is None:
        skip_reason = "Issue is not labeled as a PoC or Incubation application."
    elif TERMINAL_STATUS_LABELS.intersection(labels):
        skip_reason = "Issue already has a terminal or paused status."

    body = str(issue.get("body") or "")
    fields = parse_issue_form(body)
    checks: list[Check] = []
    obvious_missing: list[str] = []
    documents: list[dict[str, str]] = []
    repository_metadata: dict[str, Any] = {}

    if kind and skip_reason is None:
        form_checks, obvious_missing = application_checks(kind, fields)
        checks.extend(form_checks)
        repo_url = repository_field(fields).strip()
        if repo_url and not no_network:
            repo_checks, documents, repository_metadata = repository_checks(repo_url, client)
            checks.extend(repo_checks)
        elif repo_url:
            checks.append(
                Check(
                    id="repository.network_checks",
                    category="repository",
                    status="info",
                    summary="Repository network checks were skipped",
                    detail="The script was run with --no-network.",
                    evidence=[{"label": "Repository or proposal", "url": repo_url}],
                )
            )

    status_label = "status: needs-info" if obvious_missing else "status: in-review"
    counts = {status: 0 for status in ("pass", "warn", "fail", "info", "manual")}
    for check in checks:
        counts[check.status] = counts.get(check.status, 0) + 1

    user = issue.get("user") if isinstance(issue.get("user"), dict) else {}
    issue_number = issue.get("number") or issue.get("issue_number")
    issue_url = issue.get("html_url") or issue.get("url")
    return {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_repository": source_repository,
        "issue": {
            "number": issue_number,
            "title": issue.get("title"),
            "url": issue_url,
            "author": user.get("login") if isinstance(user, dict) else None,
            "labels": labels,
        },
        "application": {
            "type": kind,
            "fields": fields,
        },
        "repository": repository_metadata,
        "checks": [check.to_dict() for check in checks],
        "documents": documents,
        "counts": counts,
        "routing": {
            "skip": skip_reason is not None,
            "skip_reason": skip_reason,
            "status_label": status_label,
            "obvious_missing": obvious_missing,
            "reviewer": "xmnlab",
        },
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a deterministic preliminary review of an application issue.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--event", help="GitHub event JSON containing an issue object.")
    source.add_argument("--issue-number", type=int, help="Issue number to fetch with --repository.")
    parser.add_argument("--repository", help="Application repository in owner/name form.")
    parser.add_argument("--output", required=True, help="JSON report output path.")
    parser.add_argument("--timeout", type=int, default=15, help="Network timeout in seconds.")
    parser.add_argument("--no-network", action="store_true", help="Skip applicant repository network checks.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    client = HTTPClient(timeout=args.timeout)
    if args.event:
        issue, event_repository = load_event(Path(args.event))
        source_repository = args.repository or event_repository
    else:
        if not args.repository:
            raise SystemExit("--repository is required with --issue-number")
        issue = fetch_issue(client, args.repository, args.issue_number)
        source_repository = args.repository

    report = build_report(issue, source_repository, client, no_network=args.no_network)
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Reviewed issue {report['issue']['number']}: "
        f"{report['counts']['pass']} pass, {report['counts']['warn']} warning, "
        f"{report['counts']['fail']} fail"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
