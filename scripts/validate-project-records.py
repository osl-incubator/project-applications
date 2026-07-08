#!/usr/bin/env python3
"""Validate optional data/projects.json-style records for OSL incubation."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Any

ALLOWED_STAGES = {"poc", "incubation", "graduated", "inactive", "archived"}
ALLOWED_REVIEW_TYPES = {"none", "not_applicable", "pyopensci", "ropensci", "equivalent", "other", "unknown"}
ALLOWED_REVIEW_STATUSES = {
    "not_applicable",
    "planned",
    "in_progress",
    "pending",
    "accepted",
    "blocked",
    "deferred",
    "unsure",
    "unknown",
}
REQUIRED_PROJECT_KEYS = {"name", "slug", "stage", "repository", "maintainers", "scientific_review"}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def is_https_url(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def is_date_or_null(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    try:
        dt.date.fromisoformat(value)
        return True
    except ValueError:
        return False


def validate_project(project: Any, index: int) -> list[str]:
    prefix = f"projects[{index}]"
    errors: list[str] = []
    if not isinstance(project, dict):
        return [f"{prefix}: must be an object"]

    missing = sorted(REQUIRED_PROJECT_KEYS - set(project))
    for key in missing:
        errors.append(f"{prefix}.{key}: missing required key")

    name = project.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append(f"{prefix}.name: must be a non-empty string")

    slug = project.get("slug")
    if not isinstance(slug, str) or not SLUG_RE.match(slug):
        errors.append(f"{prefix}.slug: must be kebab-case lowercase text")

    stage = project.get("stage")
    if stage not in ALLOWED_STAGES:
        errors.append(f"{prefix}.stage: must be one of {', '.join(sorted(ALLOWED_STAGES))}")

    if not is_https_url(project.get("repository")):
        errors.append(f"{prefix}.repository: must be an https:// URL")

    for optional_url_key in ("website", "code_of_conduct", "decision_url", "graduation_issue"):
        value = project.get(optional_url_key)
        if value not in (None, "") and not is_https_url(value):
            errors.append(f"{prefix}.{optional_url_key}: must be an https:// URL when present")

    maintainers = project.get("maintainers")
    if not isinstance(maintainers, list) or not maintainers:
        errors.append(f"{prefix}.maintainers: must be a non-empty list")
    elif all(isinstance(item, dict) for item in maintainers):
        for maintainer_index, maintainer in enumerate(maintainers):
            has_identity = any(maintainer.get(key) for key in ("name", "github", "email", "url"))
            if not has_identity:
                errors.append(f"{prefix}.maintainers[{maintainer_index}]: must include name, github, email, or url")
            if maintainer.get("url") and not is_https_url(maintainer.get("url")):
                errors.append(f"{prefix}.maintainers[{maintainer_index}].url: must be an https:// URL")
    else:
        errors.append(f"{prefix}.maintainers: every maintainer must be an object")

    acknowledgement_required = project.get("acknowledgement_required")
    if acknowledgement_required is not None and not isinstance(acknowledgement_required, bool):
        errors.append(f"{prefix}.acknowledgement_required: must be true or false when present")

    if not is_date_or_null(project.get("last_reviewed")):
        errors.append(f"{prefix}.last_reviewed: must be null or YYYY-MM-DD")

    scientific_review = project.get("scientific_review")
    if not isinstance(scientific_review, dict):
        errors.append(f"{prefix}.scientific_review: must be an object")
    else:
        review_type = scientific_review.get("type")
        review_status = scientific_review.get("status")
        review_url = scientific_review.get("url")
        if review_type not in ALLOWED_REVIEW_TYPES:
            errors.append(f"{prefix}.scientific_review.type: must be one of {', '.join(sorted(ALLOWED_REVIEW_TYPES))}")
        if review_status not in ALLOWED_REVIEW_STATUSES:
            errors.append(f"{prefix}.scientific_review.status: must be one of {', '.join(sorted(ALLOWED_REVIEW_STATUSES))}")
        if review_url is not None and not is_https_url(review_url):
            errors.append(f"{prefix}.scientific_review.url: must be null or an https:// URL")
        if stage == "graduated" and review_type in {"pyopensci", "ropensci", "equivalent"}:
            if review_status != "accepted" or not is_https_url(review_url):
                errors.append(f"{prefix}.scientific_review: graduated scientific projects must record accepted review URL")

    return errors


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate OSL incubator project JSON records.")
    parser.add_argument("path", help="Path to projects JSON file.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    path = Path(args.path)
    errors: list[str] = []

    if not path.exists():
        print(f"error: {path} does not exist", file=sys.stderr)
        return 1

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in {path}: {exc}", file=sys.stderr)
        return 1

    if not isinstance(data, dict):
        errors.append("root: must be an object")
        projects: list[Any] = []
    else:
        projects = data.get("projects")  # type: ignore[assignment]
        if not isinstance(projects, list):
            errors.append("root.projects: must be a list")
            projects = []

    for index, project in enumerate(projects):
        errors.extend(validate_project(project, index))

    if errors:
        print(f"{path}: invalid project records", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"{path}: OK ({len(projects)} project record(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
