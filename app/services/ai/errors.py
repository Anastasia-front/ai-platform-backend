from dataclasses import dataclass

import httpx


@dataclass
class ProviderFailureSummary:
    provider: str
    model: str
    category: str
    status_code: int | None = None


class ProviderError(Exception):
    category = "provider_error"
    retryable = False

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class ProviderRateLimitError(ProviderError):
    category = "rate_limit"
    retryable = True


class ProviderQuotaError(ProviderError):
    category = "quota"
    retryable = True


class ProviderTimeoutError(ProviderError):
    category = "timeout"
    retryable = True


class ProviderUnavailableError(ProviderError):
    category = "unavailable"
    retryable = True


class ProviderAuthenticationError(ProviderError):
    category = "authentication"


class ProviderInvalidRequestError(ProviderError):
    category = "invalid_request"


class ProviderResponseError(ProviderError):
    category = "response_error"


class ProviderPartialGenerationError(ProviderError):
    category = "partial_generation"


class AllProvidersFailedError(ProviderError):
    category = "all_providers_failed"

    def __init__(self, attempts: list[ProviderFailureSummary]) -> None:
        super().__init__("No configured AI provider could complete the request.")
        self.attempts = attempts


def classify_provider_error(exc: Exception) -> ProviderError:
    if isinstance(exc, ProviderError):
        return exc

    if isinstance(exc, (httpx.TimeoutException, TimeoutError)):
        return ProviderTimeoutError("Provider request timed out.")

    if isinstance(exc, httpx.ConnectError):
        return ProviderUnavailableError("Provider connection failed.")

    if isinstance(exc, httpx.NetworkError):
        return ProviderUnavailableError("Provider network error.")

    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        retry_after = _retry_after_seconds(exc.response.headers.get("Retry-After"))

        if status_code == 402:
            return ProviderQuotaError(
                "Provider quota exhausted.",
                status_code=status_code,
                retry_after=retry_after,
            )
        if status_code == 429:
            return ProviderRateLimitError(
                "Provider rate limited the request.",
                status_code=status_code,
                retry_after=retry_after,
            )
        if 500 <= status_code <= 599:
            return ProviderUnavailableError(
                "Provider server error.",
                status_code=status_code,
                retry_after=retry_after,
            )
        if status_code in {401, 403}:
            return ProviderAuthenticationError(
                "Provider authentication failed.",
                status_code=status_code,
            )
        if 400 <= status_code <= 499:
            return ProviderInvalidRequestError(
                "Provider rejected the request.",
                status_code=status_code,
            )

    if isinstance(exc, httpx.HTTPError):
        return ProviderUnavailableError("Provider HTTP error.")

    if isinstance(exc, (KeyError, IndexError, ValueError)):
        return ProviderResponseError("Provider returned an unexpected response.")

    return ProviderResponseError("Provider request failed.")


def _retry_after_seconds(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(float(value), 0.0)
    except ValueError:
        return None
