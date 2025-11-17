import os
from typing import Any, Dict

import pytest

from services.premium_price_service import PremiumPriceService


class DummyResponse:
    def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
        self._json = json_data
        self.status_code = status_code

    def json(self) -> Dict[str, Any]:
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            from requests import HTTPError

            raise HTTPError(f"status={self.status_code}")


@pytest.fixture(autouse=True)
def clear_env(monkeypatch: pytest.MonkeyPatch):
    keys = [
        "SERPAPI_KEY",
        "SERPAPI_BACKUP_KEY",
        "COINGECKO_API_KEY",
        "ALPHA_VANTAGE_API_KEY",
        "FINNHUB_API_KEY",
    ]
    for key in keys:
        monkeypatch.setenv(key, "")
    yield
    for key in keys:
        monkeypatch.setenv(key, "")


def test_crypto_serpapi_success(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SERPAPI_KEY", "abc123")

    def fake_get(self, url, params=None, timeout=None):
        return DummyResponse({"price": "0.55", "price_movement": {"percentage": "1.5"}})

    monkeypatch.setattr("requests.Session.get", fake_get)
    monkeypatch.setattr(PremiumPriceService, "_respect_rate_limit", lambda self, name: None)

    svc = PremiumPriceService()
    quote = svc.get_price("xrp")

    assert quote is not None
    assert quote["source"] == "SERPAPI"
    assert quote["asset_class"] == "crypto"
    assert "0.5500" in quote["text"]


def test_crypto_fallback_to_coingecko(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("COINGECKO_API_KEY", "cg-key")

    def fake_get(self, url, params=None, timeout=None):
        if "serpapi.com" in url:
            return DummyResponse({"price": None})
        if "coingecko.com" in url:
            return DummyResponse({"ripple": {"usd": 0.62, "usd_24h_change": -2.5}})
        raise AssertionError("Unexpected URL")

    monkeypatch.setattr("requests.Session.get", fake_get)
    monkeypatch.setattr(PremiumPriceService, "_respect_rate_limit", lambda self, name: None)

    svc = PremiumPriceService()
    quote = svc.get_price("xrp")

    assert quote is not None
    assert quote["source"] == "CoinGecko"
    assert quote["price"] == pytest.approx(0.62)
    assert "CoinGecko" in quote["text"]


def test_equity_prefers_alpha_vantage(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "alpha")

    def fake_get(self, url, params=None, timeout=None):
        if "alphavantage.co" in url:
            return DummyResponse(
                {
                    "Global Quote": {
                        "05. price": "189.12",
                        "09. change": "1.23",
                        "10. change percent": "0.65%",
                        "06. volume": "123456",
                    }
                }
            )
        raise AssertionError("Unexpected URL")

    monkeypatch.setattr("requests.Session.get", fake_get)
    monkeypatch.setattr(PremiumPriceService, "_respect_rate_limit", lambda self, name: None)

    svc = PremiumPriceService()
    quote = svc.get_price("AAPL")

    assert quote is not None
    assert quote["source"] == "Alpha Vantage"
    assert quote["price"] == pytest.approx(189.12)
    assert "AAPL" in quote["text"]


def test_equity_fallback_to_finnhub(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FINNHUB_API_KEY", "finn")

    def fake_get(self, url, params=None, timeout=None):
        if "alphavantage.co" in url:
            return DummyResponse({}, status_code=200)
        if "finnhub.io" in url:
            return DummyResponse({"c": 410.55, "d": -2.1, "dp": -0.5})
        raise AssertionError("Unexpected URL")

    monkeypatch.setattr("requests.Session.get", fake_get)
    monkeypatch.setattr(PremiumPriceService, "_respect_rate_limit", lambda self, name: None)

    svc = PremiumPriceService()
    quote = svc.get_price("MSFT")

    assert quote is not None
    assert quote["source"] == "Finnhub"
    assert quote["price"] == pytest.approx(410.55)


def test_returns_none_when_no_keys(monkeypatch: pytest.MonkeyPatch):
    def fake_get(self, url, params=None, timeout=None):
        raise AssertionError("Should not call external API without keys")

    monkeypatch.setattr("requests.Session.get", fake_get)
    monkeypatch.setattr(PremiumPriceService, "_respect_rate_limit", lambda self, name: None)

    svc = PremiumPriceService()
    quote = svc.get_price("UNKNOWN")

    assert quote is None


