#!/usr/bin/env python3
"""Small, standard-library GitHub helpers shared by review scripts."""

from __future__ import annotations

import base64
import datetime as dt
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class HTTPClient:
    """Read public web and GitHub API resources without executing repository code."""

    def __init__(self, timeout: int, token: str | None = None) -> None:
        self.timeout = timeout
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    def _headers(self, *, authenticated: bool = True) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "osl-incubator-review-bot",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if authenticated and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _get(self, url: str, *, authenticated: bool = True) -> bytes:
        request = urllib.request.Request(url, headers=self._headers(authenticated=authenticated))
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return response.read()

    def get_json(
        self,
        url: str,
        *,
        allow_anonymous_retry: bool = False,
    ) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
        try:
            return json.loads(self._get(url).decode("utf-8")), None
        except urllib.error.HTTPError as exc:
            if allow_anonymous_retry and self.token and exc.code in {401, 403, 404}:
                try:
                    return json.loads(self._get(url, authenticated=False).decode("utf-8")), None
                except Exception as retry_exc:  # noqa: BLE001 - callers need a report, not a traceback
                    return None, describe_http_error(retry_exc)
            return None, describe_http_error(exc)
        except Exception as exc:  # noqa: BLE001 - callers need a report, not a traceback
            return None, describe_http_error(exc)

    def get_text(
        self,
        url: str,
        *,
        allow_anonymous_retry: bool = False,
    ) -> tuple[str | None, str | None]:
        try:
            return self._get(url).decode("utf-8", errors="replace"), None
        except urllib.error.HTTPError as exc:
            if allow_anonymous_retry and self.token and exc.code in {401, 403, 404}:
                try:
                    return self._get(url, authenticated=False).decode("utf-8", errors="replace"), None
                except Exception as retry_exc:  # noqa: BLE001 - callers need a report, not a traceback
                    return None, describe_http_error(retry_exc)
            return None, describe_http_error(exc)
        except Exception as exc:  # noqa: BLE001 - callers need a report, not a traceback
            return None, describe_http_error(exc)

    def check_url(self, url: str) -> tuple[bool, str]:
        headers = {"User-Agent": "osl-incubator-review-bot"}
        for method in ("HEAD", "GET"):
            try:
                request = urllib.request.Request(url, headers=headers, method=method)
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return True, f"HTTP {response.status}"
            except urllib.error.HTTPError as exc:
                if method == "HEAD" and exc.code in {403, 405}:
                    continue
                return False, f"HTTP {exc.code}: {exc.reason}"
            except Exception as exc:  # noqa: BLE001 - report-only helper
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
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        return None
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        return None
    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo):
        return None
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


def github_content(
    client: HTTPClient,
    owner: str,
    repo: str,
    path: str,
    *,
    allow_anonymous_retry: bool = False,
) -> tuple[str | None, str | None]:
    url_path = urllib.parse.quote(path, safe="/")
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{url_path}"
    payload, error = client.get_json(url, allow_anonymous_retry=allow_anonymous_retry)
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
        except Exception as exc:  # noqa: BLE001 - report-only helper
            return None, f"could not decode content: {exc}"
    download_url = payload.get("download_url")
    if isinstance(download_url, str):
        return client.get_text(download_url, allow_anonymous_retry=allow_anonymous_retry)
    return "", None


def first_existing_content(
    client: HTTPClient,
    owner: str,
    repo: str,
    paths: list[str],
    *,
    allow_anonymous_retry: bool = False,
) -> tuple[str | None, str | None, str | None]:
    last_error: str | None = None
    for path in paths:
        content, error = github_content(
            client,
            owner,
            repo,
            path,
            allow_anonymous_retry=allow_anonymous_retry,
        )
        if error is None:
            return path, content, None
        last_error = error
    return None, None, last_error
