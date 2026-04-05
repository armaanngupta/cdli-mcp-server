import os
import unittest

from paper.cdli_api import (
    advanced_search,
    close_mcp_client,
    get_artifact,
    get_translation,
    init_mcp_client,
)


@unittest.skipUnless(
    os.getenv("PAPER_RUN_LIVE_INTEGRATION") == "1",
    "Set PAPER_RUN_LIVE_INTEGRATION=1 to run live MCP/CDLI integration tests.",
)
class TestMcpIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await init_mcp_client()

    async def asyncTearDown(self):
        await close_mcp_client()

    async def test_advanced_search_get_artifact_get_translation(self):
        result = await advanced_search({"atf_translation_text": "rain", "limit": 1})
        self.assertIn("entities", result)

        entities = result.get("entities", [])
        self.assertGreaterEqual(len(entities), 1)

        artifact_id = entities[0]["id"]

        artifact = await get_artifact(f"P{str(artifact_id).zfill(6)}")
        self.assertIsInstance(artifact, dict)

        translation = await get_translation(f"P{str(artifact_id).zfill(6)}")
        self.assertIn("atf", translation)


if __name__ == "__main__":
    unittest.main()
