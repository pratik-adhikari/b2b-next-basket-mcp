from __future__ import annotations


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


def readable_items_from_tokens(tokens: list[str]) -> list[str]:
    return [make_token_readable(token) for token in tokens if not is_special_token(token)]


def extract_time_prediction(tokens: list[str]) -> str | None:
    for token in tokens:
        if is_time_token(token):
            return make_time_token_readable(token)
    return None
