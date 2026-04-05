import unittest

from paper.cdli_mcp import (
    _parse_advanced_search_text,
    _parse_metadata_text,
    normalize_artifact_id,
)
from paper.mcp_client import MCPToolError


class TestCdliApiParsing(unittest.TestCase):
    def test_normalize_artifact_id(self):
        self.assertEqual(normalize_artifact_id("P315278"), "315278")
        self.assertEqual(normalize_artifact_id("p000123"), "000123")
        self.assertEqual(normalize_artifact_id("315278"), "315278")

    def test_parse_advanced_search_citations_and_total(self):
        text = (
            "P254876 — Rain invocation ritual\n"
            "https://cdli.earth/artifacts/254876\n\n"
            "P315278 — BM 01234\n"
            "https://cdli.earth/artifacts/315278\n\n"
            "(Showing 2 of 547 total results)"
        )
        parsed = _parse_advanced_search_text(text)

        self.assertEqual(parsed["paging"]["count"], 547)
        self.assertEqual(len(parsed["entities"]), 2)
        self.assertEqual(parsed["entities"][0]["id"], "254876")
        self.assertEqual(parsed["entities"][0]["designation"], "Rain invocation ritual")

    def test_parse_advanced_search_no_results(self):
        parsed = _parse_advanced_search_text("No artifacts found for the given search parameters.")
        self.assertEqual(parsed, {"entities": [], "paging": {"count": 0}})

    def test_parse_metadata_dict(self):
        data = _parse_metadata_text('{"id":315278,"designation":"BM 01234"}')
        self.assertEqual(data["id"], 315278)
        self.assertEqual(data["designation"], "BM 01234")

    def test_parse_metadata_list(self):
        data = _parse_metadata_text('[{"id":315278,"designation":"BM 01234"}]')
        self.assertEqual(data["id"], 315278)

    def test_parse_metadata_invalid_json_raises(self):
        with self.assertRaises(MCPToolError):
            _parse_metadata_text("not-json")


if __name__ == "__main__":
    unittest.main()
