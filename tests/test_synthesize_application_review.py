from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import synthesize_application_review as synthesis  # noqa: E402


def sample_report() -> dict:
    return {
        "issue": {"number": 1, "title": "PoC application: Example", "author": "applicant"},
        "application": {"type": "poc", "fields": {"Project name": "Example"}},
        "repository": {"full_name": "example/project"},
        "checks": [
            {
                "id": "repository.public",
                "status": "pass",
                "summary": "Repository is public",
                "detail": "public",
                "evidence": [{"label": "repository", "url": "https://github.com/example/project"}],
            }
        ],
        "documents": [],
        "counts": {"pass": 1, "warn": 0, "fail": 0, "info": 0, "manual": 0},
        "routing": {
            "skip": False,
            "status_label": "status: in-review",
            "reviewer": "xmnlab",
        },
    }


class SynthesisTests(unittest.TestCase):
    def test_request_is_non_tool_using_and_schema_constrained(self) -> None:
        payload = synthesis.build_openai_request(sample_report(), "Review safely.", "example-model", "low")
        self.assertFalse(payload["store"])
        self.assertNotIn("tools", payload)
        self.assertEqual(payload["text"]["format"]["type"], "json_schema")
        self.assertTrue(payload["text"]["format"]["strict"])
        self.assertIn("untrusted", payload["input"][1]["content"][0]["text"].casefold() or "")

    def test_extracts_responses_api_output_text(self) -> None:
        expected = {"summary": "Example"}
        response = {
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": json.dumps(expected)}],
                }
            ]
        }
        self.assertEqual(json.loads(synthesis.extract_output_text(response)), expected)

    def test_unknown_evidence_references_are_dropped(self) -> None:
        raw = {
            "summary": "Ready for review.",
            "readiness": "ready_for_human_review",
            "criteria": [
                {
                    "criterion": "Public repository",
                    "assessment": "satisfied",
                    "rationale": "The repository is public.",
                    "evidence_ids": ["repository.public", "invented.evidence"],
                }
            ],
            "strengths": [],
            "risks": [],
            "questions": [],
            "human_review_focus": [],
        }
        validated = synthesis.validate_assessment(raw, sample_report())
        self.assertEqual(validated["criteria"][0]["evidence_ids"], ["repository.public"])

    def test_decision_language_is_rejected(self) -> None:
        raw = {
            "summary": "This application should be approved.",
            "readiness": "ready_for_human_review",
            "criteria": [],
            "strengths": [],
            "risks": [],
            "questions": [],
            "human_review_focus": [],
        }
        with self.assertRaises(ValueError):
            synthesis.validate_assessment(raw, sample_report())

    def test_renderer_neutralizes_uncontrolled_mentions(self) -> None:
        assessment = {
            "summary": "Ask @applicant for details.",
            "readiness": "needs_information",
            "criteria": [],
            "strengths": [],
            "risks": [],
            "questions": ["Can @other-reviewer confirm this?"],
            "human_review_focus": [],
        }
        body = synthesis.render_markdown(sample_report(), assessment, model="example-model", ai_error=None)
        self.assertIn(synthesis.COMMENT_MARKER, body)
        self.assertIn("@xmnlab", body)
        self.assertNotIn("@applicant", body)
        self.assertNotIn("@other-reviewer", body)
        self.assertIn("@\u200bapplicant", body)
        self.assertNotIn("accepted", body.casefold())

    def test_safe_url_rejects_control_characters(self) -> None:
        self.assertIsNone(synthesis.safe_url("https://example.org/path\n@reviewer"))


if __name__ == "__main__":
    unittest.main()
