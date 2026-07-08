#!/usr/bin/env python3
"""Report-only health checks for optional OSL incubated project records.

The first version of this script is intentionally non-destructive and exits 0
so scheduled automation can publish a report without blocking on network or
record issues. Use validate-project-records.py when a hard validation failure is
needed.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ACKNOWLEDGEMENT_TERMS = (
    "open science labs",
    "osl incubator",
    "incubated by open science labs",
    "part of the osl incubator program",
    "graduated from the osl incubator program",
)


@dataclass
class Check:
    level: str
    name: str
    detail: str


@dataclass
class ProjectReport:
    name: str
    slug: str | None = None
    checks: list[Check] = field(default_factory=list)

    def add(self, level: str, name: str, detail: str) -> None:
        self.checks.append(Check(level=level, name=name, detail=detail))

    @property
    def counts(self) -> dict[str, int]:
        result = {"ok": 0, "warning": 0, "error": 0, "info": 0}
        for check in self.checks:
            result[check.level] = result.get(check.level, 0) + 1
        return result


class HTTPClient:
    def __init__(self, timeout: int) -> None:
        self.timeout = timeout
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "osl-incubator-health-check",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def get_json(self, url: str) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
        try:
            request = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = response.read().decode("utf-8")
            return json.loads(payload), None
        except Exception as exc:  # noqa: BLE001 - report-only script
            return None, describe_http_error(exc)

    def get_text(self, url: str) -> tuple[str | None, str | None]:
        try:
            request = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = response.read().decode("utf-8", errors="replace")
            return payload, None
        except Exception as exc:  # noqa: BLE001 - report-only script
            return None, describe_http_error(exc)

    def check_url(self, url: str) -> tuple[bool, str]:
        headers = {"User-Agent": "osl-incubator-health-check"}
        for method in ("HEAD", "GET"):
            try:
                request = urllib.request.Request(url, headers=headers, method=method)
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return True, f"HTTP {response.status}"
            except urllib.error.HTTPError as exc:
                if method == "HEAD" and exc.code in {403, 405}:
                    continue
                return False, f"HTTP {exc.code}: {exc.reason}"
            except Exception as exc:  # noqa: BLE001 - report-only script
                if method == "HEAD":
                    continue
                return False, describe_http_error(exc)
        return False, "unreachable"


def describe_http_error(exc: BaseException) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"HTTP {exc.code}: {exc.reason}"
    if isinstance(exc, urllib.error.URLError):
        return f"URL error: {exc.reason}"
    return f"{type(exc).__name__}: {exc}"


def parse_github_repo(url: str) -> tuple[str, str] | None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None
    if parsed.netloc.lower() != "github.com":
        return None
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        return None
    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


def parse_datetime(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        parsed = dt.datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc)
    except ValueError:
        return None


def github_content(client: HTTPClient, owner: str, repo: str, path: str) -> tuple[str | None, str | None]:
    url_path = urllib.parse.quote(path, safe="/")
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{url_path}"
    payload, error = client.get_json(url)
    if error:
        return None, error
    if not isinstance(payload, dict):
        return None, "unexpected content response"
    if payload.get("type") != "file":
        return None, "not a file"
    if payload.get("encoding") == "base64" and isinstance(payload.get("content"), str):
        try:
            data = base64.b64decode(payload["content"], validate=False)
            return data.decode("utf-8", errors="replace"), None
        except Exception as exc:  # noqa: BLE001 - report-only script
            return None, f"could not decode content: {exc}"
    download_url = payload.get("download_url")
    if isinstance(download_url, str):
        return client.get_text(download_url)
    return "", None


def first_existing_content(
    client: HTTPClient,
    owner: str,
    repo: str,
    paths: list[str],
) -> tuple[str | None, str | None, str | None]:
    last_error: str | None = None
    for path in paths:
        content, error = github_content(client, owner, repo, path)
        if error is None:
            return path, content, None
        last_error = error
    return None, None, last_error


def load_projects(source: Path) -> tuple[list[dict[str, Any]], str | None]:
    if not source.exists():
        return [], f"No project data file found at `{source}`. This is expected for v1 if issues or the website remain the source of truth."
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report-only script
        return [], f"Could not read `{source}`: {exc}"
    projects = data.get("projects") if isinstance(data, dict) else None
    if not isinstance(projects, list):
        return [], f"`{source}` does not contain a top-level `projects` list."
    normalized = [project for project in projects if isinstance(project, dict)]
    skipped = len(projects) - len(normalized)
    warning = None
    if skipped:
        warning = f"Skipped {skipped} non-object project records from `{source}`."
    return normalized, warning


def check_project(
    project: dict[str, Any],
    client: HTTPClient,
    *,
    no_network: bool,
    max_inactive_days: int,
) -> ProjectReport:
    name = str(project.get("name") or project.get("slug") or "Unnamed project")
    report = ProjectReport(name=name, slug=project.get("slug"))

    stage = str(project.get("stage") or "").strip().lower()
    repository = str(project.get("repository") or "").strip()
    website = str(project.get("website") or "").strip()
    maintainers = project.get("maintainers")

    if repository.startswith("https://"):
        report.add("ok", "repository URL", repository)
    else:
        report.add("error", "repository URL", "Missing or not an https:// URL.")

    if isinstance(maintainers, list) and maintainers:
        report.add("ok", "maintainers", f"{len(maintainers)} maintainer record(s) listed.")
    else:
        report.add("error", "maintainers", "No maintainer records listed.")

    if stage in {"poc", "incubation", "graduated", "inactive", "archived"}:
        report.add("ok", "stage", stage)
    elif stage:
        report.add("warning", "stage", f"Unexpected stage `{stage}`.")
    else:
        report.add("warning", "stage", "No stage recorded.")

    parsed_repo = parse_github_repo(repository)
    if parsed_repo:
        owner, repo = parsed_repo
        report.add("ok", "GitHub repository", f"Parsed as `{owner}/{repo}`.")
    elif repository:
        report.add("warning", "GitHub repository", "Repository is not a github.com URL; GitHub-specific checks skipped.")
        owner = repo = None  # type: ignore[assignment]
    else:
        owner = repo = None  # type: ignore[assignment]

    if no_network:
        report.add("info", "network checks", "Skipped because --no-network was used.")
    elif parsed_repo:
        owner, repo = parsed_repo
        run_github_checks(report, client, owner, repo, max_inactive_days=max_inactive_days)
    else:
        report.add("info", "network checks", "Skipped because no GitHub repository could be parsed.")

    if website:
        if website.startswith("https://"):
            if no_network:
                report.add("info", "website", f"Recorded: {website}; reachability not checked.")
            else:
                ok, detail = client.check_url(website)
                report.add("ok" if ok else "warning", "website", f"{website} ({detail})")
        else:
            report.add("warning", "website", "Website URL is not https://.")

    has_milestones = any(project.get(key) for key in ("milestones", "roadmap", "review_issue"))
    if stage in {"poc", "incubation"} and not has_milestones:
        report.add("warning", "milestones", "No milestones, roadmap, or review issue recorded.")
    if stage == "graduated" and not any(project.get(key) for key in ("graduation_issue", "graduation_review", "decision_url")):
        report.add("warning", "graduation record", "No graduation decision/review URL recorded.")

    scientific_review = project.get("scientific_review")
    if isinstance(scientific_review, dict):
        review_type = str(scientific_review.get("type") or "none")
        review_status = str(scientific_review.get("status") or "unknown")
        report.add("ok", "scientific review", f"{review_type}: {review_status}")
        if stage == "graduated" and review_type in {"pyopensci", "ropensci", "equivalent"}:
            if review_status != "accepted" or not scientific_review.get("url"):
                report.add("warning", "scientific review evidence", "Graduated scientific project should record accepted review URL.")
    else:
        report.add("warning", "scientific review", "No scientific_review metadata recorded.")

    return report


def run_github_checks(
    report: ProjectReport,
    client: HTTPClient,
    owner: str,
    repo: str,
    *,
    max_inactive_days: int,
) -> None:
    repo_payload, error = client.get_json(f"https://api.github.com/repos/{owner}/{repo}")
    if error or not isinstance(repo_payload, dict):
        report.add("warning", "GitHub API", error or "Unexpected repository response.")
        return

    if repo_payload.get("private") is False:
        report.add("ok", "repository visibility", "Repository is public.")
    else:
        report.add("error", "repository visibility", "Repository appears private or visibility is unknown.")

    if repo_payload.get("archived") is False:
        report.add("ok", "archive status", "Repository is not archived.")
    else:
        report.add("warning", "archive status", "Repository is archived or archive status is unknown.")

    default_branch = repo_payload.get("default_branch")
    if default_branch:
        report.add("ok", "default branch", str(default_branch))
    else:
        report.add("warning", "default branch", "No default branch reported.")

    pushed_at = parse_datetime(repo_payload.get("pushed_at"))
    if pushed_at:
        age_days = (dt.datetime.now(dt.timezone.utc) - pushed_at).days
        level = "ok" if age_days <= max_inactive_days else "warning"
        report.add(level, "recent activity", f"Last push was {age_days} day(s) ago ({pushed_at.date()}).")
    else:
        report.add("warning", "recent activity", "No pushed_at timestamp available.")

    open_issues_count = repo_payload.get("open_issues_count")
    if isinstance(open_issues_count, int):
        report.add("info", "open issues and PRs", f"GitHub reports {open_issues_count} open issue/PR item(s).")

    license_path, _, license_error = first_existing_content(client, owner, repo, ["LICENSE", "LICENSE.md", "COPYING"])
    if license_path:
        report.add("ok", "LICENSE file", f"Found `{license_path}`.")
    else:
        report.add("error", "LICENSE file", f"No LICENSE file found ({license_error}).")

    coc_path, _, coc_error = first_existing_content(client, owner, repo, ["CODE_OF_CONDUCT.md", ".github/CODE_OF_CONDUCT.md"])
    if coc_path:
        report.add("ok", "Code of Conduct", f"Found `{coc_path}`.")
    else:
        report.add("error", "Code of Conduct", f"No Code of Conduct found ({coc_error}).")

    readme_path, readme_text, readme_error = first_existing_content(client, owner, repo, ["README.md", "README.rst"])
    if readme_path:
        report.add("ok", "README", f"Found `{readme_path}`.")
        lower_readme = (readme_text or "").lower()
        if any(term in lower_readme for term in ACKNOWLEDGEMENT_TERMS):
            report.add("ok", "acknowledgement", "README appears to mention OSL/incubation status.")
        else:
            report.add("warning", "acknowledgement", "README does not appear to include OSL status acknowledgement.")
    else:
        report.add("error", "README", f"No README found ({readme_error}).")

    contributing_path, _, _ = first_existing_content(client, owner, repo, ["CONTRIBUTING.md", ".github/CONTRIBUTING.md"])
    if contributing_path:
        report.add("ok", "contributing guide", f"Found `{contributing_path}`.")
    else:
        report.add("warning", "contributing guide", "No CONTRIBUTING.md found.")

    security_path, _, _ = first_existing_content(client, owner, repo, ["SECURITY.md", ".github/SECURITY.md"])
    if security_path:
        report.add("ok", "security policy", f"Found `{security_path}`.")
    else:
        report.add("warning", "security policy", "No SECURITY.md found.")


def render_markdown(source: Path, source_note: str | None, reports: list[ProjectReport]) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# OSL Incubated Project Health Check",
        "",
        f"Generated: {now}",
        f"Source: `{source}`",
        "",
    ]
    if source_note:
        lines.extend([f"> {source_note}", ""])
    if not reports:
        lines.extend([
            "No project records were checked.",
            "",
            "This report is informational. It does not make lifecycle decisions.",
        ])
        return "\n".join(lines) + "\n"

    totals = {"ok": 0, "warning": 0, "error": 0, "info": 0}
    for report in reports:
        for level, count in report.counts.items():
            totals[level] += count
    lines.extend([
        "## Summary",
        "",
        f"- Projects checked: {len(reports)}",
        f"- OK: {totals['ok']}",
        f"- Warnings: {totals['warning']}",
        f"- Errors: {totals['error']}",
        f"- Info: {totals['info']}",
        "",
    ])

    icon = {"ok": "✅", "warning": "⚠️", "error": "❌", "info": "ℹ️"}
    for report in reports:
        heading = report.name
        if report.slug:
            heading += f" (`{report.slug}`)"
        lines.extend([f"## {heading}", ""])
        for check in report.checks:
            detail = check.detail.replace("\n", " ")
            lines.append(f"- {icon.get(check.level, '•')} **{check.name}:** {detail}")
        lines.append("")

    lines.extend([
        "This report is informational. OSL reviewers make lifecycle decisions through public review issues.",
        "",
    ])
    return "\n".join(lines)


def write_json_summary(path: Path, reports: list[ProjectReport]) -> None:
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "projects": [
            {
                "name": report.name,
                "slug": report.slug,
                "counts": report.counts,
                "checks": [check.__dict__ for check in report.checks],
            }
            for report in reports
        ],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a report-only health check for OSL incubated project records."
    )
    parser.add_argument("--source", default="data/projects.json", help="Path to project JSON records.")
    parser.add_argument("--output", help="Write Markdown report to this path instead of stdout.")
    parser.add_argument("--json-output", help="Optional JSON summary output path.")
    parser.add_argument("--max-inactive-days", type=int, default=120, help="Warn when last push is older than this many days.")
    parser.add_argument("--timeout", type=int, default=10, help="Network timeout in seconds.")
    parser.add_argument("--no-network", action="store_true", help="Skip network checks.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    source = Path(args.source)
    projects, source_note = load_projects(source)
    client = HTTPClient(timeout=args.timeout)
    reports = [
        check_project(project, client, no_network=args.no_network, max_inactive_days=args.max_inactive_days)
        for project in projects
    ]
    markdown = render_markdown(source, source_note, reports)
    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
    if args.json_output:
        write_json_summary(Path(args.json_output), reports)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        raise SystemExit(130)
