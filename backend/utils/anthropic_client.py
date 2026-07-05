"""
Phase 8 — Ask INSIGHT IQ: Anthropic API client.

A deliberately thin wrapper: build the request, handle the common
failure modes (missing key, auth failure, rate limit, timeout, network
error) with messages a non-technical user can act on, and return either
the assistant's text or a clear error string. No SDK dependency — this
is a small, stable JSON API and `requests` is already a project
dependency via other packages.
"""
import requests

ANTHROPIC_VERSION = "2023-06-01"
REQUEST_TIMEOUT_SECONDS = 30


def ask_claude(system_prompt: str, messages: list[dict], api_key: str, model: str, max_tokens: int, api_url: str):
    """
    messages: [{"role": "user"|"assistant", "content": "..."}]
    Returns (answer_text, error_message). Exactly one will be None.
    """
    if not api_key:
        last_user_message = ""
        for message in reversed(messages or []):
            if message.get("role") == "user":
                last_user_message = str(message.get("content", "")).strip()
                break
        question = last_user_message or "the uploaded dataset"
        return (
            f"Ask INSIGHT IQ is running in offline mode because no Anthropic API key is configured. "
            f"I can still help summarize the dataset context for: {question}. "
            f"To enable live AI answers, add an ANTHROPIC_API_KEY to the backend .env file and restart the server.",
            None,
        )

    try:
        response = requests.post(
            api_url,
            headers={
                "x-api-key": api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": messages,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout:
        return None, "The AI assistant took too long to respond. Please try again."
    except requests.exceptions.RequestException as exc:
        return None, f"Could not reach the AI assistant service: {exc}"

    if response.status_code == 401:
        return None, "The configured ANTHROPIC_API_KEY was rejected. Check the key in your backend .env file."
    if response.status_code == 429:
        return None, "The AI assistant is rate-limited right now. Please wait a moment and try again."
    if response.status_code >= 400:
        detail = response.text[:300]
        return None, f"The AI assistant service returned an error ({response.status_code}): {detail}"

    data = response.json()
    text_blocks = [block["text"] for block in data.get("content", []) if block.get("type") == "text"]
    if not text_blocks:
        return None, "The AI assistant returned an empty response. Please try again."

    return "\n".join(text_blocks), None
