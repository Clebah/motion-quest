"""Tests for the 5 ready-made script templates (SPEC-003 RF-02, §4)."""
from __future__ import annotations

import unittest

from src.adapters.inbound.web.templates_catalog import get_template_by_id, get_templates


class TestTemplatesCatalog(unittest.TestCase):

    EXPECTED_GENRES = {"Terror", "Ficção Científica", "Drama", "Romance", "Comédia"}

    def test_exactly_five_templates(self):
        self.assertEqual(len(get_templates()), 5)

    def test_covers_the_five_required_genres(self):
        genres = {t["genre"] for t in get_templates()}
        self.assertEqual(genres, self.EXPECTED_GENRES)

    def test_ids_are_unique(self):
        ids = [t["id"] for t in get_templates()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_template_has_non_empty_required_fields(self):
        for template in get_templates():
            for field in ("id", "genre", "title", "synopsis", "promptText"):
                self.assertTrue(
                    template.get(field, "").strip(),
                    f"template {template.get('id')!r} has an empty '{field}'",
                )
            self.assertGreaterEqual(
                len(template["promptText"]), 20,
                f"template {template['id']!r} promptText is too short to seed a storyboard",
            )

    def test_get_template_by_id_found_and_not_found(self):
        terror = get_template_by_id("terror")
        self.assertIsNotNone(terror)
        self.assertEqual(terror["genre"], "Terror")

        self.assertIsNone(get_template_by_id("does_not_exist"))


if __name__ == "__main__":
    unittest.main()
