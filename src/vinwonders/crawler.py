"""Fetch VinWonders ticket prices from the official booking API."""

from __future__ import annotations

import time
from typing import Any

import cloudscraper
import requests

API_TOUR = "https://booking-tour-api.vinpearl.com"
API_INFO = f"{API_TOUR}/api/bwc/vinwonder/vinwonderinfo"
API_DETAIL = f"{API_TOUR}/api/bwc/vinwonder/vinwonderticketdetail"

REQUEST_DELAY_SEC = 0.15


def _referer(supplier_code: str, using_date: str) -> str:
    return (
        f"https://booking.vinwonders.com/vi-VND/search"
        f"?code={supplier_code}&usingDate={using_date}"
    )


def _headers(supplier_code: str, using_date: str) -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Origin": "https://booking.vinwonders.com",
        "Referer": _referer(supplier_code, using_date),
        "x-supplier-code": supplier_code,
    }


def _fetch_catalog(
    supplier_code: str,
    using_date: str,
    session: requests.Session,
) -> list[dict[str, Any]]:
    """First page only; VinWonders pagination often repeats the same rows."""
    resp = session.get(
        API_INFO,
        params={"SupplierCode": supplier_code, "UsingDate": using_date},
        headers=_headers(supplier_code, using_date),
        timeout=60,
    )
    resp.raise_for_status()
    batch = (resp.json().get("data") or {}).get("result") or []

    seen: set[str] = set()
    tickets: list[dict[str, Any]] = []
    for ticket in batch:
        tid = ticket.get("vinWonderTicketId")
        if tid and tid not in seen:
            seen.add(tid)
            tickets.append(ticket)
    return tickets


def _fetch_price_tiers(
    supplier_code: str,
    using_date: str,
    ticket: dict[str, Any],
    scraper: cloudscraper.CloudScraper,
) -> list[dict[str, Any]]:
    resp = scraper.get(
        API_DETAIL,
        params={
            "SupplierCode": supplier_code,
            "UsingDate": using_date,
            "VinWonderTicketId": ticket["vinWonderTicketId"],
            "vinWonderId": ticket["vinWonderId"],
        },
        headers=_headers(supplier_code, using_date),
        timeout=45,
    )
    resp.raise_for_status()
    data = resp.json().get("data") or {}
    name = ticket.get("ticketName") or ""
    rows: list[dict[str, Any]] = []

    for item in data.get("vinWonderTicketItemResponses") or []:
        if not item.get("isEnableListing", True):
            continue
        obj = item.get("objectType") or {}
        label = obj.get("name") or obj.get("code") or ""
        rows.append(
            {
                "name": f"{name} - {label}".strip(" -"),
                "salePrice": int(item["salePrice"])
                if item.get("salePrice") is not None
                else None,
                "originalPrice": int(item["originalPrice"])
                if item.get("originalPrice") is not None
                else None,
                "guestType": label,
                "isDefault": bool(item.get("isDefault")),
            }
        )

    for combo in data.get("vinWonderTicketComboResponses") or []:
        combo_name = combo.get("vinWonderComboName") or combo.get("comboName") or name
        sale = combo.get("salePrice") or combo.get("comboSalePrice")
        rows.append(
            {
                "name": combo_name,
                "salePrice": int(sale) if sale is not None else None,
                "originalPrice": None,
                "guestType": "Combo",
                "isDefault": False,
            }
        )

    return [r for r in rows if r.get("salePrice") is not None]


def _pick_display_price(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One row per ticket: prefer default tier, else adult."""
    by_base: dict[str, dict[str, Any]] = {}
    for row in rows:
        full = row["name"]
        base = full.rsplit(" - ", 1)[0] if " - " in full else full
        is_adult = "Adult" in full or "(NL)" in full
        current = by_base.get(base)
        if current is None or row.get("isDefault") or (
            is_adult and not current.get("isDefault")
        ):
            by_base[base] = {
                "name": base,
                "salePrice": row["salePrice"],
                "originalPrice": row.get("originalPrice"),
            }
    return list(by_base.values())


def get_ticket_prices(
    supplier_code: str,
    using_date: str,
    *,
    detailed: bool = False,
) -> dict[str, Any]:
    """
    Load ticket prices for a site code and date.

    Args:
        supplier_code: e.g. NTVW1, PQVW1
        using_date: DD-MM-YYYY (VinWonders format)
        detailed: if True, return all guest tiers; else one price per ticket
    """
    http = requests.Session()
    scraper = cloudscraper.create_scraper()
    scraper.get(_referer(supplier_code, using_date), timeout=30)

    catalog = _fetch_catalog(supplier_code, using_date, http)
    all_rows: list[dict[str, Any]] = []

    for ticket in catalog:
        try:
            all_rows.extend(
                _fetch_price_tiers(supplier_code, using_date, ticket, scraper)
            )
        except requests.RequestException as exc:
            all_rows.append(
                {
                    "name": ticket.get("ticketName", ""),
                    "salePrice": None,
                    "error": str(exc),
                }
            )
        time.sleep(REQUEST_DELAY_SEC)

    tickets = all_rows if detailed else _pick_display_price(all_rows)
    site_name = catalog[0].get("siteName") if catalog else None

    return {
        "supplierCode": supplier_code,
        "usingDate": using_date,
        "siteName": site_name,
        "ticketCount": len(catalog),
        "tickets": [t for t in tickets if t.get("salePrice") is not None],
    }
