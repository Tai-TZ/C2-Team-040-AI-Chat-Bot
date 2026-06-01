"""
E-commerce tools for Lab 3 — Smart Shopping Assistant scenario.
Each tool has a precise description so the LLM can call it correctly.
"""

from typing import Any, Callable, Dict, List

# Mock product catalog (USD)
PRODUCTS = {
    "iphone": {"name": "iPhone 15", "price": 999.0, "weight_kg": 0.2, "stock": 50},
    "macbook": {"name": "MacBook Air", "price": 1199.0, "weight_kg": 1.2, "stock": 20},
    "airpods": {"name": "AirPods Pro", "price": 249.0, "weight_kg": 0.05, "stock": 100},
}

COUPONS = {
    "WINNER": 0.15,
    "SAVE10": 0.10,
    "VIP20": 0.20,
}

SHIPPING_RATES = {
    "hanoi": 5.0,
    "hcm": 4.0,
    "danang": 6.0,
    "default": 10.0,
}


def check_stock(item_name: str) -> str:
    """Return stock and unit price for a product. item_name: lowercase product key (iphone, macbook, airpods)."""
    key = item_name.strip().lower()
    if key not in PRODUCTS:
        return f"Error: Product '{item_name}' not found. Available: {', '.join(PRODUCTS.keys())}"
    p = PRODUCTS[key]
    return f"{p['name']}: price=${p['price']}, stock={p['stock']} units, weight={p['weight_kg']}kg"


def get_discount(coupon_code: str) -> str:
    """Return discount percentage for a coupon code. coupon_code: uppercase string (e.g. WINNER, SAVE10)."""
    code = coupon_code.strip().upper()
    if code not in COUPONS:
        return f"Error: Coupon '{coupon_code}' is invalid or expired."
    pct = int(COUPONS[code] * 100)
    return f"Coupon '{code}' gives {pct}% discount."


def calc_shipping(weight: float, destination: str) -> str:
    """Calculate shipping cost. weight: total weight in kg (float). destination: city name lowercase (hanoi, hcm, danang)."""
    dest = destination.strip().lower()
    base = SHIPPING_RATES.get(dest, SHIPPING_RATES["default"])
    cost = round(base + weight * 2.0, 2)
    return f"Shipping to {destination}: ${cost} (base ${base} + ${weight * 2.0:.2f} weight surcharge)"


def calc_total(subtotal: float, discount_pct: float, shipping: float) -> str:
    """Calculate final total. subtotal: pre-discount amount, discount_pct: 0-100 integer/float, shipping: shipping cost."""
    discount_amount = subtotal * (discount_pct / 100)
    total = round(subtotal - discount_amount + shipping, 2)
    return (
        f"Subtotal=${subtotal:.2f}, discount={discount_pct}% (-${discount_amount:.2f}), "
        f"shipping=${shipping:.2f}, TOTAL=${total:.2f}"
    )


TOOL_REGISTRY: Dict[str, Callable[..., str]] = {
    "check_stock": check_stock,
    "get_discount": get_discount,
    "calc_shipping": calc_shipping,
    "calc_total": calc_total,
}


def get_tool_definitions() -> List[Dict[str, Any]]:
    return [
        {
            "name": "check_stock",
            "description": check_stock.__doc__,
            "func": check_stock,
            "params": ["item_name"],
        },
        {
            "name": "get_discount",
            "description": get_discount.__doc__,
            "func": get_discount,
            "params": ["coupon_code"],
        },
        {
            "name": "calc_shipping",
            "description": calc_shipping.__doc__,
            "func": calc_shipping,
            "params": ["weight", "destination"],
        },
        {
            "name": "calc_total",
            "description": calc_total.__doc__,
            "func": calc_total,
            "params": ["subtotal", "discount_pct", "shipping"],
        },
    ]
