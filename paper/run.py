"""
CLI entry point for the /paper agent.

Usage:
    python -m paper.run "grain storage in Ur III period"
    python paper/run.py "grain storage in Ur III period"

Steps:
  1. Runs the discovery node and pauses.
  2. Shows what was found and prompts the user for confirmation.
  3. On "y", resumes the graph through scoping → ingestion → clustering → synthesis.
  4. Exports the final paper as a PDF into OUTPUT_DIR (default: paper/output/).
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from .cdli_api import close_mcp_client, init_mcp_client
from .graph import build_graph


SPINNER_LABELS = {
    "discovery":          "Searching CDLI corpus...",
    "scoping":            "Ranking and shortlisting artifacts...",
    "ingestion":          "Reading and summarizing artifacts...",
    "clustering":         "Identifying recurring historical themes...",
    "evaluation":         "Evaluating evidence quality...",
    "synthesis":          "Drafting the research paper...",
    "citation_validator": "Validating citations...",
}


async def run(topic: str) -> None:
    try:
        await init_mcp_client()
    except Exception as e:
        command = os.getenv("PAPER_MCP_COMMAND", "node")
        args = os.getenv("PAPER_MCP_ARGS", "build/index.js")
        workdir = os.getenv("PAPER_MCP_WORKDIR", str(Path(__file__).resolve().parent.parent))
        print(
            "[ERROR] Failed to initialize MCP connection for /paper.\n"
            f"        Tried: {command} {args}\n"
            f"        Workdir: {workdir}\n"
            "        Ensure the server is built (`npm run build`) and command is valid.\n"
            f"        Details: {e}\n",
            flush=True,
        )
        return

    try:
        graph = build_graph()
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "topic": topic,
            "found_artifacts": [],
            "shortlisted_artifacts": [],
            "artifact_summaries": [],
            "themes": [],
            "needs_more_research": False,
            "evaluation_attempts": 0,
            "draft": "",
            "citation_issues": [],
            "errors": [],
        }

        print(f"\nStarting /paper agent for topic: \"{topic}\"\n")

        # ── Phase 1: Run until interrupt (after discovery) ────────────────────────
        async for event in graph.astream(initial_state, config=config, stream_mode="debug"):
            etype = event.get("type")
            ename = event.get("payload", {}).get("name")

            if etype == "task" and ename == "discovery":
                print(f" {SPINNER_LABELS['discovery']}", flush=True)

            elif etype == "task_result" and ename == "discovery":
                found = event["payload"].get("result", {}).get("found_artifacts", [])
                print(f"   [DONE] Found {len(found)} artifacts.\n", flush=True)

        # ── Human-in-the-loop checkpoint ──────────────────────────────────────────
        snapshot = graph.get_state(config)
        found_count = len(snapshot.values.get("found_artifacts", []))

        if found_count == 0:
            print("[WARNING] No artifacts found for this topic. Try a broader search term.\n", flush=True)
            return

        answer = input(f"   Proceed with analyzing the top 10 most relevant artifacts? [y/n]: ").strip().lower()
        if answer != "y":
            print("   Cancelled.", flush=True)
            return

        print("\nResuming workflow...\n", flush=True)

        # ── Phase 2-5: Resume graph until END ────────────────────────────────────
        async for event in graph.astream(None, config=config, stream_mode="debug"):
            etype = event.get("type")
            ename = event.get("payload", {}).get("name")

            if etype == "task":
                label = SPINNER_LABELS.get(ename)
                if label:
                    print(f" {label}", flush=True)

            elif etype == "task_result":
                data = event["payload"].get("result", {})

                if ename == "scoping":
                    selected = data.get("shortlisted_artifacts", [])
                    print(f"   [DONE] Shortlisted {len(selected)} artifacts.\n", flush=True)
                elif ename == "ingestion":
                    summaries = data.get("artifact_summaries", [])
                    print(f"   [DONE] Summarized {len(summaries)} artifacts.\n", flush=True)
                elif ename == "clustering":
                    themes = data.get("themes", [])
                    theme_names = ", ".join(t["name"] for t in themes)
                    print(f"   [DONE] Identified themes: {theme_names}\n", flush=True)
                elif ename == "synthesis":
                    print(f"   [DONE] Paper draft complete.\n", flush=True)

        # ── Export to PDF ─────────────────────────────────────────────────────────
        final_state = graph.get_state(config)
        draft: str = final_state.values.get("draft", "")

        if not draft:
            print("⚠️   Synthesis produced no output. Check your API key or try again.\n")
            return

        output_dir = Path(os.getenv("OUTPUT_DIR", "paper/output"))
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_topic = topic[:50].replace(" ", "_").replace("/", "-")
        md_path = output_dir / f"{safe_topic}.md"

        # Export to Markdown (much safer than PDF for Unicode)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {topic}\n\n")
            f.write(draft)

        print(f"[SUCCESS] Paper saved to: {md_path.resolve()}\n", flush=True)
    finally:
        await close_mcp_client()



def main():
    if len(sys.argv) < 2:
        print("Usage: python -m paper.run \"<research topic>\"")
        sys.exit(1)

    topic = " ".join(sys.argv[1:])
    asyncio.run(run(topic))


if __name__ == "__main__":
    main()
