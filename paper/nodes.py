"""
All five LangGraph node functions for the /paper workflow.

Each node is async, receives the full PaperState, and returns a partial
dict of keys it is responsible for updating.

Node execution order enforced by the graph:
  discovery → [interrupt] → scoping → ingestion → clustering → synthesis
"""

import asyncio
import json
import os

import httpx
from langchain_core.messages import HumanMessage, SystemMessage

from .cdli_api import get_artifact, get_translation, advanced_search
from .state import ArtifactBrief, PaperState, Theme

# ---------------------------------------------------------------------------
# LLM factory — respects LLM_PROVIDER env var
# ---------------------------------------------------------------------------

def _build_llm():
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.2,
        )
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.1"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.2,
        )
    elif provider == "mistral":
        from langchain_mistralai import ChatMistralAI
        return ChatMistralAI(
            model=os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
            api_key=os.getenv("MISTRAL_API_KEY"),
            temperature=0.2,
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.2,
        )


# ---------------------------------------------------------------------------
# Node 1 — Discovery
# ---------------------------------------------------------------------------

async def discovery_node(state: PaperState) -> dict:
    """
    Uses advanced_search to find artifacts relevant to the topic.
    Returns a list of ArtifactBrief dicts.
    """
    topic = state["topic"]
    llm = _build_llm()

    # Ask the LLM to decompose the topic into 1–3 targeted search parameter sets.
    system = SystemMessage(content=(
        "You are a CDLI database expert. Your job is to turn a research topic into "
        "at most 3 CDLI advanced-search parameter sets. Each parameter set is a JSON object."
        "\n\nSupported keys for the object:\n"
        "- material: e.g. 'clay', 'stone', 'egyptian blue'\n"
        "- period: e.g. 'Ur III', 'Old Babylonian'\n"
        "- language: e.g. 'Sumerian', 'Akkadian'\n"
        "- genre: e.g. 'Administrative', 'Literary', 'Legal'\n"
        "- provenience: e.g. 'Nippur', 'Lagash', 'Ur'\n"
        "- artifact_type: e.g. 'tablet', 'cone', 'seal'\n"
        "- collection: e.g. 'British Museum', 'Vatican Museum'\n"
        "- atf_translation_text: search within English translations\n"
        "Output ONLY a JSON array of 1-3 parameter objects, nothing else. "
        "Example: [{\"material\": \"clay\", \"period\": \"Ur III\", \"genre\": \"Administrative\", \"limit\": 30}]"
    ))

    human = HumanMessage(content=f"Research topic: {topic}")
    response = await llm.ainvoke([system, human])

    # Parse the LLM's suggested queries
    try:
        raw = response.content.strip().strip("```json").strip("```").strip()
        query_sets: list[dict] = json.loads(raw)
        print(f"   (Debug: LLM suggested queries: {query_sets})", flush=True)
    except Exception:
        # Fallback: simple text search
        query_sets = [{"atf_translation_text": topic, "limit": 30}]
        print(f"   (Debug: LLM parsing failed. Using fallback: {query_sets})", flush=True)



    # Run all query sets and collect unique artifacts
    seen_ids: set[str] = set()
    found: list[ArtifactBrief] = []

    for params in query_sets[:3]:
        params.setdefault("limit", 30)
        try:
            data = await advanced_search(params)
            entities = data.get("entities", [])
            for e in entities:
                raw_id = str(e.get("id") or e.get("artifact_id") or "")
                if not raw_id or raw_id in seen_ids:
                    continue
                seen_ids.add(raw_id)
                found.append(ArtifactBrief(
                    id=f"P{raw_id.zfill(6)}",
                    title=e.get("designation") or e.get("museum_no") or "(no title)",
                    period=e.get("period") or "",
                    provenience=e.get("provenience") or "",
                ))
        except httpx.HTTPError:
            pass  # Network issues: skip this query set silently

    return {"found_artifacts": found, "errors": state.get("errors", [])}


# ---------------------------------------------------------------------------
# Node 2 — Scoping & Ranking
# ---------------------------------------------------------------------------

