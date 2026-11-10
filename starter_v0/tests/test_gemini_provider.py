"""Provider transport checks, without network requests or real waits."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from google import genai
from google.genai.errors import APIError

from providers import gemini_provider
from providers.gemini_provider import GeminiProvider


@pytest.fixture
def transport(monkeypatch):
    factory = MagicMock()
    client = factory.return_value
    response = SimpleNamespace(candidates=[], function_calls=[])
    client.models.generate_content.return_value = response
    monkeypatch.setattr(genai, "Client", factory)
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    clock = SimpleNamespace(now=100.0, waits=[])

    def sleep(seconds):
        clock.waits.append(seconds)
        clock.now += seconds

    monkeypatch.setattr(gemini_provider.time, "monotonic", lambda: clock.now)
    monkeypatch.setattr(gemini_provider.time, "sleep", sleep)
    return factory, client, response, clock


def api_error(code, details=None):
    return APIError(code, {"error": {"code": code, "message": "test", "details": details or []}})


def test_reuses_connection_and_closes_it(transport):
    factory, client, _, _ = transport
    provider = GeminiProvider()
    provider.complete([])
    provider.complete([])
    factory.assert_called_once()
    # The provider owns retries, so they cannot multiply SDK retry delays.
    assert factory.call_args.kwargs["http_options"].retry_options.attempts == 1
    assert factory.call_args.kwargs["http_options"].timeout == 60000
    provider.close()
    provider.close()
    client.close.assert_called_once()


def test_only_waits_for_interval_remaining_after_tool_execution(transport):
    _, _, _, clock = transport
    provider = GeminiProvider()
    provider.complete([])
    clock.now += 4
    provider.complete([])
    clock.now += 20
    provider.complete([])
    assert clock.waits == pytest.approx([8.1])


def test_request_interval_can_be_disabled(monkeypatch, transport):
    _, _, _, clock = transport
    monkeypatch.setenv("GEMINI_REQUEST_INTERVAL", "0")
    provider = GeminiProvider()
    provider.complete([])
    provider.complete([])
    assert clock.waits == []


def test_missing_key_does_not_create_client(monkeypatch, transport):
    factory, _, _, _ = transport
    monkeypatch.delenv("GEMINI_API_KEY")
    with pytest.raises(RuntimeError, match="Missing API key"):
        GeminiProvider().complete([])
    factory.assert_not_called()


@pytest.mark.parametrize("delay,expected", [(5, 12.1), (20, 20.1)])
def test_rate_limit_respects_server_cooldown_without_double_wait(transport, delay, expected):
    _, client, response, clock = transport
    client.models.generate_content.side_effect = [
        api_error(429, [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": f"{delay}s"}]),
        response,
    ]
    GeminiProvider().complete([])
    assert clock.waits == pytest.approx([expected])
    assert client.models.generate_content.call_count == 2


def test_overload_retries_stop_after_four_attempts(transport):
    _, client, _, clock = transport
    client.models.generate_content.side_effect = api_error(503)
    with pytest.raises(APIError):
        GeminiProvider().complete([])
    assert client.models.generate_content.call_count == 4
    assert clock.waits == pytest.approx([12.1, 12.1, 12.1])


def test_rate_limit_without_cooldown_waits_for_quota_window(transport):
    _, client, response, clock = transport
    client.models.generate_content.side_effect = [api_error(429), response]
    GeminiProvider().complete([])
    assert clock.waits == pytest.approx([60.1])


@pytest.mark.parametrize("code,details", [
    (401, []),
    (403, []),
    (429, [{"violations": [{"quotaId": "GenerateRequestsPerDayPerProject"}]}]),
    (429, [{"violations": [{"quotaValue": "0"}]}]),
])
def test_permanent_errors_fail_without_waiting(transport, code, details):
    _, client, _, clock = transport
    client.models.generate_content.side_effect = api_error(code, details)
    with pytest.raises(APIError):
        GeminiProvider().complete([])
    client.models.generate_content.assert_called_once()
    assert clock.waits == []


def test_twenty_requests_stay_within_five_per_rolling_minute(transport):
    _, client, response, clock = transport
    starts = []

    def generate(**kwargs):
        starts.append(clock.now)
        clock.now += 3
        return response

    client.models.generate_content.side_effect = generate
    provider = GeminiProvider()
    for _ in range(20):
        provider.complete([])
        clock.now += 2  # Simulated local tool/API work.
    assert all(sum(start <= t < start + 60 for t in starts) <= 5 for start in starts)
    assert starts[-1] - starts[0] == pytest.approx(19 * 12.1)


def test_daily_quota_stops_further_calls_without_blocking_other_models(transport):
    _, client, response, clock = transport
    client.models.generate_content.side_effect = api_error(
        429, [{"violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel"}]}],
    )
    provider = GeminiProvider()
    for _ in range(20):
        with pytest.raises(APIError):
            provider.complete([], model="exhausted-model")
    client.models.generate_content.assert_called_once()
    assert clock.waits == []
    client.models.generate_content.side_effect = None
    client.models.generate_content.return_value = response
    provider.complete([], model="other-model")
    assert client.models.generate_content.call_count == 2
