#!/usr/bin/env python3
"""build_site.py — minimal `web-implementation` build (Wave 4).

Renders a project's content + image-manifest + profile into build/index.html:
  * correct locale <html dir/lang> (RTL via CSS logical properties, not hardcoded left/right)
  * hero from the home.hero slot as a RASTER <img> (no SVG-before-raster flash)
  * consent-gated analytics (commented placeholder — never loads before consent)
Use --flaw svg-flash to simulate a BROKEN implementation (SVG placeholder that swaps to raster) so the
first_paint_probe can prove it catches the flash. This is a tiny renderer for the demo, not a framework.

Usage: python3 scripts/build_site.py <project-dir> [--flaw svg-flash]
"""
import sys, json, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "probes"))
from lib_common import load_json  # noqa

def esc(s): return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def main():
    proj = Path(sys.argv[1]); flaw = "--flaw" in sys.argv and sys.argv[sys.argv.index("--flaw")+1]
    profile = load_json(proj/"profile.json") if (proj/"profile.json").exists() else {}
    manifest = load_json(proj/"image-manifest.json") if (proj/"image-manifest.json").exists() else {"slots": []}
    lang = "ar" if profile.get("primary_language") == "ar" else "en"
    dir_ = "rtl" if lang == "ar" else "ltr"
    hero = next((s for s in manifest.get("slots", []) if s.get("slot_id") == "home.hero"), None)

    build = proj/"build"; assets = build/"assets"
    if build.exists(): shutil.rmtree(build)
    assets.mkdir(parents=True)
    # copy real assets
    if (proj/"assets").is_dir():
        for f in (proj/"assets").glob("*"):
            if f.is_file(): shutil.copy(f, assets/f.name)

    if flaw == "svg-flash":
        # BROKEN: an SVG placeholder loads first, then JS swaps to raster -> first-paint flash + an SVG request
        (assets/"hero-placeholder.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="9"><rect width="16" height="9" fill="#ccc"/></svg>')
        hero_html = ('<img id="hero" src="assets/hero-placeholder.svg" alt="hero" width="1440" height="810">'
                     '<script>addEventListener("load",()=>{document.getElementById("hero").src="assets/home-hero.avif"});</script>')
    else:
        src = (hero or {}).get("asset", "assets/home-hero.avif")
        alt = esc((hero or {}).get(f"alt_{lang}", "hero"))
        hero_html = f'<img id="hero" src="{src}" alt="{alt}" width="1440" height="810" fetchpriority="high">'

    html = f"""<!doctype html>
<html lang="{lang}" dir="{dir_}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nabtiq demo — {esc(profile.get('project',''))}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ margin:0; font-family: system-ui, sans-serif; }}
  /* direction via LOGICAL properties, not left/right */
  .wrap {{ padding-inline: 1.5rem; padding-block: 2rem; max-inline-size: 72rem; margin-inline: auto; }}
  #hero {{ inline-size:100%; block-size:auto; aspect-ratio:16/9; object-fit:cover; }}
</style>
</head>
<body>
  <main class="wrap">
    {hero_html}
    <h1>Sesame</h1>
    <p>Premium sesame for food manufacturers and traders, shipped with full export documentation.</p>
  </main>
  <!-- analytics is CONSENT-GATED: the tag is injected only after the visitor accepts (PDPL consent-first). -->
</body>
</html>
"""
    (build/"index.html").write_text(html, encoding="utf-8")
    print(f"built {build/'index.html'} (lang={lang} dir={dir_}{' FLAW=svg-flash' if flaw=='svg-flash' else ''})")

if __name__ == "__main__":
    main()
