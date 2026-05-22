import asyncio
from dataclasses import dataclass

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
    api = API(pool)
    await api.pool.add_account(
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
    await api.pool.login_all()
    click.echo("Login complete.")


async def get_user_id(api: API, handle: str) -> str | None:
    user = await api.user_by_login(handle)
    return str(user.id) if user else None


async def fetch_article_links(
    api: API, handle: str, user_id: str, limit: int
) -> list[ArticleLink]:
    links: list[ArticleLink] = []
    async for tweet in api.user_tweets(int(user_id), limit=limit):
        for text_link in tweet.links:
            url = text_link.expanded_url or text_link.url
            if not url:
                continue
            # skip t.co redirects and twitter/x self-links
            if "t.co/" in url or "twitter.com" in url or "x.com" in url:
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
