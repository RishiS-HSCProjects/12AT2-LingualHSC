from flask import current_app, has_request_context, url_for


def build_external_url(endpoint: str, **values) -> str:
    """Build an absolute URL without requiring SERVER_NAME in development.

    Uses the active request host when available. If no request context exists
    (for example in background threads), falls back to PUBLIC_BASE_URL.
    """
    if has_request_context():
        return url_for(endpoint, _external=True, **values)

    base_url = (current_app.config.get('PUBLIC_BASE_URL') or '').strip().rstrip('/')
    if not base_url:
        raise RuntimeError(
            "Cannot build external URL without request context. "
            "Set PUBLIC_BASE_URL in environment or app config."
        )

    with current_app.test_request_context(base_url=base_url):
        return url_for(endpoint, _external=True, **values)