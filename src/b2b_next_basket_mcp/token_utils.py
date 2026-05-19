from __future__ import annotations


def split_tokens(text: str) -> list[str]:
    return text.split()


def is_time_token(token: str) -> bool:
    return token.startswith("<dt_")


def is_special_token(token: str) -> bool:
    return token in {"<eos>", "<unk>"} or is_time_token(token)


def make_time_token_readable(token: str) -> str:
    cleaned = token.replace("<dt_", "").replace(">", "")
    replacements = {
        "d": " day(s)",
        "w": " week(s)",
        "m": " month(s)",
        "y": " year(s)",
    }
    for suffix, label in replacements.items():
        if cleaned.endswith(suffix):
            return f"next order after {cleaned[:-1]}{label}"
    return f"next order timing: {cleaned}"


def make_token_readable(token: str) -> str:
    """
    Convert compact model tokens into rough human-readable labels.

    Example:
    s_gloves_nitrile_l -> gloves nitrile l
    c_solv_ethanol_abs -> solv ethanol abs
    """
    if is_time_token(token):
        return make_time_token_readable(token)

    if token in {"<eos>", "<unk>"}:
        return token

    parts = token.split("_")
    if len(parts) > 1 and len(parts[0]) <= 2:
        parts = parts[1:]
    return " ".join(parts)


def estimate_order_count(tokens: list[str]) -> int:
    return sum(1 for token in tokens if is_time_token(token))


def compact_token_preview(text: str, head: int = 40, tail: int = 80) -> dict[str, str | int]:
    tokens = split_tokens(text)
    preview_start = " ".join(tokens[:head])
    recent_history = " ".join(tokens[-tail:]) if tail > 0 else ""

    return {
        "total_tokens": len(tokens),
        "estimated_order_events": estimate_order_count(tokens),
        "preview_start": preview_start,
        "recent_history": recent_history,
    }


def readable_items_from_tokens(tokens: list[str]) -> list[str]:
    return [make_token_readable(token) for token in tokens if not is_special_token(token)]


def extract_time_prediction(tokens: list[str]) -> str | None:
    for token in tokens:
        if is_time_token(token):
            return make_time_token_readable(token)
    return None
