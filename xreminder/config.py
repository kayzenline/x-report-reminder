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
    # base32 TOTP secret for authenticator-app 2FA; spaces stripped for paste-safety
    x_mfa_secret: str = field(
        default_factory=lambda: os.getenv("X_MFA_SECRET", "").replace(" ", "")
    )
    # browser session cookies ("auth_token=..; ct0=..") to bypass Cloudflare login
    x_cookies: str = field(default_factory=lambda: os.getenv("X_COOKIES", "").strip())
    deepseek_api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    deepseek_base_url: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    )
    deepseek_model: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    )
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
        if not self.deepseek_api_key:
            return ["DEEPSEEK_API_KEY"]
        return []
