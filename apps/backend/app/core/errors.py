class AppError(Exception):
    """Expected application error safe to map to a public message."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        error_code: str = "application_error",
        provider: str | None = None,
        stage: str | None = None,
    ) -> None:
        super().__init__(message)
        self.public_message = message
        self.status_code = status_code
        self.error_code = error_code
        self.provider = provider
        self.stage = stage


class ProviderUnavailableError(AppError):
    def __init__(self, provider: str) -> None:
        super().__init__(
            f"{provider} is unavailable. Configure its server-side credentials or use DEMO mode.",
            status_code=503,
            error_code="provider_unavailable",
            provider=provider,
            stage="configuration",
        )

