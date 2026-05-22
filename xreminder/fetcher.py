from dataclasses import dataclass

import httpx
import trafilatura


@dataclass
class FetchResult:
    url: str
    title: str
    text: str
    fetch_error: str


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


async def fetch_article_text(url: str) -> FetchResult:
    try:
        async with httpx.AsyncClient(
            headers=_HEADERS, follow_redirects=True, timeout=15.0
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
    except Exception as exc:
        return FetchResult(url=url, title="", text="", fetch_error=str(exc))

    extracted = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        with_metadata=True,
        output_format="json",
    )
    if not extracted:
        return FetchResult(url=url, title="", text="", fetch_error="trafilatura: no content extracted")

    import json
    data = json.loads(extracted)
    return FetchResult(
        url=url,
        title=data.get("title", ""),
        text=data.get("text", ""),
        fetch_error="",
    )
