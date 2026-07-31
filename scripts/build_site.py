#!/usr/bin/env python3
"""Build a bilingual, token-driven Corporate/Brochure website.

The generator deliberately has no runtime framework dependency. It reads the
project contracts, renders every locale/page, copies approved media renditions,
and emits a portable static build.

Usage:
    python3 scripts/build_site.py projects/<project>
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "site_templates" / "corporate-brochure"


class BuildError(RuntimeError):
    """A project contract cannot be rendered safely."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BuildError(f"missing required artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BuildError(f"invalid JSON in {path}: {exc}") from exc


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def json_for_html(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def token_name(path: tuple[str, ...]) -> str:
    return "--" + "-".join(re.sub(r"[^a-z0-9-]", "-", part.lower()) for part in path)


def token_ref(value: Any) -> str:
    if not isinstance(value, str):
        return str(value)
    match = re.fullmatch(r"\{([^}]+)\}", value)
    if not match:
        return value
    return f"var({token_name(tuple(match.group(1).split('.')))})"


def flatten_tokens(node: dict[str, Any], prefix: tuple[str, ...] = ()) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in node.items():
        if key.startswith("$"):
            continue
        path = prefix + (key,)
        if isinstance(value, dict) and "$value" in value:
            result[token_name(path)] = token_ref(value["$value"])
        elif isinstance(value, dict):
            result.update(flatten_tokens(value, path))
    return result


def css_variables(tokens: dict[str, Any]) -> str:
    base = flatten_tokens(tokens.get("tokens", {}))
    semantic = tokens.get("semantic", {})
    light = flatten_tokens(semantic.get("light", {}), ("semantic",))
    dark = flatten_tokens(semantic.get("dark", {}), ("semantic",))

    def body(mapping: dict[str, str]) -> str:
        return "\n".join(f"  {name}: {value};" for name, value in sorted(mapping.items()))

    return (
        "/* Generated from design-tokens.json. Do not edit build output. */\n"
        f":root,\n[data-theme=\"light\"] {{\n{body({**base, **light})}\n}}\n\n"
        f"[data-theme=\"dark\"] {{\n{body(dark)}\n}}\n"
    )


def route_output(build: Path, route: str) -> Path:
    clean = route.strip("/")
    return build / clean / "index.html" if clean else build / "index.html"


def media_slot(manifest: dict[str, Any], slot_id: str) -> dict[str, Any]:
    for slot in manifest.get("slots", []):
        if slot.get("slot_id") == slot_id:
            return slot
    raise BuildError(f"media slot {slot_id!r} is not declared")


def optional_slot(manifest: dict[str, Any] | None, slot_id: str | None) -> dict[str, Any] | None:
    if not manifest or not slot_id:
        return None
    for item in manifest.get("slots", []):
        if item.get("slot_id") == slot_id:
            return item
    raise BuildError(f"media slot {slot_id!r} is not declared")


def local_text(block: dict[str, Any], key: str, default: str = "") -> str:
    value = block.get(key, default)
    return str(value) if value is not None else default


def render_button(cta: dict[str, Any] | None, class_name: str = "button") -> str:
    if not cta:
        return ""
    return (
        f'<a class="{esc(class_name)}" href="{esc(cta.get("href", "#"))}">'
        f'<span>{esc(cta.get("label", ""))}</span>'
        '<svg aria-hidden="true" viewBox="0 0 20 20"><path d="M4 10h11m-4-4 4 4-4 4"/></svg>'
        "</a>"
    )


def render_hero(
    block: dict[str, Any],
    locale: str,
    manifest: dict[str, Any],
    video_manifest: dict[str, Any] | None,
    compact: bool,
) -> str:
    slot = media_slot(manifest, block.get("asset_slot", "home.hero"))
    renditions = slot.get("renditions", {})
    desktop = renditions.get("desktop", {})
    mobile = renditions.get("mobile", {})
    alt = slot.get(f"alt_{locale}", "")
    hero_class = "hero hero--compact" if compact else "hero"
    video = optional_slot(video_manifest, block.get("video_slot"))
    video_markup = ""
    if video and video.get("status") == "approved" and not compact:
        desktop_video = video.get("desktop", {})
        mobile_video = video.get("mobile", {})
        source_markup = []
        for source in mobile_video.get("sources", []):
            source_markup.append(
                f'<source media="(max-width: 47.99rem)" src="/{esc(source.get("src"))}" '
                f'type="{esc(source.get("mime"))}">'
            )
        for source in desktop_video.get("sources", []):
            source_markup.append(
                f'<source src="/{esc(source.get("src"))}" type="{esc(source.get("mime"))}">'
            )
        video_markup = (
            f'<video class="hero__video" poster="/{esc(desktop_video.get("poster"))}" '
            'muted loop playsinline preload="metadata" data-hero-video aria-hidden="true">'
            f'{"".join(source_markup)}</video>'
        )
    actions = (
        render_button(block.get("primary_cta"))
        + render_button(block.get("secondary_cta"), "button button--quiet")
    )
    return f"""
<section class="{hero_class}" aria-labelledby="hero-title">
  {video_markup}
  <picture class="hero__media" data-hero-poster>
    <source media="(max-width: 47.99rem)" srcset="/{esc(mobile.get('src'))}">
    <img src="/{esc(desktop.get('src'))}" width="{esc(desktop.get('width'))}"
         height="{esc(desktop.get('height'))}" alt="{esc(alt)}"
         fetchpriority="high" decoding="async">
  </picture>
  <div class="hero__veil" aria-hidden="true"></div>
  <div class="hero__orbit hero__orbit--one" aria-hidden="true"></div>
  <div class="hero__orbit hero__orbit--two" aria-hidden="true"></div>
  <div class="shell hero__layout">
    <div class="glass glass--deep hero__panel" data-reveal>
      <p class="eyebrow">{esc(block.get("eyebrow", ""))}</p>
      <h1 id="hero-title">{esc(block.get("heading", ""))}</h1>
      <p class="hero__lede">{esc(block.get("body", ""))}</p>
      <div class="hero__actions">{actions}</div>
      <p class="hero__note">{esc(block.get("note", ""))}</p>
    </div>
  </div>
  <a class="hero__scroll" href="#content">
    <span>{esc(block.get("scroll_label", ""))}</span><i aria-hidden="true"></i>
  </a>
</section>"""


def section_heading(block: dict[str, Any]) -> str:
    eyebrow = (
        f'<p class="eyebrow">{esc(block.get("eyebrow"))}</p>'
        if block.get("eyebrow")
        else ""
    )
    body = (
        f'<p class="section-heading__body">{esc(block.get("body"))}</p>'
        if block.get("body")
        else ""
    )
    return (
        '<header class="section-heading" data-reveal>'
        f'{eyebrow}<h2>{esc(block.get("heading", ""))}</h2>{body}</header>'
    )


def render_cards(block: dict[str, Any]) -> str:
    cards = []
    for index, item in enumerate(block.get("items", []), start=1):
        points = "".join(f"<li>{esc(point)}</li>" for point in item.get("points", []))
        cards.append(
            f"""
<article class="glass glass--surface feature-card" data-reveal>
  <span class="feature-card__number" aria-hidden="true">{index:02d}</span>
  <h3>{esc(item.get("heading", ""))}</h3>
  <p>{esc(item.get("body", ""))}</p>
  <ul>{points}</ul>
</article>"""
        )
    return (
        f'<section class="section section--tint"><div class="shell">{section_heading(block)}'
        f'<div class="card-grid">{"".join(cards)}</div></div></section>'
    )


def render_metrics(block: dict[str, Any]) -> str:
    items = "".join(
        f"""
<div class="metric" data-reveal>
  <strong>{esc(item.get("value", ""))}</strong>
  <span>{esc(item.get("label", ""))}</span>
</div>"""
        for item in block.get("items", [])
    )
    return (
        '<section class="section section--compact"><div class="shell">'
        f'<div class="glass glass--surface metrics">{items}</div></div></section>'
    )


def render_split(block: dict[str, Any]) -> str:
    points = "".join(
        f'<li data-reveal><span aria-hidden="true"></span><p>{esc(point)}</p></li>'
        for point in block.get("points", [])
    )
    return f"""
<section class="section">
  <div class="shell split">
    <div>{section_heading(block)}</div>
    <div class="glass glass--surface split__panel" data-reveal>
      <p class="split__statement">{esc(block.get("statement", ""))}</p>
      <ul class="check-list">{points}</ul>
    </div>
  </div>
</section>"""


def render_steps(block: dict[str, Any]) -> str:
    steps = []
    for index, item in enumerate(block.get("items", []), start=1):
        steps.append(
            f"""
<li data-reveal>
  <span class="steps__index">{index:02d}</span>
  <div><h3>{esc(item.get("heading", ""))}</h3><p>{esc(item.get("body", ""))}</p></div>
</li>"""
        )
    return (
        f'<section class="section section--tint"><div class="shell">{section_heading(block)}'
        f'<ol class="steps">{"".join(steps)}</ol></div></section>'
    )


def render_route(block: dict[str, Any]) -> str:
    nodes = []
    for index, item in enumerate(block.get("items", []), start=1):
        nodes.append(
            f"""
<li class="route__node" data-reveal>
  <span>{index:02d}</span><div><strong>{esc(item.get("heading", ""))}</strong>
  <p>{esc(item.get("body", ""))}</p></div>
</li>"""
        )
    return f"""
<section class="section section--dark">
  <div class="shell route">
    {section_heading(block)}
    <div class="route__canvas glass glass--deep">
      <div class="route__line" aria-hidden="true"></div>
      <ol>{"".join(nodes)}</ol>
    </div>
  </div>
</section>"""


def render_cta(block: dict[str, Any]) -> str:
    return f"""
<section class="section section--cta">
  <div class="shell">
    <div class="glass glass--luminous cta-panel" data-reveal>
      <p class="eyebrow">{esc(block.get("eyebrow", ""))}</p>
      <h2>{esc(block.get("heading", ""))}</h2>
      <p>{esc(block.get("body", ""))}</p>
      {render_button(block.get("primary_cta"))}
    </div>
  </div>
</section>"""


def render_contact(block: dict[str, Any]) -> str:
    channels = []
    for item in block.get("channels", []):
        channels.append(
            f"""
<a class="glass glass--surface contact-card" href="{esc(item.get("href", "#"))}" data-reveal>
  <span>{esc(item.get("label", ""))}</span>
  <strong>{esc(item.get("value", ""))}</strong>
</a>"""
        )
    return f"""
<section class="section">
  <div class="shell contact-layout">
    <div>{section_heading(block)}</div>
    <div class="contact-grid">{"".join(channels)}</div>
  </div>
</section>"""


def render_faq(block: dict[str, Any]) -> str:
    items = []
    for item in block.get("items", []):
        items.append(
            f"""
<details class="glass glass--surface faq-item" data-reveal>
  <summary>{esc(item.get("question", ""))}<span aria-hidden="true"></span></summary>
  <div><p>{esc(item.get("answer", ""))}</p></div>
</details>"""
        )
    return f"""
<section class="section section--tint">
  <div class="shell faq">
    {section_heading(block)}
    <div class="faq__list">{"".join(items)}</div>
  </div>
</section>"""


def render_gallery(block: dict[str, Any]) -> str:
    items = []
    for item in block.get("items", []):
        items.append(
            f"""
<figure class="gallery-card glass glass--surface" data-reveal>
  <img src="/{esc(item.get("src"))}" width="{esc(item.get("width"))}"
       height="{esc(item.get("height"))}" alt="{esc(item.get("alt"))}"
       loading="lazy" decoding="async">
  <figcaption><strong>{esc(item.get("heading", ""))}</strong>
  <span>{esc(item.get("body", ""))}</span></figcaption>
</figure>"""
        )
    return f"""
<section class="section">
  <div class="shell">
    {section_heading(block)}
    <div class="gallery-grid">{"".join(items)}</div>
  </div>
</section>"""


def render_before_after(block: dict[str, Any]) -> str:
    before = block.get("before", {})
    after = block.get("after", {})
    return f"""
<section class="section section--dark">
  <div class="shell">
    {section_heading(block)}
    <div class="before-after">
      <figure class="glass glass--deep" data-reveal>
        <img src="/{esc(before.get("src"))}" width="{esc(before.get("width"))}"
             height="{esc(before.get("height"))}" alt="{esc(before.get("alt"))}"
             loading="lazy" decoding="async">
        <figcaption>{esc(before.get("label", ""))}</figcaption>
      </figure>
      <figure class="glass glass--deep" data-reveal>
        <img src="/{esc(after.get("src"))}" width="{esc(after.get("width"))}"
             height="{esc(after.get("height"))}" alt="{esc(after.get("alt"))}"
             loading="lazy" decoding="async">
        <figcaption>{esc(after.get("label", ""))}</figcaption>
      </figure>
    </div>
  </div>
</section>"""


def render_logo_cloud(block: dict[str, Any]) -> str:
    items = "".join(
        f'<li class="glass glass--surface" data-reveal>{esc(item.get("name", ""))}</li>'
        for item in block.get("items", [])
    )
    return f"""
<section class="section section--compact">
  <div class="shell">
    {section_heading(block)}
    <ul class="logo-cloud">{"".join(items)}</ul>
  </div>
</section>"""


def render_lead_form(block: dict[str, Any]) -> str:
    action = str(block.get("action", ""))
    if not action.startswith("https://"):
        raise BuildError("lead_form action must be an approved https endpoint")
    fields = []
    for field in block.get("fields", []):
        field_type = field.get("type", "text")
        required = " required" if field.get("required") else ""
        if field_type == "textarea":
            control = (
                f'<textarea id="{esc(field.get("id"))}" name="{esc(field.get("name"))}"'
                f'{required}></textarea>'
            )
        else:
            control = (
                f'<input id="{esc(field.get("id"))}" name="{esc(field.get("name"))}" '
                f'type="{esc(field_type)}"{required}>'
            )
        fields.append(
            f'<label><span>{esc(field.get("label"))}</span>{control}</label>'
        )
    return f"""
<section class="section">
  <div class="shell lead-layout">
    <div>{section_heading(block)}</div>
    <form class="glass glass--surface lead-form" action="{esc(action)}" method="post"
          data-lead-form>
      {"".join(fields)}
      <label class="lead-form__consent">
        <input type="checkbox" name="privacy_consent" required>
        <span>{esc(block.get("consent_label", ""))}</span>
      </label>
      <button class="button" type="submit"><span>{esc(block.get("submit_label", ""))}</span></button>
    </form>
  </div>
</section>"""


RENDERERS = {
    "cards": render_cards,
    "metrics": render_metrics,
    "split": render_split,
    "steps": render_steps,
    "route": render_route,
    "cta": render_cta,
    "contact": render_contact,
    "faq": render_faq,
    "gallery": render_gallery,
    "before_after": render_before_after,
    "logo_cloud": render_logo_cloud,
    "lead_form": render_lead_form,
}


def render_page(
    project: Path,
    page_spec: dict[str, Any],
    page: dict[str, Any],
    locale: str,
    sitemap: dict[str, Any],
    brand: dict[str, Any],
    manifest: dict[str, Any],
    video_manifest: dict[str, Any] | None,
) -> str:
    loc = page.get("locales", {}).get(locale)
    if not loc:
        raise BuildError(f"{page_spec['id']} has no locale {locale}")
    locale_meta = next(item for item in sitemap["locales"] if item["code"] == locale)
    direction = locale_meta["dir"]
    other_locale = next(item["code"] for item in sitemap["locales"] if item["code"] != locale)
    current_path = page_spec["paths"][locale]
    other_path = page_spec["paths"][other_locale]
    site_url = brand["website"].rstrip("/")
    canonical = f"{site_url}{current_path}"

    page_lookup = {item["id"]: item for item in sitemap["pages"]}
    nav = []
    for page_id in sitemap.get("navigation", []):
        target = page_lookup[page_id]
        target_doc = load_json(project / target["source"])
        label = target_doc["locales"][locale]["nav_label"]
        active = ' aria-current="page"' if page_id == page_spec["id"] else ""
        nav.append(
            f'<a href="{esc(target["paths"][locale])}"{active}>{esc(label)}</a>'
        )

    blocks = loc.get("blocks", [])
    if not blocks or blocks[0].get("type") != "hero":
        raise BuildError(f"{page_spec['id']}:{locale} must begin with a hero block")
    hero = render_hero(
        blocks[0],
        locale,
        manifest,
        video_manifest,
        compact=page_spec["id"] != "home",
    )
    sections = []
    for block in blocks[1:]:
        renderer = RENDERERS.get(block.get("type"))
        if not renderer:
            raise BuildError(
                f"unsupported block type {block.get('type')!r} in {page_spec['id']}:{locale}"
            )
        sections.append(renderer(block))

    seo = loc.get("seo", {})
    social = media_slot(manifest, "home.hero").get("renditions", {}).get("social", {})
    ld_json = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": brand["name"][locale],
        "url": brand["website"],
        "email": brand["contact"]["email"],
        "description": seo.get("description", ""),
    }
    theme_labels = locale_meta["ui"]
    brand_name = brand["name"][locale]
    year = brand.get("copyright_year", 2026)
    return f"""<!doctype html>
<html lang="{esc(locale)}" dir="{esc(direction)}" data-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <meta name="theme-color" content="#071621">
  <title>{esc(seo.get("title", brand_name))}</title>
  <meta name="description" content="{esc(seo.get("description", ""))}">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="alternate" hreflang="{esc(locale)}" href="{esc(canonical)}">
  <link rel="alternate" hreflang="{esc(other_locale)}" href="{esc(site_url + other_path)}">
  <link rel="alternate" hreflang="x-default" href="{esc(site_url + page_spec["paths"][sitemap["default_locale"]])}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{esc(seo.get("title", brand_name))}">
  <meta property="og:description" content="{esc(seo.get("description", ""))}">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:image" content="{esc(site_url + "/" + social.get("src", ""))}">
  <meta property="og:locale" content="{esc(locale_meta.get("og_locale", locale))}">
  <link rel="stylesheet" href="/assets/styles.css">
  <script type="application/ld+json">{json_for_html(ld_json)}</script>
  <script src="/assets/app.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#content">{esc(theme_labels["skip"])}</a>
  <header class="site-header" data-header>
    <div class="shell site-header__inner glass glass--nav">
      <a class="brand" href="{esc(page_lookup["home"]["paths"][locale])}" aria-label="{esc(brand_name)}">
        <span class="brand__mark" aria-hidden="true"><i></i><i></i></span>
        <span><strong>{esc(brand_name)}</strong><small>{esc(brand["descriptor"][locale])}</small></span>
      </a>
      <nav class="site-nav" id="site-nav" aria-label="{esc(theme_labels["nav"])}" data-nav>
        {"".join(nav)}
      </nav>
      <div class="site-actions">
        <a class="locale-switch" href="{esc(other_path)}" lang="{esc(other_locale)}"
           hreflang="{esc(other_locale)}">{esc(locale_meta["switch_label"])}</a>
        <button class="icon-button" type="button" data-theme-toggle
                aria-label="{esc(theme_labels["theme"])}" aria-pressed="true">
          <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 3v2m0 14v2M3 12h2m14 0h2M5.6 5.6 7 7m10 10 1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4"/><circle cx="12" cy="12" r="4"/></svg>
        </button>
        <button class="icon-button menu-button" type="button" data-menu-toggle
                aria-controls="site-nav" aria-expanded="false" aria-label="{esc(theme_labels["menu"])}">
          <span></span><span></span>
        </button>
      </div>
    </div>
  </header>
  {hero}
  <main id="content">{"".join(sections)}</main>
  <footer class="site-footer">
    <div class="shell site-footer__grid">
      <div>
        <a class="brand brand--footer" href="{esc(page_lookup["home"]["paths"][locale])}">
          <span class="brand__mark" aria-hidden="true"><i></i><i></i></span>
          <strong>{esc(brand_name)}</strong>
        </a>
        <p>{esc(brand["footer_note"][locale])}</p>
      </div>
      <nav aria-label="{esc(theme_labels["footer_nav"])}">{"".join(nav)}</nav>
      <div class="site-footer__meta">
        <p>© {esc(year)} {esc(brand_name)}.</p>
        <a href="https://nabtiq.com" rel="noopener">{esc(theme_labels["credit"])}</a>
      </div>
    </div>
  </footer>
</body>
</html>
"""


