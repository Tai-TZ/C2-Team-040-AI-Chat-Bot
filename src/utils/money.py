"""Money formatting helpers."""


def format_vnd(amount: int) -> str:
    return f"{amount:,} đ".replace(",", ".")
