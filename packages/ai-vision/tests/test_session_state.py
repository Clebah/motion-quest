"""Tests for the in-memory session character store (SPEC-003 RF-01, §8.6)."""
from __future__ import annotations

import asyncio
import shutil
import unittest
from pathlib import Path

from src.adapters.inbound.web import session_state
from src.adapters.inbound.web.session_state import SessionCharacterStore
from src.adapters.outbound.mock_adapters import MockImageProcessorAdapter

_SAMPLE_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00"
    b"\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
)


class TestSessionCharacterStore(unittest.TestCase):

    def setUp(self):
        self.store = SessionCharacterStore(MockImageProcessorAdapter())

    def tearDown(self):
        if session_state.SESSION_ROOT.exists():
            shutil.rmtree(session_state.SESSION_ROOT)

    def test_register_valid_character_appears_in_list(self):
        summary = asyncio.run(self.store.register(
            name="Pedro",
            description="Explorador",
            headshot_files=[("head.png", _SAMPLE_PNG_BYTES)],
            fullbody_files=[("body.png", _SAMPLE_PNG_BYTES)],
        ))

        self.assertEqual(summary.name, "Pedro")
        self.assertTrue(summary.headshotPreviewUrl.startswith("/media/"))
        self.assertTrue(summary.fullbodyPreviewUrl.startswith("/media/"))

        listed_ids = [c.id for c in self.store.list()]
        self.assertIn(summary.id, listed_ids)

    def test_register_without_fullbody_photo_raises_value_error(self):
        with self.assertRaises(ValueError):
            asyncio.run(self.store.register(
                name="Ana",
                description="Aventureira",
                headshot_files=[("head.png", _SAMPLE_PNG_BYTES)],
                fullbody_files=[],
            ))

    def test_register_rejects_unsupported_file_extension(self):
        with self.assertRaises(ValueError):
            asyncio.run(self.store.register(
                name="Carlos",
                description="Mago",
                headshot_files=[("head.gif", _SAMPLE_PNG_BYTES)],
                fullbody_files=[("body.png", _SAMPLE_PNG_BYTES)],
            ))

    def test_register_rejects_a_sixth_photo_of_the_same_type(self):
        six_headshots = [(f"head_{i}.png", _SAMPLE_PNG_BYTES) for i in range(6)]
        with self.assertRaises(ValueError):
            asyncio.run(self.store.register(
                name="Bea",
                description="Cientista",
                headshot_files=six_headshots,
                fullbody_files=[("body.png", _SAMPLE_PNG_BYTES)],
            ))

    def test_remove_character(self):
        summary = asyncio.run(self.store.register(
            name="Zeca",
            description="Pescador",
            headshot_files=[("head.png", _SAMPLE_PNG_BYTES)],
            fullbody_files=[("body.png", _SAMPLE_PNG_BYTES)],
        ))

        self.assertTrue(self.store.remove(summary.id))
        self.assertNotIn(summary.id, [c.id for c in self.store.list()])
        self.assertFalse(self.store.remove(summary.id))

    def test_get_many_returns_only_matching_registered_characters(self):
        summary = asyncio.run(self.store.register(
            name="Lia",
            description="Piloto",
            headshot_files=[("head.png", _SAMPLE_PNG_BYTES)],
            fullbody_files=[("body.png", _SAMPLE_PNG_BYTES)],
        ))

        found = self.store.get_many([summary.id, "does_not_exist"])
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].id, summary.id)


if __name__ == "__main__":
    unittest.main()
