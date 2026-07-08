#!/usr/bin/env python3
"""Generate a Markdown review summary from a project JSON record."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_project(path: Path, selector: str | None) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("projects"), list):
        projects = [project for project in data["projects"] if isinstance(project, dict)]
        if selector:
            for project in projects:
                if selector in {project.get("slug"), project.get("name")}:
                    return project
            raise SystemExit(f"No project matched selector: {selector}")
        if not projects:
            raise SystemExit("No project records found")
        return projects[0]
    if isinstance(data, dict):
        return data
    raise SystemExit("Input must be a project object or an object with a projects list")


def value(project: dict[str, Any], key: str, default: str = "Not provided") -> str:
    current = project.get(key)
    if current in (None, ""):
        return default
    if isinstance(current, (dict, list)):
        return json.dumps(current, indent=2)
    return str(current)


def render(project: dict[str, Any]) -> str:
    maintainers = project.get("maintainers")
    if isinstance(maintainers, list):
        maintainer_lines = []
        for maintainer in maintainers:
            if isinstance(maintainer, dict):
                pieces = [str(maintainer[key]) for key in ("name", "github", "email", "url") if maintainer.get(key)]
                maintainer_lines.append(" / ".join(pieces) or "Unspecified maintainer")
            else:
                maintainer_lines.append(str(maintainer))
        maintainer_text = "\n".join(f"- {line}" for line in maintainer_lines) or "- Not provided"
    else:
        maintainer_text = "- Not provided"

    scientific_review = project.get("scientific_review") if isinstance(project.get("scientific_review"), dict) else {}
    lines = [
        f"# Review Summary: {value(project, 'name')}",
        "",
        "## Basic information",
        "",
        f"- Slug: `{value(project, 'slug')}`",
        f"- Stage: `{value(project, 'stage')}`",
        f"- Repository: {value(project, 'repository')}",
        f"- Website/docs: {value(project, 'website', 'N/A')}",
        f"- License: {value(project, 'license', 'Not recorded')}",
        f"- Code of Conduct: {value(project, 'code_of_conduct', 'Not recorded')}",
        "",
        "## Maintainers",
        "",
        maintainer_text,
        "",
        "## Scientific review",
        "",
        f"- Type: `{scientific_review.get('type', 'none')}`",
        f"- Status: `{scientific_review.get('status', 'unknown')}`",
        f"- URL: {scientific_review.get('url') or 'N/A'}",
        "",
        "## Reviewer checklist",
        "",
        "- [ ] License is OSI-approved and public LICENSE file exists.",
        "- [ ] Code of Conduct exists with reporting path.",
        "- [ ] Maintainers are reachable.",
        "- [ ] Public collaboration path exists.",
        "- [ ] Roadmap or milestones are current for the requested stage.",
        "- [ ] README/docs acknowledgement status is correct.",
        "- [ ] Scientific review path is documented where relevant.",
        "- [ ] No GSoC/funding/contributor/mentor guarantees are implied.",
        "",
        "## Decision notes",
        "",
        "<!-- Add reviewer notes, decision, conditions, and next steps. -->",
        "",
    ]
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Markdown review summary from project JSON.")
    parser.add_argument("source", help="Project JSON file or projects.json file.")
    parser.add_argument("--project", help="Project name or slug to select when source contains a projects list.")
    parser.add_argument("--output", help="Write summary to this file instead of stdout.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = load_project(Path(args.source), args.project)
    summary = render(project)
    if args.output:
        Path(args.output).write_text(summary, encoding="utf-8")
    else:
        print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
