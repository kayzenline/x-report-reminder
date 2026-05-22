import asyncio
from dataclasses import dataclass
from urllib.parse import urlparse

import click
from twscrape import API, AccountsPool
from twscrape.login import LoginConfig

from .config import Config


@dataclass
class ArticleLink:
    tweet_id: str
    handle: str
    url: str
    tweet_date: str


async def init_twscrape(config: Config) -> None:
    config.twscrape_db_path.parent.mkdir(parents=True, exist_ok=True)
    # manual=True → twscrape prompts you to type the verification code X sends,
    # rather than trying to read it from your inbox over IMAP.
    pool = AccountsPool(
        str(config.twscrape_db_path),
        login_config=LoginConfig(manual=True),
    )
    # Re-init is idempotent: drop any prior row so fresh cookies/secret take effect
    # (add_account silently skips usernames that already exist).
    await pool.delete_accounts(config.x_username)

    if config.x_cookies:
        # Cookie path: account becomes active on add (ct0 present) — no login flow,
        # so X's Cloudflare-protected login endpoint is never touched.
        await pool.add_account(
            username=config.x_username,
            password=config.x_password,
            email=config.x_email,
            email_password=config.x_email_password,
            cookies=config.x_cookies,
        )
    else:
        await pool.add_account(
            username=config.x_username,
            password=config.x_password,
            email=config.x_email,
            email_password=config.x_email_password,
            mfa_code=config.x_mfa_secret or None,
        )
        click.echo(
            "Logging in to X… if prompted, paste the verification code "
            "(check your email, SMS, or the X app) and press Enter."
        )
        await pool.login_all()

    # Report the real outcome instead of assuming success.
    info = await pool.accounts_info()
    acc = next((a for a in info if a["username"] == config.x_username), None)
    if acc and acc["active"]:
        click.echo(f"✓ Account {config.x_username} is active — session saved.")
    else:
        detail = (acc and acc["error_msg"]) or "no active session"
        raise click.ClickException(f"Login failed for {config.x_username}: {detail}")


async def get_user_id(api: API, handle: str) -> str | None:
    user = await api.user_by_login(handle)
    return str(user.id) if user else None


async def fetch_article_links(
    api: API, handle: str, user_id: str, limit: int
) -> list[ArticleLink]:
    links: list[ArticleLink] = []
    seen: set[str] = set()
    async for tweet in api.user_tweets(int(user_id), limit=limit):
        for text_link in tweet.links:
            # twscrape's TextLink.url is already the expanded URL; tcourl is the t.co form
            url = text_link.url or text_link.tcourl
            if not url:
                continue
            # dedupe within the batch — X repeats a link in the card and the text,
            # which would otherwise summarise (and bill) the same article twice
            if url in seen:
                continue
            seen.add(url)
            # skip t.co redirects and twitter/x self-links (host-based, not substring)
            host = urlparse(url).netloc.lower()
            if "@" in host:
                host = host.rsplit("@", 1)[1]
            if ":" in host:
                host = host.split(":", 1)[0]
            if any(host == d or host.endswith("." + d) for d in ("t.co", "twitter.com", "x.com")):
                continue
            if not url.startswith("http"):
                continue
            links.append(
                ArticleLink(
                    tweet_id=str(tweet.id),
                    handle=handle,
                    url=url,
                    tweet_date=tweet.date.strftime("%Y-%m-%d") if tweet.date else "",
                )
            )
    return links

    # --- Playwright fallback stub (uncomment to swap in) ---
    # async with async_playwright() as p:
    #     browser = await p.chromium.launch(headless=True)
    #     page = await browser.new_page()
    #     await page.goto(f"https://x.com/{handle}")
    #     # scroll and extract links...
    #     await browser.close()
    # return links
