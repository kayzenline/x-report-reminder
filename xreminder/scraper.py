import asyncio
from dataclasses import dataclass

import click
from twscrape import API, AccountsPool

from .config import Config


@dataclass
class ArticleLink:
    tweet_id: str
    handle: str
    url: str
    tweet_date: str


def _make_api(config: Config) -> API:
    pool = AccountsPool(str(config.twscrape_db_path))
    return API(pool)


async def init_twscrape(config: Config) -> None:
    config.twscrape_db_path.parent.mkdir(parents=True, exist_ok=True)
    api = _make_api(config)
    await api.pool.add_account(
        username=config.x_username,
        password=config.x_password,
        email=config.x_email,
        email_password=config.x_email_password,
    )
    click.echo("Logging in to X… (may prompt for email verification code)")
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