async def scoping_node(state: PaperState) -> dict:
    """
    Ranks discovered artifacts by metadata relevance and caps the list at 10.
    No tool calls — purely an LLM reasoning step.
    """
    topic = state["topic"]
    artifacts = state["found_artifacts"]

    if not artifacts:
        return {"shortlisted_artifacts": [], "errors": state.get("errors", []) + ["Discovery returned 0 artifacts."]}

    # Build a compact metadata list for the LLM to rank
    meta_lines = "\n".join(
        f"{i+1}. ID={a['id']} | Title={a['title']} | Period={a['period']} | Site={a['provenience']}"
        for i, a in enumerate(artifacts)
    )

    llm = _build_llm()
    system = SystemMessage(content=(
        "You are a cuneiform studies researcher. Given a research topic and a list of CDLI artifacts "
        "(with their ID, title, period, and provenience), select the top 10 most relevant artifacts. "
        "Output ONLY a JSON array of the selected artifact IDs in the format: [\"P254876\", \"P315278\", ...]. "
        "Prioritise: genre match with topic, period alignment, archaeological significance. "
        "Select AT MOST 10, even if more seem relevant."
    ))
    human = HumanMessage(content=f"Research topic: {topic}\n\nArtifacts:\n{meta_lines}")
    response = await llm.ainvoke([system, human])

    try:
        raw = response.content.strip().strip("```json").strip("```").strip()
        selected_ids: list[str] = json.loads(raw)
        # Normalise IDs (uppercase P prefix)
        selected_ids = [sid.upper() if sid.startswith("p") else sid for sid in selected_ids[:10]]
    except Exception:
        # Fallback: take first 10
        selected_ids = [a["id"] for a in artifacts[:10]]

    id_map = {a["id"]: a for a in artifacts}
    shortlisted = [id_map[sid] for sid in selected_ids if sid in id_map][:10]

    return {"shortlisted_artifacts": shortlisted}


# ---------------------------------------------------------------------------
# Node 3 — Ingestion & Summarization
# ---------------------------------------------------------------------------

async def ingestion_node(state: PaperState) -> dict:
    """
    Sequentially fetches each shortlisted artifact and writes a 3-sentence summary.
    Raw ATF text is discarded immediately after summarisation to protect context budget.
    """
    topic = state["topic"]
    artifacts = state["shortlisted_artifacts"]
    summaries: list[str] = list(state.get("artifact_summaries", []))
    errors: list[str] = list(state.get("errors", []))
    llm = _build_llm()

    async def summarize_one(artifact: ArtifactBrief) -> tuple[str, str or None]:
        artifact_id = artifact["id"]
        try:
            data = await get_artifact(artifact_id)
            if isinstance(data, list) and len(data) > 0:
                meta_dict = data[0]
            else:
                meta_dict = data
            if isinstance(meta_dict, list) and len(meta_dict) > 0:
                meta_dict = meta_dict[0]

            if not isinstance(meta_dict, dict):
                meta_dict = {
                    "designation": artifact["title"],
                    "period": artifact["period"],
                    "provenience": artifact["provenience"]
                }
            
            atf_snippet = ""
            try:
                insc = await get_translation(artifact_id)
                raw_atf = insc.get("atf") or insc.get("inscription") or ""
                atf_snippet = str(raw_atf)[:600]
            except Exception:
                pass

            meta_text = (
                f"ID: {artifact_id}\n"
                f"Title/Designation: {meta_dict.get('designation') or meta_dict.get('title') or artifact['title']}\n"
                f"Period: {meta_dict.get('period') or artifact['period']}\n"
                f"Provenience: {meta_dict.get('provenience') or artifact['provenience']}\n"
                f"Genre: {meta_dict.get('genre') or ''}\n"
                f"Language: {meta_dict.get('language') or ''}\n"
            )
            if atf_snippet:
                meta_text += f"ATF excerpt: {atf_snippet}\n"

            system = SystemMessage(content=(
                f"You are writing an academic research paper about: '{topic}'.\n"
                "Write a concise 3-sentence summary of the following CDLI artifact, "
                "focused strictly on what the artifact reveals about the research topic. "
                "Begin the summary with the artifact ID in brackets, e.g. [P254876]. "
                "Do NOT copy raw ATF text verbatim — paraphrase and interpret it."
            ))
            human = HumanMessage(content=meta_text)
            response = await llm.ainvoke([system, human])
            return response.content.strip(), None
        except Exception as e:
            return f"[{artifact_id}] Summary unavailable.", f"{artifact_id}: {e}"

    # Run all summarization tasks in parallel
    results = await asyncio.gather(*(summarize_one(a) for a in artifacts))
    
    for summary, error in results:
        summaries.append(summary)
        if error:
            errors.append(error)

    return {"artifact_summaries": summaries, "errors": errors}