def root_chooser(brand: dict[str, Any], sitemap: dict[str, Any]) -> str:
    en = sitemap["pages"][0]["paths"]["en"]
    ar = sitemap["pages"][0]["paths"]["ar"]
    return f"""<!doctype html>
<html lang="en" dir="ltr" data-theme="dark">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{esc(brand["name"]["en"])}</title>
  <meta name="robots" content="noindex">
  <link rel="stylesheet" href="/assets/styles.css">
</head>
<body class="language-page">
  <main class="glass glass--deep language-card">
    <span class="brand__mark" aria-hidden="true"><i></i><i></i></span>
    <h1>{esc(brand["name"]["en"])}</h1>
    <p>Choose your language · اختر لغتك</p>
    <div><a class="button" href="{esc(en)}">English</a><a class="button button--quiet" href="{esc(ar)}">العربية</a></div>
  </main>
</body>
</html>"""


def build(project: Path) -> Path:
    profile = load_json(project / "profile.json")
    if profile.get("profile") != "corporate-brochure":
        raise BuildError("this Alpha renderer supports profile=corporate-brochure only")
    brand = load_json(project / "brand.json")
    sitemap = load_json(project / "site-map.json")
    tokens = load_json(project / "design-tokens.json")
    manifest = load_json(project / "image-manifest.json")
    video_manifest_path = project / "video-manifest.json"
    video_manifest = load_json(video_manifest_path) if video_manifest_path.exists() else None

    build_dir = project / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    (build_dir / "assets").mkdir(parents=True)

    for source in (project / "assets").rglob("*"):
        if source.is_file():
            relative = source.relative_to(project / "assets")
            if relative.parts and relative.parts[0] == "source":
                continue
            destination = build_dir / "assets" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    css = css_variables(tokens) + "\n" + (TEMPLATE_ROOT / "styles.css").read_text(encoding="utf-8")
    (build_dir / "assets" / "styles.css").write_text(css, encoding="utf-8")
    shutil.copy2(TEMPLATE_ROOT / "app.js", build_dir / "assets" / "app.js")

    page_count = 0
    for page_spec in sitemap["pages"]:
        page = load_json(project / page_spec["source"])
        for locale in [item["code"] for item in sitemap["locales"]]:
            output = route_output(build_dir, page_spec["paths"][locale])
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                render_page(
                    project,
                    page_spec,
                    page,
                    locale,
                    sitemap,
                    brand,
                    manifest,
                    video_manifest,
                ),
                encoding="utf-8",
            )
            page_count += 1

    routing = sitemap.get(
        "routing",
        {"mode": "locale-prefix-all", "root_behavior": "chooser"},
    )
    if routing.get("root_behavior") == "chooser":
        (build_dir / "index.html").write_text(root_chooser(brand, sitemap), encoding="utf-8")
    elif not (build_dir / "index.html").exists():
        raise BuildError(
            "root_behavior=default-locale requires the default-locale home route to be /"
        )
    base_url = brand["website"].rstrip("/")
    urls = [
        f"{base_url}{page['paths'][locale['code']]}"
        for page in sitemap["pages"]
        for locale in sitemap["locales"]
    ]
    sitemap_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{esc(url)}</loc></url>\n" for url in urls)
        + "</urlset>\n"
    )
    (build_dir / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")
    (build_dir / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n", encoding="utf-8"
    )
    (build_dir / "site.webmanifest").write_text(
        json.dumps(
            {
                "name": brand["name"][sitemap["default_locale"]],
                "short_name": brand["short_name"],
                "start_url": sitemap["pages"][0]["paths"][sitemap["default_locale"]],
                "display": "standalone",
                "background_color": "#071621",
                "theme_color": "#071621",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    root_label = "root chooser" if routing.get("root_behavior") == "chooser" else "default-locale root"
    print(f"built {page_count} localized pages + {root_label} in {build_dir}")
    return build_dir


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    try:
        build(args.project.resolve())
    except BuildError as exc:
        print(f"BUILD BLOCKED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
