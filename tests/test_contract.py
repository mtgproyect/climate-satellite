from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MANIFEST = DOCS / "manifiesto.json"


class SatelliteContractTests(unittest.TestCase):
    def test_manifest_is_valid(self) -> None:
        value = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(value["schema_version"], 1)
        self.assertTrue(value["enabled"])
        self.assertEqual(
            value["storage"]["mode"],
            "remote_urls_only",
        )
        self.assertEqual(
            value["storage"]["stored_image_count"],
            0,
        )

    def test_repository_contains_no_satellite_images(self) -> None:
        extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
        images = [
            path
            for path in ROOT.rglob("*")
            if path.is_file() and path.suffix.lower() in extensions
        ]
        self.assertEqual(images, [])

    def test_frame_urls_are_remote(self) -> None:
        value = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for frame in value.get("frames", []):
            self.assertTrue(
                frame["url"].startswith(
                    "https://estaticos.smn.gob.ar/"
                )
            )


if __name__ == "__main__":
    unittest.main()
