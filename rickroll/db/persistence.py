from abc import ABC, abstractmethod
from typing import Self, Optional
from urllib.parse import quote, unquote
from datetime import datetime, timedelta
import random, string


class PersistenceException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class Persistence(ABC):
    supports_cleanup: bool

    def __init__(self, app, max_urls_per_ip: int = 10, *args, **kwargs) -> None:
        self.app = app
        self.max_urls_per_ip = max_urls_per_ip

    def get(self: Self, url: str, client_ip: str) -> str:
        if (result := self._get(url)) is not None:
            return result

        if self.urls_per_ip(client_ip) >= self.max_urls_per_ip:
            raise PersistenceException(
                "Too many urls created. Please, try again later."
            )
        return self._create(url, client_ip)

    def lookup(self: Self, slug: str) -> str:
        if (url := self._lookup(slug)) is not None:
            self._update_time_accessed(slug)
            return url
        raise PersistenceException(f'Slug "{slug}" is invalid or has expired')

    @abstractmethod
    def _get(self: Self, url: str) -> Optional[str]:
        pass

    @abstractmethod
    def _create(self: Self, url: str, client_ip: str) -> str:
        pass

    @abstractmethod
    def _lookup(self: Self, slug: str) -> Optional[str]:
        pass

    @abstractmethod
    def _update_time_accessed(self: Self, slug: str):
        pass

    @abstractmethod
    def urls_per_ip(self: Self, ip: str) -> int:
        pass

    def teardown(self: Self, exception: Optional[Exception]):
        pass

    def cleanup(self: Self, retention: timedelta):
        pass

    def generate_slug(self: Self) -> str:
        return "".join(random.choice(string.hexdigits) for _ in range(15))  # nosec B311

    def now(self: Self) -> datetime:
        return datetime.utcnow()


class NoPersistence(Persistence):
    supports_cleanup = False

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _get(self: Self, url: str) -> str:
        return quote(url, safe="")

    def _create(self: Self, url: str, client_ip: str) -> str:
        return self._get(url)

    def _lookup(self: Self, slug: str) -> Optional[str]:
        return unquote(slug)

    def _update_time_accessed(self: Self, slug: str):
        pass

    def urls_per_ip(self: Self, ip: str) -> int:
        return 0