"""
Structured Input Parser — Extracts strategy parameters from plain English.
"""

import re
from typing import Dict, Any, Optional


def parse_strategy_description(text: str) -> Dict[str, Any]:
    """
    Parse free-form English description into structured fields.
    Returns dict with: raw_text, indicators, conditions, risk_params, timeframe, direction.
    """
    text = text.strip()
    if not text:
        return {"raw_text": "", "needs_clarification": True}

    result: Dict[str, Any] = {
        "raw_text": text,
        "indicators": [],
        "entry_conditions": [],
        "exit_conditions": [],
        "risk_params": {},
        "timeframe": None,
        "direction": "both",  # long, short, both
        "needs_clarification": False,
    }

    # Extract timeframe (4H, 1H, 15m, daily, etc.)
    tf_pattern = r"\b(1m|5m|15m|30m|1H|4H|1D|1W|1M|daily|weekly|4h|1h)\b"
    match = re.search(tf_pattern, text, re.I)
    if match:
        result["timeframe"] = match.group(1)

    # Extract common indicators
    indicator_keywords = ["EMA", "SMA", "RSI", "MACD", "Bollinger", "VWAP", "Supertrend", "ATR", "stochastic"]
    for kw in indicator_keywords:
        if kw.lower() in text.lower():
            result["indicators"].append(kw)

    # Extract numbers for EMA lengths, RSI, etc.
    ema_match = re.search(r"EMA\s*(\d+)\s*/\s*(\d+)|EMA\s*(\d+)\s*,\s*(\d+)|fast\s*(\d+)\s*slow\s*(\d+)", text, re.I)
    if ema_match:
        nums = [g for g in ema_match.groups() if g]
        if len(nums) >= 2:
            result["risk_params"]["ema_fast"] = int(nums[0])
            result["risk_params"]["ema_slow"] = int(nums[1])

    # Stop loss / take profit
    sl_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*stop\s*loss|stop\s*loss\s*(\d+(?:\.\d+)?)\s*%", text, re.I)
    if sl_match:
        result["risk_params"]["stop_loss_pct"] = float(sl_match.group(1) or sl_match.group(2))
    tp_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*take\s*profit|take\s*profit\s*(\d+(?:\.\d+)?)\s*%", text, re.I)
    if tp_match:
        result["risk_params"]["take_profit_pct"] = float(tp_match.group(1) or tp_match.group(2))

    # Long/short
    if "long only" in text.lower() or "long entries" in text.lower():
        result["direction"] = "long"
    elif "short only" in text.lower() or "short entries" in text.lower():
        result["direction"] = "short"

    return result


def build_user_prompt(description: str, parsed: Optional[Dict[str, Any]] = None) -> str:
    """
    Build the user prompt for GPT. Adds structure hints if parsed data available.
    """
    if parsed is None:
        parsed = parse_strategy_description(description)

    base = f"Generate a complete, backtest-ready PineScript V5 strategy from this description:\n\n{description}\n\n"
    base += "Requirements: Use //@version=5, strategy() with full parameters (initial_capital, commission_type, commission_value, slippage, default_qty_type, default_qty_value), strategy.entry with conditional blocks, strategy.exit with from_entry. Use ta. prefix for indicators. Output ONLY the PineScript code."
    return base
