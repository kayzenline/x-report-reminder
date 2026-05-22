import asyncio
import sqlite3

import click
from openai import AsyncOpenAI
from twscrape import API, AccountsPool

from .config import Config
from .db import is_processed, mark_processed, update_twitter_id
from .fetcher import fetch_article_text
from .notes import save_note
from .scraper import ArticleLink, fetch_article_links, get_user_id
from .summarizer import summarize

_SEMAPHORE_LIMIT = 3  # max concurrent DeepSeek calls


async def _process_link(
    link: ArticleLink,
    config: Config,
    conn: sqlite3.Connection,
    client: AsyncOpenAI,
    sem: asyncio.Semaphore,
    dry_run: bool,
    stats: dict,
) -> None:
    if is_processed(conn, link.url):
        stats["skipped"] += 1
        return

    stats["fetched"] += 1

    if dry_run:
        click.echo(f"  [dry-run] @{link.handle} | {link.url}")
        return

    try:
        result = await fetch_article_text(link.url)
        if result.fetch_error:
            click.echo(f"  [fetch error] {link.url}: {result.fetch_error}", err=True)
            mark_processed(conn, link.url, link.tweet_id, link.handle, "")
            stats["errors"] += 1
            return

        async with sem:
            summary = await summarize(client, config.deepseek_model, result.title, result.text)

        note_path = save_note(
            vault_path=str(config.resolved_vault_path),
            handle=link.handle,
            title=result.title,
            url=link.url,
            date=link.tweet_date,
            summary=summary,
        )
        mark_processed(conn, link.url, link.tweet_id, link.handle, note_path)
        stats["saved"] += 1
        click.echo(f"  Saved: {result.title or link.url}")

    except Exception as exc:
        click.echo(f"  [error] {link.url}: {exc}", err=True)
        mark_processed(conn, link.url, link.tweet_id, link.handle, "")
        stats["errors"] += 1


async def run_pipeline(
    config: Config,
    conn: sqlite3.Connection,
    handles: list[str],
    dry_run: bool = False,
) -> dict:
    stats = {"fetched": 0, "saved": 0, "skipped": 0, "errors": 0}
    sem = asyncio.Semaphore(_SEMAPHORE_LIMIT)

    pool = AccountsPool(str(config.twscrape_db_path))
    api = API(pool)
    client = AsyncOpenAI(
        api_key=config.deepseek_api_key,
        base_url=config.deepseek_base_url,
    )

    for handle in handles:
        click.echo(f"\nFetching @{handle}…")

        # get twitter_id (use cached value from DB if available)
        from .db import list_accounts
        rows = list_accounts(conn)
        cached = {r["handle"]: r["twitter_id"] for r in rows}
        twitter_id = cached.get(handle)

        if not twitter_id:
            twitter_id = await get_user_id(api, handle)
            if not twitter_id:
                click.echo(f"  Could not resolve @{handle} — skipping", err=True)
                continue
            update_twitter_id(conn, handle, twitter_id)

        links: list[ArticleLink] = await fetch_article_links(
            api, handle, twitter_id, config.fetch_limit
        )
        click.echo(f"  Found {len(links)} article link(s)")

        tasks = [
            _process_link(link, config, conn, client, sem, dry_run, stats)
            for link in links
        ]
        await asyncio.gather(*tasks)

    return stats