# ---------------------------------------------------------------------------
# Node 3.5 — Thematic Clustering
# ---------------------------------------------------------------------------

async def clustering_node(state: PaperState) -> dict:
    """
    Groups the 10 summaries into 3–5 research themes.
    Gives the Synthesis node an organisational backbone instead of a raw list.
    """
    topic = state["topic"]
    summaries = state["artifact_summaries"]

    if not summaries:
        return {"themes": []}

    summaries_text = "\n\n".join(summaries)
    llm = _build_llm()

    system = SystemMessage(content=(
        f"You are an academic editor preparing a paper on '{topic}'. "
        "Read the following artifact summaries and group them into 3–5 distinct thematic clusters "
        "(e.g. 'Taxation records', 'Agricultural distribution', 'Temple offerings'). "
        "For each theme output:\n"
        "  - name: short theme title\n"
        "  - supporting_artifacts: list of CDLI IDs (e.g. [\"P254876\"])\n"
        "  - summary: 2-sentence description of what the theme reveals\n\n"
        "Output ONLY a JSON array of theme objects matching this schema exactly:\n"
        "[{\"name\": \"...\", \"supporting_artifacts\": [\"P...\"], \"summary\": \"...\"}]"
    ))
    human = HumanMessage(content=summaries_text)

    response = await llm.ainvoke([system, human])

    try:
        raw = response.content.strip().strip("```json").strip("```").strip()
        themes_raw: list[dict] = json.loads(raw)
        themes: list[Theme] = [
            Theme(
                name=t.get("name", "Unnamed Theme"),
                supporting_artifacts=t.get("supporting_artifacts", []),
                summary=t.get("summary", ""),
            )
            for t in themes_raw
        ]
    except Exception:
        # Fallback: one generic theme containing all artifacts
        all_ids = [s.split("]")[0].lstrip("[") for s in summaries if s.startswith("[")]
        themes = [Theme(name=topic, supporting_artifacts=all_ids, summary="General corpus overview.")]

    return {"themes": themes}


# ---------------------------------------------------------------------------
# Node 4 — Synthesis
# ---------------------------------------------------------------------------

async def synthesis_node(state: PaperState) -> dict:
    """
    Writes the final structured paper in Markdown, using only the
    clustered themes. The LLM never sees raw ATF text at this stage.

    Strict enforced rule: every paragraph must include an inline CDLI ID citation.
    """
    topic = state["topic"]
    themes = state["themes"]
    errors = state.get("errors", [])

    themes_text = "\n\n".join(
        f"### Theme: {t['name']}\nSupporting artifacts: {', '.join(t['supporting_artifacts'])}\n{t['summary']}"
        for t in themes
    )

    system = SystemMessage(content=(
        f"You are an academic writer producing a structured research paper on: '{topic}'.\n\n"
        "You will use ONLY the thematic summaries provided below. Do NOT invent new artifacts or facts.\n\n"
        "CRITICAL CITATION RULE: Every single paragraph in the paper body MUST end with at least one "
        "inline citation in the format [CDLI ID: PXXXXXX]. Any paragraph without a citation is INVALID.\n\n"
        "Output a COMPLETE Markdown document with these exact sections:\n"
        "## Abstract\n"
        "## Introduction\n"
        "## Corpus Overview\n"
        "## Textual Evidence\n"
        "(organised by theme — use the theme names as subsection headers)\n"
        "## Discussion\n"
        "## References\n"
        "(each cited artifact as: `PXXXXXX — <title> · https://cdli.earth/artifacts/<numeric_id>`)\n\n"
        "The Abstract should be approximately 150 words. Other sections should be academically rigorous."
    ))
    human = HumanMessage(content=f"Thematic Research Summary:\n\n{themes_text}")

    llm = _build_llm()
    response = await llm.ainvoke([system, human])
    draft = response.content.strip()

    # Append any errors as a note at the end of the paper
    if errors:
        error_note = "\n\n---\n> **Note:** The following artifacts were unavailable and excluded:\n"
        error_note += "\n".join(f"> - {e}" for e in errors)
        draft += error_note

    return {"draft": draft}


