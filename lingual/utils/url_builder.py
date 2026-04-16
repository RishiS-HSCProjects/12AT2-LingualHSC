from flask import current_app, has_request_context, url_for

def build_external_url(endpoint: str, **values) -> str:
    """Build an absolute URL without requiring SERVER_NAME in development.

    Uses the active request host when available. If no request context exists
    (for example in background threads), falls back to PUBLIC_BASE_URL.
    """
    if has_request_context():
        # If we have a request context, we can build the URL normally using url_for with _external=True to get an absolute URL.
        return url_for(endpoint, _external=True, **values)

    # Get the base URL from configuration, removing trailing slashes
    base_url = (current_app.config.get('PUBLIC_BASE_URL') or '').strip().rstrip('/')
    if not base_url:
        # If PUBLIC_BASE_URL is not set, we cannot build an external URL without a request context, so we raise an error to indicate this misconfiguration.
        raise RuntimeError(
            "Cannot build external URL without request context. "
            "Set PUBLIC_BASE_URL in environment or app config."
        )

    # Use a test request context with the base URL to build the absolute URL for the given endpoint and values.
    with current_app.test_request_context(base_url=base_url):
        return url_for(endpoint, _external=True, **values) # Build endpoint URL
