import re
from pathlib import Path


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80]


def save_note(
    vault_path: str,
    handle: str,
    title: str,
    url: str,
    date: str,
    summary: str,
) -> str:
    vault = Path(vault_path) if vault_path.startswith("/") else Path(vault_path.replace("~", str(Path.home())))
    vault.mkdir(parents=True, exist_ok=True)

    slug = _slugify(title) if title else "untitled"
    filename = f"{date}-{slug}.md" if date else f"{slug}.md"
    note_path = vault / filename

    # avoid overwriting if slug collision
    counter = 1
    while note_path.exists():
        note_path = vault / f"{date}-{slug}-{counter}.md"
        counter += 1

    display_title = title or url
    frontmatter = f"""---
title: "{display_title.replace('"', "'")}"
author: "@{handle}"
source_url: "{url}"
date: {date}
tags:
  - x-report
  - auto-summary
---

"""
    note_path.write_text(frontmatter + summary, encoding="utf-8")
    return str(note_path)
