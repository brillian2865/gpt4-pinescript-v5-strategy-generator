#!/usr/bin/env python3
"""
Tests for GPT4 PineScript V5 Strategy Generator.
Runs without API key by mocking OpenAI.
"""

import os
import sys
from unittest.mock import MagicMock, patch

# Ensure project root in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Canned valid V5 response (matches README example structure)
CANNED_RESPONSE = '''{"code": "//@version=5
strategy(\"EMA 9/21 + RSI Filter\", overlay=true,
         initial_capital=10000, commission_type=strategy.commission.percent,
         commission_value=0.05, slippage=2, default_qty_type=strategy.percent_of_equity,
         default_qty_value=10)
fast_len = input.int(9, \"Fast EMA Length\", minval=1)
slow_len = input.int(21, \"Slow EMA Length\", minval=1)
fast_ema = ta.ema(close, fast_len)
slow_ema = ta.ema(close, slow_len)
rsi_val = ta.rsi(close, 14)
long_cond = ta.crossover(fast_ema, slow_ema) and rsi_val > 50
short_cond = ta.crossunder(fast_ema, slow_ema) and rsi_val < 50
if long_cond
    strategy.entry(\"Long\", strategy.long)
if short_cond
    strategy.entry(\"Short\", strategy.short)
strategy.exit(\"Long Exit\", from_entry=\"Long\", loss=close*0.01, profit=close*0.02)
strategy.exit(\"Short Exit\", from_entry=\"Short\", loss=close*0.01, profit=close*0.02)
plot(fast_ema, \"Fast EMA\", color=color.blue)
plot(slow_ema, \"Slow EMA\", color=color.orange)"}'''


def test_validator():
    """Test validator with valid V5 code."""
    from validator import validate_pinescript_v5

    code = """
//@version=5
strategy("Test", overlay=true, initial_capital=10000, commission_type=strategy.commission.percent,
         commission_value=0.05, slippage=2, default_qty_type=strategy.percent_of_equity, default_qty_value=10)
x = ta.ema(close, 9)
if ta.crossover(x, ta.ema(close, 21))
    strategy.entry("Long", strategy.long)
strategy.exit("X", from_entry="Long", loss=10, profit=20)
"""
    valid, errors = validate_pinescript_v5(code)
    assert valid, f"Validator should pass: {errors}"
    print("[PASS] Validator accepts valid V5 code")


def test_validator_rejects_study():
    """Validator must reject study()."""
    from validator import validate_pinescript_v5

    code = "//@version=5\nstudy(\"Bad\")"
    valid, errors = validate_pinescript_v5(code)
    assert not valid and any("study" in e.lower() for e in errors)
    print("[PASS] Validator rejects study()")


def test_parser():
    """Test structured input parser."""
    from parser import parse_strategy_description, build_user_prompt

    desc = "EMA crossover. Fast 9, slow 21. 1% stop loss, 2% take profit. 4H chart."
    parsed = parse_strategy_description(desc)
    assert "raw_text" in parsed
    assert "EMA" in parsed.get("indicators", [])
    assert parsed.get("timeframe")
    assert "stop_loss_pct" in parsed.get("risk_params", {})
    prompt = build_user_prompt(desc)
    assert desc in prompt
    assert "PineScript" in prompt
    print("[PASS] Parser extracts structure")


def test_generator_mock():
    """Test full generation pipeline with mocked API."""
    from generator import generate_strategy

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = CANNED_RESPONSE

    with patch("generator.OpenAI") as mock_openai, patch.dict(os.environ, {"CHUTES_API_KEY": "cpk-test"}):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        code, valid = generate_strategy(
            "EMA crossover, fast 9 slow 21, RSI filter, 1% SL 2% TP",
            model="Qwen/Qwen2.5-Coder-32B-Instruct",
            validation_enabled=True,
        )

    assert "//@version=5" in code
    assert "strategy(" in code
    assert "strategy.entry" in code
    assert "strategy.exit" in code
    assert "from_entry" in code
    assert valid, "Canned response should pass validation"
    print("[PASS] Generator mock pipeline produces valid output")


def test_cli_help():
    """CLI --help works."""
    import subprocess
    r = subprocess.run(
        [sys.executable, "generate.py", "--help"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert r.returncode == 0
    assert "preview" in r.stdout
    assert "save" in r.stdout
    print("[PASS] CLI --help works")


def test_cli_no_description():
    """CLI fails gracefully without description or API key."""
    import subprocess
    proj = os.path.dirname(os.path.abspath(__file__))
    env = os.environ.copy()
    env.pop("CHUTES_API_KEY", None)
    env.pop("OPENAI_API_KEY", None)
    # Run from /tmp so load_dotenv() won't find .env
    r = subprocess.run(
        [sys.executable, os.path.join(proj, "generate.py"), "--mode", "preview"],
        cwd="/tmp",
        capture_output=True,
        text=True,
        timeout=5,
        env=env,
        stdin=subprocess.DEVNULL,
    )
    assert r.returncode != 0
    err = r.stderr.lower()
    assert "description" in err or "chutes" in err or "openai" in err
    print("[PASS] CLI fails without description or API key")


def test_regeneration_on_validation_failure():
    """Generator regenerates when first response fails validation."""
    import logging
    from generator import generate_strategy

    bad_response = '{"code": "study(\\"bad\\")"}'  # Fails: study() deprecated
    good_response = CANNED_RESPONSE

    responses = [bad_response, good_response]
    call_count = [0]

    def mock_create(*args, **kwargs):
        idx = min(call_count[0], len(responses) - 1)
        call_count[0] += 1
        r = MagicMock()
        r.choices = [MagicMock()]
        r.choices[0].message.content = responses[idx]
        return r

    # Suppress expected "Validation attempt N failed" warning during test
    logging.getLogger("generator").setLevel(logging.ERROR)
    try:
        with patch("generator.OpenAI") as mock_openai, patch.dict(os.environ, {"CHUTES_API_KEY": "cpk-test"}):
            mock_client = MagicMock()
            mock_client.chat.completions.create = mock_create
            mock_openai.return_value = mock_client

            code, valid = generate_strategy(
                "test",
                model="test-model",
                validation_enabled=True,
                max_regeneration_attempts=2,
            )
    finally:
        logging.getLogger("generator").setLevel(logging.WARNING)

    assert call_count[0] >= 2, "Should have called API at least twice (1 fail + 1 retry)"
    assert valid
    assert "//@version=5" in code
    assert "study" not in code
    print("[PASS] Regeneration on validation failure")


def run_all():
    """Run all tests."""
    tests = [
        test_validator,
        test_validator_rejects_study,
        test_parser,
        test_generator_mock,
        test_regeneration_on_validation_failure,
        test_cli_help,
        test_cli_no_description,
    ]
    failed = []
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failed.append((t.__name__, str(e)))
        except Exception as e:
            failed.append((t.__name__, str(e)))
    if failed:
        print("\n[FAILED]")
        for name, err in failed:
            print(f"  {name}: {err}")
        sys.exit(1)
    print("\n[OK] All tests passed")


if __name__ == "__main__":
    run_all()
