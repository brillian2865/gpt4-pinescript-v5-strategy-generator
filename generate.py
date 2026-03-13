#!/usr/bin/env python3
"""
GPT4 PineScript V5 Strategy Generator — CLI entry point.
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

from generator import generate_strategy

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config(path: str = "config.yaml") -> dict:
    """Load config.yaml."""
    p = Path(path)
    if not p.is_absolute():
        p = Path(__file__).resolve().parent / path
    if not p.exists():
        return {}
    with open(p) as f:
        return yaml.safe_load(f) or {}


def format_output(
    code: str,
    description: str,
    valid: bool,
    include_timestamp: bool = True,
    include_input_comment: bool = True,
) -> str:
    """Format final output with header."""
    lines = []
    if include_timestamp:
        lines.append("═" * 55)
        lines.append("  GPT4 PineScript V5 Strategy Generator — OUTPUT")
        lines.append(f"  Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        lines.append(f"  Validation: {'PASS' if valid else 'FAIL'} ({0 if valid else 'compile errors detected'})")
        lines.append("═" * 55)
        lines.append("")
    if include_input_comment and description:
        lines.append(f"// Input: {description[:80]}{'...' if len(description) > 80 else ''}")
        lines.append("")
    lines.append(code)
    lines.append("")
    lines.append("═" * 55)
    lines.append("  Paste directly into TradingView Pine Editor → Add to Chart")
    lines.append("═" * 55)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="GPT4 PineScript V5 Strategy Generator — Plain English to backtest-ready PineScript V5",
    )
    parser.add_argument(
        "description",
        nargs="?",
        default=None,
        help="Strategy description in plain English (or pass via stdin)",
    )
    parser.add_argument(
        "--mode",
        choices=["preview", "save"],
        default="preview",
        help="preview: print to terminal; save: write to strategies/",
    )
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    args = parser.parse_args()

    config = load_config(args.config)
    if not config:
        logger.error("Config file not found: %s. Create from README.", args.config)
        sys.exit(1)

    # Get description
    desc = args.description
    if not desc and not sys.stdin.isatty():
        desc = sys.stdin.read().strip()
    if not desc:
        logger.error("No strategy description. Usage: python generate.py 'EMA crossover strategy...' --mode preview")
        sys.exit(1)

    api_key = os.getenv("CHUTES_API_KEY", "").strip() or os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        logger.error("CHUTES_API_KEY or OPENAI_API_KEY not set. Add to .env file.")
        sys.exit(1)

    use_chutes = bool(os.getenv("CHUTES_API_KEY", "").strip())
    m = config.get("model")
    if m is None:
        model = "Qwen/Qwen2.5-Coder-32B-Instruct" if use_chutes else "gpt-4o"
    else:
        model = m if isinstance(m, str) else m.get("model", "gpt-4o")

    temperature = config.get("temperature", 0.2)
    max_tokens = config.get("max_tokens", 2048)
    structured_output = config.get("structured_output", True)
    validation_enabled = config.get("validation_enabled", True)
    max_regen = config.get("max_regeneration_attempts", 2)
    include_ts = config.get("include_timestamp_header", True)
    include_input = config.get("include_input_as_comment", True)
    output_dir = Path(config.get("output_dir", "./strategies"))

    logger.info("Generating PineScript V5 strategy...")
    code, valid = generate_strategy(
        desc,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        structured_output=structured_output,
        validation_enabled=validation_enabled,
        max_regeneration_attempts=max_regen,
        use_chutes=use_chutes,
    )

    output = format_output(code, desc, valid, include_ts, include_input)

    if args.mode == "preview":
        print(output)
        if not valid:
            logger.warning("Validation reported issues. Review output before pasting to TradingView.")
        return

    # save mode
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    # Sanitize filename from description
    base = "strategy"
    if desc:
        base = "".join(c if c.isalnum() or c in " -_" else "_" for c in desc[:40]).strip() or "strategy"
    fname = f"{base}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pine"
    out_path = output_dir / fname
    with open(out_path, "w") as f:
        f.write(output)
    logger.info("Saved to %s", out_path)
    if not valid:
        logger.warning("Validation reported issues. Review before pasting to TradingView.")


if __name__ == "__main__":
    main()
