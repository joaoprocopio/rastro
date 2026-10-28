import httpx
import pytest

from rastro.settings import Settings


@pytest.fixture
async def cookieless_client(
    sample_client: httpx.AsyncClient, settings: Settings
) -> httpx.AsyncClient:
    """A sample client with no CSRF cookie and no CSRF header."""
    sample_client.cookies.clear()
    del sample_client.headers[settings.csrf_header_name]
    return sample_client
