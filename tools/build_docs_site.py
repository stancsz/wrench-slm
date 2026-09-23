"""Build the curated static documentation only. No runtime or provider calls."""
from __future__ import annotations

import argparse
import html
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "index": ("Wrench | Affordable AI for the rest of us", "Home"),
    "getting-started": ("Getting started | Wrench", "Getting started"),
    "how-it-works": ("How it works | Wrench", "How it works"),
    "model-story": ("How Wrench was built | Wrench", "How we built it"),
    "integrations": ("Coding clients | Wrench", "Coding clients"),
    "evidence": ("Evidence and progress | Wrench", "Evidence & progress"),
    "roadmap": ("Mission and hardware roadmap | Wrench", "Mission & roadmap"),
    "faq": ("Practical questions | Wrench", "FAQ"),
    "brand": ("Brand assets | Wrench", "Brand assets"),
    "author": ("A note from the author | Wrench", "From the author"),
}

ASSETS = ("site.css", "brand.css", "site.js", "demo-receipt.json", "wrench-mark.svg", "wrench-mark-ink.svg", "wrench-avatar.svg", "hardware-garden.svg")
GENERATED_ASSETS = ("hardware-garden-zh.svg",)
ZH_PAGES = {
    "index": ("Wrench | AI，也得用得起", "首页"),
    "getting-started": ("先跑起来 | Wrench", "先跑起来"),
    "how-it-works": ("它怎么干活 | Wrench", "它怎么干活"),
    "model-story": ("这把扳手怎么造的 | Wrench", "这把扳手怎么造的"),
    "integrations": ("和谁搭伙 | Wrench", "和谁搭伙"),
    "evidence": ("进展与证据 | Wrench", "进展与证据"),
    "roadmap": ("我们想怎么走 | Wrench", "我们想怎么走"),
    "faq": ("你大概会问 | Wrench", "你大概会问"),
    "brand": ("品牌素材 | Wrench", "品牌素材"),
    "author": ("作者留言 | Wrench", "作者留言"),
}


def link(slug, label, current):
    active = ' aria-current="page"' if slug == current else ""
    return f'<a href="{slug}.html"{active}>{html.escape(label)}</a>'


