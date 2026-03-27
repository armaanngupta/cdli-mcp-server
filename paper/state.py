"""
Shared LangGraph state definition for the /paper workflow.
This TypedDict is the single source of truth passed between all nodes.
"""

from typing import TypedDict


class ArtifactBrief(TypedDict):
    id: str
    title: str
    period: str
    provenience: str


class Theme(TypedDict):
    name: str
    supporting_artifacts: list[str]  # list of CDLI IDs e.g. ["P254876", "P315278"]
    summary: str


class PaperState(TypedDict):
    # ── Input ─────────────────────────────────────────────────────────────────
    topic: str

    # ── Node 1: Discovery ─────────────────────────────────────────────────────
    found_artifacts: list[ArtifactBrief]

    # ── Node 2: Scoping ───────────────────────────────────────────────────────
    shortlisted_artifacts: list[ArtifactBrief]

    # ── Node 3: Ingestion ─────────────────────────────────────────────────────
    artifact_summaries: list[str]

    # ── Node 3.5: Thematic Clustering ─────────────────────────────────────────
    themes: list[Theme]

    # ── Node 4: Evidence Evaluation ───────────────────────────────────────────
    needs_more_research: bool       # If True, route back to scoping
    evaluation_attempts: int        # How many times we've looped (max 2)

    # ── Node 5: Synthesis ─────────────────────────────────────────────────────
    draft: str  # Final Markdown-formatted paper text

    # ── Node 6: Citation Validator ────────────────────────────────────────────
    citation_issues: list[str]      # Any hallucinated IDs found in the draft

    # ── Error accumulator (persists across all nodes) ─────────────────────────
    errors: list[str]

