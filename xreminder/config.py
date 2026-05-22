import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    x_username: str = field(default_factory=lambda: os.getenv("X_USERNAME", ""))
    x_password: str = field(default_factory=lambda: os.getenv("X_PASSWORD", ""))
    x_email: str = field(default_factory=lambda: os.getenv("X_EMAIL", ""))
    x_email_password: str = field(default_factory=lambda: os.getenv("X_EMAIL_PASSWORD", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    obsidian_vault_path: str = field(
        default_factory=lambda: os.getenv(
            "OBSIDIAN_VAULT_PATH",
            "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/all/sources/",
        )
    )
    db_path: str = field(
        default_factory=lambda: os.getenv(
            "DB_PATH", "~/.local/share/xreminder/xreminder.db"
        )
    )
    fetch_limit: int = field(
        default_factory=lambda: int(os.getenv("FETCH_LIMIT", "20"))
    )

    @property
    def resolved_vault_path(self) -> Path:
        return Path(os.path.expanduser(self.obsidian_vault_path))

    @property
    def resolved_db_path(self) -> Path:
        return Path(os.path.expanduser(self.db_path))

    @property
    def twscrape_db_path(self) -> Path:
        return self.resolved_db_path.parent / "twscrape_accounts.db"

    def validate_scraper(self) -> list[str]:
        missing = []
        if not self.x_username:
            missing.append("X_USERNAME")
        if not self.x_password:
            missing.append("X_PASSWORD")
        if not self.x_email:
            missing.append("X_EMAIL")
        return missing

    def validate_summarizer(self) -> list[str]:
        if not self.anthropic_api_key:
            return ["ANTHROPIC_API_KEY"]
        return []