def build(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    assets = output / "assets"
    assets.mkdir(exist_ok=True)
    for name in ASSETS:
        shutil.copyfile(ROOT / "site" / "assets" / name, assets / name)
    shutil.copyfile(ROOT / "examples" / "local_first.py", assets / "local_first.py")
    artwork = (assets / "hardware-garden.svg").read_text(encoding="utf-8")
    for original, translated in {
        "A little more life in the hardware you already own": "让手头的硬件再上场",
        "An original vector illustration of a laptop, a compact graphics card, and an older phone linked by dotted paths. This illustrates the hardware and sharing vision, not currently supported devices.": "笔记本、小显卡和旧手机由虚线连接。这是硬件和分享愿景的插画，不代表目前支持的设备。",
        "THE COMPUTER ON YOUR DESK": "桌上那台老伙计",
        "A LITTLE MORE POSSIBILITY": "再多一点可能",
        "THE PHONE IN YOUR DRAWER": "抽屉里的旧手机",
    }.items():
        artwork = artwork.replace(original, translated)
    (assets / "hardware-garden-zh.svg").write_text(artwork, encoding="utf-8")
    for language, page_map in (("en", PAGES), ("zh-CN", ZH_PAGES)):
        build_language(output, language, page_map)
    (output / ".nojekyll").touch()
    (output / "404.html").write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Page not found | Wrench</title><h1>That page is missing. / 这页走丢了。</h1><p>Visit the <a href="/wrench-slm/">Wrench documentation home</a>.</p></html>', encoding="utf-8")
    print(f"Built {len(PAGES) + len(ZH_PAGES)} bilingual pages in {output}")


def build_language(output: Path, language: str, page_map: dict):
    chinese = language == "zh-CN"
    prefix = "../" if chinese else ""
    source = ROOT / "site" / "pages" / ("zh" if chinese else "")
    destination = output / ("zh" if chinese else "")
    destination.mkdir(parents=True, exist_ok=True)
    description = ("让普通人也用得起 AI。Wrench 想让你手头的硬件多干点实事，从有边界的本地开发任务开始。" if chinese else "Affordable AI for the rest of us. Wrench is building useful local AI workflows for the hardware you already own. Explore the developer preview and hardware roadmap.")
    main_links = [("getting-started", "文档"), ("roadmap", "路线图"), ("evidence", "进展")] if chinese else [("getting-started", "Docs"), ("roadmap", "Roadmap"), ("evidence", "Evidence")]
    footer_links = [("getting-started", "使用文档"), ("roadmap", "我们的想法"), ("author", "作者留言"), ("evidence", "进展与证据"), ("faq", "常见问题"), ("brand", "品牌素材")] if chinese else [("getting-started", "Documentation"), ("roadmap", "Our mission"), ("author", "From the author"), ("evidence", "Evidence"), ("faq", "FAQ"), ("brand", "Brand")]
    for slug, (title, label) in page_map.items():
        content = (source / f"{slug}.html").read_text(encoding="utf-8")
        if chinese:
            content = content.replace('href="assets/', 'href="../assets/').replace('src="assets/', 'src="../assets/')
        navigation = "".join(link(s, l, slug) for s, l in main_links)
        switch_url = f"../{slug}.html" if chinese else f"zh/{slug}.html"
        switch_label = "EN" if chinese else "中文"
        switch_lang = "en" if chinese else "zh-CN"
        switch_title = "Switch this page to English" if chinese else "阅读本页中文版"
        language_switch = f'<a class="language-switch" href="{switch_url}" lang="{switch_lang}" hreflang="{switch_lang}" aria-label="{switch_title}">{switch_label}</a>'
        footer_navigation = "".join(link(s, l, slug) for s, l in footer_links)
        home_label = "Wrench 首页" if chinese else "Wrench home"
        cta = "认识一下 Wrench ↗" if chinese else "Explore Wrench ↗"
        footer_note = "AI，也得让咱用得起。开发者预览版，认真打磨中。" if chinese else "Affordable AI for the rest of us. Developer preview, built with care."
        if slug == "author":
            content = f'<div class="wrap letter-layout"><article class="article author-letter">{content}</article></div>'
        elif slug != "index":
            sidebar = "".join(link(s, v[1], slug) for s, v in page_map.items() if s not in ("index", "brand"))
            guide_title = "Wrench 上手小册子" if chinese else "The Wrench field guide"
            review = "开发者预览版<br>更新于 2026-09-22" if chinese else "DEVELOPER PREVIEW<br>Reviewed 2026-09-22"
            content = f'<div class="wrap docs-layout"><nav class="sidebar" aria-label="{"文档目录" if chinese else "Documentation"}"><strong>{guide_title}</strong>{sidebar}<p class="small">{review}</p></nav><article class="article">{content}</article></div>'
        page = f'''<!doctype html>
<html lang="{language}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)}</title><meta name="description" content="{description}"><meta name="theme-color" content="#fdfcf8"><link rel="alternate" hreflang="{switch_lang}" href="{switch_url}"><link rel="icon" type="image/svg+xml" href="{prefix}assets/wrench-avatar.svg"><link rel="stylesheet" href="{prefix}assets/site.css"><link rel="stylesheet" href="{prefix}assets/brand.css"><script defer src="{prefix}assets/site.js"></script></head>
<body><a class="skip" href="#main">{"跳到正文" if chinese else "Skip to content"}</a><header class="topbar"><div class="wrap"><a class="brand" href="index.html" aria-label="{home_label}"><img src="{prefix}assets/wrench-mark.svg" width="40" height="36" alt="">wrench</a><nav class="nav" aria-label="{"主导航" if chinese else "Main navigation"}">{navigation}{language_switch}<a class="nav-cta" href="getting-started.html">{cta}</a></nav></div></header><main id="main">{content}</main><footer class="footer"><div class="wrap"><a class="brand" href="index.html" aria-label="{home_label}"><img src="{prefix}assets/wrench-mark.svg" width="30" height="28" alt="">wrench</a><nav class="footer-links" aria-label="{"页脚导航" if chinese else "Footer navigation"}">{footer_navigation}</nav><p class="footer-note">{footer_note}<br>From Calgary with ❤️. BA Research</p></div></footer></body></html>'''
        (destination / f"{slug}.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "docs-site")
    build(parser.parse_args().output.resolve())
