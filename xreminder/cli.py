import asyncio
import sqlite3

import click

from .config import Config
from .db import add_account, init_db, list_accounts, remove_account


def get_db(config: Config):
    return init_db(config.resolved_db_path)


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    ctx.obj["config"] = Config()
    ctx.obj["db"] = get_db(ctx.obj["config"])


@cli.command("add-account")
@click.argument("handle")
@click.pass_context
def cmd_add_account(ctx, handle: str):
    """Track a new X account."""
    conn = ctx.obj["db"]
    handle = handle.lstrip("@").lower()
    added = add_account(conn, handle)
    if added:
        click.echo(f"Added @{handle}")
    else:
        click.echo(f"@{handle} is already tracked")


@cli.command("remove-account")
@click.argument("handle")
@click.pass_context
def cmd_remove_account(ctx, handle: str):
    """Stop tracking an X account."""
    conn = ctx.obj["db"]
    removed = remove_account(conn, handle)
    handle = handle.lstrip("@").lower()
    if removed:
        click.echo(f"Removed @{handle}")
    else:
        click.echo(f"@{handle} not found")


@cli.command("list-accounts")
@click.pass_context
def cmd_list_accounts(ctx, **kwargs):
    """Show all tracked X accounts."""
    conn = ctx.obj["db"]
    accounts = list_accounts(conn)
    if not accounts:
        click.echo("No accounts tracked. Use: xreminder add-account <handle>")
        return
    click.echo(f"{'Handle':<25} {'Twitter ID':<22} Added")
    click.echo("-" * 65)
    for a in accounts:
        tid = a["twitter_id"] or "-"
        click.echo(f"@{a['handle']:<24} {tid:<22} {a['added_at']}")


@cli.command("init-scraper")
@click.pass_context
def cmd_init_scraper(ctx):
    """One-time login to X via twscrape. Saves session cookies."""
    from .scraper import init_twscrape

    config = ctx.obj["config"]
    missing = config.validate_scraper()
    if missing:
        click.echo(f"Missing .env values: {', '.join(missing)}", err=True)
        raise SystemExit(1)
    asyncio.run(init_twscrape(config))
    click.echo("Scraper initialised — cookies saved.")


@cli.command("fetch")
@click.option("--account", default=None, help="Fetch only this handle (no @)")
@click.option("--dry-run", is_flag=True, help="Print URLs without saving anything")
@click.pass_context
def cmd_fetch(ctx, account: str | None, dry_run: bool):
    """Fetch new articles, summarise, and save to Obsidian."""
    from .db import list_accounts as db_list
    from .pipeline import run_pipeline

    config = ctx.obj["config"]
    conn = ctx.obj["db"]

    missing = config.validate_scraper() + config.validate_summarizer()
    if missing:
        click.echo(f"Missing .env values: {', '.join(missing)}", err=True)
        raise SystemExit(1)

    if account:
        handles = [account.lstrip("@").lower()]
    else:
        rows = db_list(conn)
        handles = [r["handle"] for r in rows]

    if not handles:
        click.echo("No accounts to fetch. Add one with: xreminder add-account <handle>")
        return

    stats = asyncio.run(run_pipeline(config, conn, handles, dry_run=dry_run))
    click.echo(
        f"\nDone — fetched: {stats['fetched']}  saved: {stats['saved']}  "
        f"skipped: {stats['skipped']}  errors: {stats['errors']}"
    )