# ---------------------------------------------------------------------------
# Node 4.5 — Evidence Evaluation
# ---------------------------------------------------------------------------

async def evaluation_node(state: PaperState) -> dict:
    """
    Critically evaluates the thematic clusters to decide if the evidence base
    is strong enough to write a research-grade paper.

    If the themes are too few, too vague, or cover fewer than 3 distinct
    supporting artifacts, the agent requests another round of targeted discovery
    (up to MAX_LOOPS times).
    """
    MAX_LOOPS = 2
    attempts = state.get("evaluation_attempts", 0)
    themes = state.get("themes", [])
    topic = state["topic"]

    if attempts >= MAX_LOOPS:
        return {"needs_more_research": False, "evaluation_attempts": attempts}

    all_cited_ids: set[str] = set()
    for t in themes:
        all_cited_ids.update(t.get("supporting_artifacts", []))

    if len(themes) >= 2 and len(all_cited_ids) >= 4:
        llm = _build_llm()
        themes_text = "\n\n".join(
            f"Theme: {t['name']}\nArtifacts ({len(t['supporting_artifacts'])}): "
            f"{', '.join(t['supporting_artifacts'])}\nSummary: {t['summary']}"
            for t in themes
        )
        system = SystemMessage(content=(
            f"You are a critical academic editor reviewing thematic clusters for a research paper on '{topic}'.\n"
            "Look at the themes and their supporting artifacts. Answer with a JSON object:\n"
            "{\"sufficient\": true/false, \"reason\": \"one sentence explaining your verdict\"}\n\n"
            "Mark 'sufficient: false' ONLY if:\n"
            "- Fewer than 2 distinct themes exist, OR\n"
            "- All themes are generic/repetitive (e.g., all say 'general overview'), OR\n"
            "- A key dimension of the topic is completely missing from all themes.\n"
            "Otherwise, mark 'sufficient: true'. Output JSON ONLY."
        ))
        human = HumanMessage(content=themes_text)
        try:
            response = await llm.ainvoke([system, human])
            raw = response.content.strip().strip("```json").strip("```").strip()
            verdict = json.loads(raw)
            needs_more = not verdict.get("sufficient", True)
        except Exception:
            needs_more = False
    else:
        needs_more = True

    return {
        "needs_more_research": needs_more,
        "evaluation_attempts": attempts + 1,
    }


# ---------------------------------------------------------------------------
# Node 6 — Citation Validator
# ---------------------------------------------------------------------------

async def citation_validator_node(state: PaperState) -> dict:
    """
    Post-synthesis guard: scans the draft for [CDLI ID: PXXXXXX] citations
    and checks each one against the shortlisted_artifacts list.

    Any cited ID that was NOT in our corpus is flagged as a hallucination.
    """
    import re

    draft = state.get("draft", "")
    shortlisted = state.get("shortlisted_artifacts", [])
    valid_ids = {a["id"].upper() for a in shortlisted}

    cited_ids = set(re.findall(r"\[(?:CDLI ID:\s*)?(P\d+)\]", draft, re.IGNORECASE))
    cited_ids = {cid.upper() for cid in cited_ids}

    hallucinated = cited_ids - valid_ids
    issues: list[str] = []

    if hallucinated:
        issues = [f"Citation {cid} was not in the analysed corpus." for cid in sorted(hallucinated)]
        warning = (
            "\n\n---\n"
            "> **Warning:** The following artifact IDs were cited but were NOT part of the "
            "analysed corpus and may be hallucinated. Please verify manually:\n"
            + "\n".join(f"> - `{cid}`" for cid in sorted(hallucinated))
        )
        draft += warning

    return {"draft": draft, "citation_issues": issues}
