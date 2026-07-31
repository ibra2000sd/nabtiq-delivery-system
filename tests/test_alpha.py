from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects" / "alpha-corporate"
sys.path.insert(0, str(ROOT))

from studio.media import probe_video  # noqa: E402
from studio.providers import luma_video_payload, openai_image_payload  # noqa: E402


def run(*args, check=True):
    return subprocess.run(
        [str(arg) for arg in args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


class AlphaBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run(sys.executable, "scripts/build_site.py", PROJECT)
        cls.build = PROJECT / "build"

    def test_eight_localized_pages_are_generated(self):
        pages = [
            self.build / locale / route / "index.html"
            for locale in ("en", "ar")
            for route in ("about", "capabilities", "contact")
        ]
        pages += [self.build / "en" / "index.html", self.build / "ar" / "index.html"]
        self.assertTrue(all(path.is_file() for path in pages))
        self.assertEqual(len(pages), 8)

    def test_arabic_is_structurally_rtl_and_natural_copy_is_present(self):
        arabic = (self.build / "ar" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<html lang="ar" dir="rtl"', arabic)
        self.assertIn("مسارات معقدة. وجهة واحدة واضحة.", arabic)
        self.assertIn('href="/en/"', arabic)

    def test_english_has_localized_routes_and_seo(self):
        english = (self.build / "en" / "capabilities" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<html lang="en" dir="ltr"', english)
        self.assertIn('rel="canonical"', english)
        self.assertIn('hreflang="ar"', english)
        self.assertIn('type="application/ld+json"', english)
        self.assertIn('href="/ar/capabilities/"', english)

    def test_design_material_and_motion_contract_ship(self):
        css = (self.build / "assets" / "styles.css").read_text(encoding="utf-8")
        js = (self.build / "assets" / "app.js").read_text(encoding="utf-8")
        for marker in (
            "--glass-blur-nav",
            "--glass-blur-surface",
            "--glass-blur-deep",
            "--glass-blur-luminous",
            "prefers-reduced-motion",
            "@supports not",
        ):
            self.assertIn(marker, css)
        self.assertIn("IntersectionObserver", js)
        self.assertIn("--pointer-x", js)
        self.assertIn("syncHeroVideo", js)

    def test_home_ships_responsive_video_with_static_fallback(self):
        english = (self.build / "en" / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="hero__video"', english)
        self.assertIn('poster="/assets/hero-loop-desktop-poster.webp"', english)
        self.assertIn('src="/assets/hero-loop-desktop.webm"', english)
        self.assertIn('src="/assets/hero-loop-mobile.mp4"', english)
        self.assertIn("Questions answered before production.", english)

    def test_approved_video_renditions_decode_to_manifest_dimensions(self):
        manifest = json.loads((PROJECT / "video-manifest.json").read_text(encoding="utf-8"))
        slot = manifest["slots"][0]
        for rendition_name in ("desktop", "mobile"):
            rendition = slot[rendition_name]
            for source in rendition["sources"]:
                info = probe_video(PROJECT / source["src"])
                stream = info["streams"][0]
                self.assertEqual(stream["width"], rendition["width"])
                self.assertEqual(stream["height"], rendition["height"])
                self.assertAlmostEqual(
                    float(info["format"]["duration"]),
                    slot["duration_seconds"],
                    delta=0.2,
                )

    def test_all_shipped_renditions_decode(self):
        for path in sorted((self.build / "assets").glob("*.webp")):
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                image.load()
                self.assertGreater(image.width, 0)
                self.assertGreater(image.height, 0)

    def test_build_is_byte_deterministic(self):
        before = tree_hash(self.build)
        run(sys.executable, "scripts/build_site.py", PROJECT)
        after = tree_hash(self.build)
        self.assertEqual(before, after)

    def test_asset_probe_rejects_a_fake_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "project"
            shutil.copytree(PROJECT, fixture, ignore=shutil.ignore_patterns("build", "source"))
            (fixture / "assets" / "hero-mobile.webp").write_text("not an image", encoding="utf-8")
            result = run(sys.executable, "probes/asset_integrity_check.py", fixture, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot be decoded", result.stdout)

    def test_contract_probe_rejects_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "project"
            shutil.copytree(PROJECT, fixture, ignore=shutil.ignore_patterns("build", "source"))
            brand = fixture / "brand.json"
            text = brand.read_text(encoding="utf-8")
            text = text.replace('"short_name": "NABTIQ ATLAS",', '"short_name": "ONE",\n  "short_name": "TWO",')
            brand.write_text(text, encoding="utf-8")
            result = run(sys.executable, "probes/site_contract_check.py", fixture, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate key", result.stdout)

    def test_studio_probe_rejects_secret_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "alpha-corporate"
            shutil.copytree(PROJECT, fixture, ignore=shutil.ignore_patterns("build", "source"))
            plan_path = fixture / "generation-plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["providers"]["image"]["credential"] = "sk-this-is-a-secret-value-123456789"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            run(sys.executable, "scripts/seal.py", plan_path)
            result = run(sys.executable, "probes/studio_contract_check.py", fixture, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("secret-like", result.stdout)

    def test_video_probe_rejects_corrupt_rendition(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "alpha-corporate"
            shutil.copytree(PROJECT, fixture, ignore=shutil.ignore_patterns("build", "source"))
            (fixture / "assets" / "hero-loop-mobile.webm").write_text("not video", encoding="utf-8")
            result = run(sys.executable, "probes/video_asset_check.py", fixture, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot be decoded", result.stdout)

    def test_provider_payloads_are_current_and_guard_loop_constraints(self):
        image = openai_image_payload(prompt="A restrained corporate hero")
        self.assertEqual(image["model"], "gpt-image-2-2026-04-21")
        self.assertNotIn("background", image)  # intentionally omitted → default opaque; only "transparent" is unsupported
        video = luma_video_payload(prompt="Subtle forward drift")
        self.assertEqual(video["model"], "ray-3.2")
        self.assertEqual(video["type"], "video")
        with self.assertRaises(ValueError):
            luma_video_payload(prompt="Bad loop", duration="10s", loop=True)

    def test_media_generation_defaults_to_keyless_dry_run(self):
        image = run(
            sys.executable,
            "scripts/media_pipeline.py",
            "image",
            PROJECT,
            "home.hero",
        )
        self.assertIn("DRY RUN", image.stdout)
        self.assertIn("no key read", image.stdout)
        video = run(
            sys.executable,
            "scripts/media_pipeline.py",
            "video",
            PROJECT,
            "home.hero.motion",
        )
        self.assertIn("<base64 omitted>", video.stdout)

    def test_client_intake_is_hashed_without_copying_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "alpha-corporate"
            inputs = Path(tmp) / "inputs"
            shutil.copytree(PROJECT, fixture, ignore=shutil.ignore_patterns("build", "source"))
            inputs.mkdir()
            (inputs / "brief.txt").write_text("Verified client brief.", encoding="utf-8")
            run(sys.executable, "scripts/intake_files.py", fixture, inputs)
            inventory = json.loads((fixture / "source-inventory.json").read_text(encoding="utf-8"))
            self.assertEqual(inventory["files"][0]["source_path"], "brief.txt")
            self.assertEqual(inventory["files"][0]["extraction"], "extracted")
            self.assertEqual(inventory["files"][0]["review_status"], "unreviewed")
            self.assertFalse((fixture / "brief.txt").exists())

    def test_current_site_crawler_is_dry_run_by_default(self):
        result = run(
            sys.executable,
            "scripts/crawl_site.py",
            PROJECT,
            "https://example.com/",
        )
        plan = json.loads(result.stdout)
        self.assertEqual(plan["mode"], "dry-run")
        self.assertEqual(plan["network_requests"], 0)
        self.assertIn("--execute", plan["next"])

    def test_default_locale_can_own_the_domain_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "alpha-corporate"
            shutil.copytree(PROJECT, fixture, ignore=shutil.ignore_patterns("build", "source"))
            sitemap_path = fixture / "site-map.json"
            sitemap = json.loads(sitemap_path.read_text(encoding="utf-8"))
            sitemap["routing"] = {
                "mode": "default-locale-root",
                "root_behavior": "default-locale",
            }
            sitemap["pages"][0]["paths"]["en"] = "/"
            for page in sitemap["pages"][1:]:
                page["paths"]["en"] = f"/{page['id']}/"
            sitemap_path.write_text(json.dumps(sitemap), encoding="utf-8")
            run(sys.executable, "scripts/seal.py", sitemap_path)
            for page_path in (fixture / "pages").glob("*.content.json"):
                page_path.write_text(
                    page_path.read_text(encoding="utf-8").replace('"/en/', '"/'),
                    encoding="utf-8",
                )
                run(sys.executable, "scripts/seal.py", page_path)
            contract = run(sys.executable, "probes/site_contract_check.py", fixture, check=False)
            self.assertEqual(contract.returncode, 0, contract.stdout)
            run(sys.executable, "scripts/build_site.py", fixture)
            root_page = (fixture / "build" / "index.html").read_text(encoding="utf-8")
            self.assertIn('<html lang="en" dir="ltr"', root_page)
            self.assertNotIn("Choose your language", root_page)

    def test_generated_json_ld_is_valid(self):
        page = (self.build / "en" / "index.html").read_text(encoding="utf-8")
        start = page.index('<script type="application/ld+json">') + len('<script type="application/ld+json">')
        end = page.index("</script>", start)
        data = json.loads(page[start:end])
        self.assertEqual(data["@type"], "Organization")
        self.assertEqual(data["name"], "Nabtiq Atlas")


if __name__ == "__main__":
    unittest.main()
