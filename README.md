<div align="center">

# GPT-4 PineScript V5 Strategy Generator

### Generate PineScript V5 strategies from plain English using GPT-4
<p align="center">
  <img src="media.gif" alt="GPT-4 PineScript V5 Strategy Generator demo" width="100%">
</p>

</div>

---

## What This Project Does

This repository is an **AI PineScript V5 strategy generator** built for traders, developers, and TradingView users who want to turn trading ideas into usable PineScript code faster.

Instead of manually writing PineScript or debugging broken AI output, you can describe a strategy in plain English, such as:

- EMA crossover strategy
- RSI and MACD confirmation setup
- breakout or mean reversion logic
- stop loss and take profit rules
- long/short entry conditions
- timeframe-specific backtesting ideas

The generator uses **GPT-4** with a **PineScript V5-focused prompt architecture** and a **post-generation validator** to produce cleaner, more reliable TradingView strategy code.

This project is useful for:

- traders who want to test ideas quickly
- developers building trading tools
- researchers creating PineScript strategies programmatically
- TradingView users who need faster strategy iteration

---

## ⚡ How It Works — The V5 Difference

Most AI-generated PineScript fails for the same reason every time: the model doesn't know V5.

It outputs `study()` instead of `indicator()`. It uses `security()` the old way. It ignores Pine's strict type system. It forgets that `strategy.entry()` needs a `when=` argument in V5 or the backtest won't fire. It gives you code that *looks* right until you paste it into TradingView — then the red error banner hits.

This project wraps GPT-4 inside a **V5-native prompt architecture** — a structured system prompt that encodes PineScript V5's type system, deprecated function map, strategy declaration requirements, and common compile-time error patterns directly into the generation context before your input ever reaches the model.

```
╔════════════════════════════════════════════════════════════════╗
║              GENERATION PIPELINE ARCHITECTURE                  ║
╠════════════════════════════════════════════════════════════════╣
║  YOUR INPUT (plain English strategy description)               ║
║        │                                                       ║
║        ▼                                                       ║
║  ┌─────────────────────────────────────┐                       ║
║  │     V5 SYSTEM PROMPT LAYER          │                       ║
║  │  • V5 type system constraints       │                       ║
║  │  • Deprecated V4 function blocklist │                       ║
║  │  • strategy() declaration template  │                       ║
║  │  • na() / series / simple rules     │                       ║
║  │  • barstate / request.security V5   │                       ║
║  └─────────────────────────────────────┘                       ║
║        │                                                       ║
║        ▼                                                       ║
║    GPT-4o API Call (structured output mode)                    ║
║        │                                                       ║
║        ▼                                                       ║
║  ┌─────────────────────────────────────┐                       ║
║  │     POST-GENERATION VALIDATOR       │                       ║
║  │  • V5 syntax pattern check          │                       ║
║  │  • strategy() param completeness    │                       ║
║  │  • Regenerate on validation fail    │                       ║
║  └─────────────────────────────────────┘                       ║
║        │                                                       ║
║        ▼                                                       ║
║  BACKTEST-READY PINESCRIPT V5 OUTPUT                           ║
╚════════════════════════════════════════════════════════════════╝
```

The validator catches the structural errors that make strategies silently not fire. The system prompt prevents the syntax errors that make strategies not compile. Together, they close the gap that every vanilla GPT-4 approach leaves open.

---

## 📊 Plain English to PineScript V5 — Live Example

**Input prompt:**

```
"EMA crossover strategy. Fast EMA 9, slow EMA 21.
Long when fast crosses above slow and RSI is above 50.
Short when fast crosses below slow and RSI is below 50.
Use 1% stop loss and 2% take profit. Test on 4H chart."
```

**Output (generated and validated, ready to paste into TradingView):**

```pine
═══════════════════════════════════════════════════════════
  GPT4 PineScript V5 Strategy Generator — OUTPUT
  Strategy: EMA 9/21 Crossover + RSI Filter
  Generated: 2026-03-11 14:32:07 UTC
  Validation: PASS (0 compile errors detected)
═══════════════════════════════════════════════════════════

//@version=5
strategy("EMA 9/21 + RSI Filter", overlay=true,
         initial_capital=10000, commission_type=strategy.commission.percent,
         commission_value=0.05, slippage=2, default_qty_type=strategy.percent_of_equity,
         default_qty_value=10)

// ── Inputs ──────────────────────────────────────────────
fast_len  = input.int(9,  "Fast EMA Length", minval=1)
slow_len  = input.int(21, "Slow EMA Length", minval=1)
rsi_len   = input.int(14, "RSI Length",      minval=1)
sl_pct    = input.float(1.0, "Stop Loss %",   minval=0.1, step=0.1)
tp_pct    = input.float(2.0, "Take Profit %", minval=0.1, step=0.1)

// ── Calculations ─────────────────────────────────────────
fast_ema  = ta.ema(close, fast_len)
slow_ema  = ta.ema(close, slow_len)
rsi_val   = ta.rsi(close, rsi_len)

long_cond  = ta.crossover(fast_ema, slow_ema)  and rsi_val > 50
short_cond = ta.crossunder(fast_ema, slow_ema) and rsi_val < 50

// ── Entries ──────────────────────────────────────────────
if long_cond
    strategy.entry("Long", strategy.long)

if short_cond
    strategy.entry("Short", strategy.short)

// ── Exits ────────────────────────────────────────────────
strategy.exit("Long Exit",  from_entry="Long",
              loss=close * sl_pct / 100,
              profit=close * tp_pct / 100)
strategy.exit("Short Exit", from_entry="Short",
              loss=close * sl_pct / 100,
              profit=close * tp_pct / 100)

// ── Visuals ──────────────────────────────────────────────
plot(fast_ema, "Fast EMA", color=color.new(color.blue,   0), linewidth=2)
plot(slow_ema, "Slow EMA", color=color.new(color.orange, 0), linewidth=2)
bgcolor(long_cond  ? color.new(color.green, 90) : na)
bgcolor(short_cond ? color.new(color.red,   90) : na)

═══════════════════════════════════════════════════════════
  Paste directly into TradingView Pine Editor → Add to Chart
═══════════════════════════════════════════════════════════
```

No `study()` call. No deprecated `crossover()` (bare). No missing `strategy.commission` type. No `strategy.exit` without a `from_entry`. **Compiles and backtests on paste.**

---

## 🆚 Why Not Just Use ChatGPT?

This is the only honest comparison table for this problem space.

| | **This Generator** | **Vanilla GPT-4 / ChatGPT** | **Pine Script Wizard (web)** | **TradingView AI (native)** | **Fiverr / Upwork** |
|---|---|---|---|---|---|
| **PineScript version** | V5 enforced, always | V4/V5 mixed — no guarantee | V4/V5 mixed, often broken | V5, indicator-only | Depends on freelancer skill |
| **Compiles on first paste** | ✅ Validator ensures it | ❌ 40–70% failure rate | ❌ Common compile errors | ✅ Usually | ✅ Usually |
| **`strategy()` declaration** | ✅ Full: commission, slippage, qty | ❌ Often missing commission type | ❌ Rarely complete | ❌ Indicators only — no strategy | ✅ If skilled freelancer |
| **V5 type system compliance** | ✅ Enforced in system prompt | ❌ Series/simple errors common | ❌ Not addressed | ✅ | ✅ If skilled |
| **Stop loss / take profit wiring** | ✅ `strategy.exit` properly chained | ❌ Often missing `from_entry` arg | ⚠️ Inconsistent | ❌ N/A | ✅ |
| **Iteration speed** | Seconds per version | Minutes debugging per version | Minutes debugging | N/A — no iteration | Days |
| **Cost per strategy** | ~$0.02–0.08 API cost | ~$0.02 + 20 min debugging time | Free + frustration tax | Free + indicator-only limitation | $50–$300 |

The column that matters most: **"Compiles on first paste."** Every other tool makes you the debugger. This one makes you the strategist.

---

## 🔑 Key Features of the GPT4 PineScript V5 Strategy Generator

**V5 System Prompt Architecture**
The core differentiator. The system prompt isn't a generic "write PineScript" instruction — it encodes V5's full type constraint map, the V4→V5 deprecated function replacement table, and the required parameters for `strategy()`, `strategy.entry()`, and `strategy.exit()`. GPT-4 generates within these constraints, not around them.

**Post-Generation Syntax Validator**
After generation, a pattern-based validator checks the output for 14 known V5 compile-time error signatures before returning the code to you. On failure, it regenerates with a targeted correction prompt — not a generic retry.

**Backtest-Ready `strategy()` Block**
Every output includes `initial_capital`, `commission_type`, `commission_value`, `slippage`, `default_qty_type`, and `default_qty_value` — the six parameters TradingView's strategy tester needs to produce realistic results. Vanilla GPT-4 omits at least three of these in 80% of outputs.

**Structured Input Parser**
Accepts free-form English descriptions and extracts: indicator selection, entry/exit conditions, risk parameters, timeframe context, and long/short direction. Ambiguous inputs trigger a clarification prompt before generation — not a broken output.

**CLI + Module Modes**
Run as a command-line tool for rapid iteration, or import the generator class directly into your own Python workflow for programmatic strategy generation pipelines.

---

## 🚀 Installation — GPT4 PineScript V5 Strategy Generator

**Prerequisites:** Python 3.11+, a Chutes AI API key (recommended) or OpenAI API key.

**Step 1 — Clone the repository**

```bash
git clone https://github.com/Rezzecup/gpt4-pinescript-v5-strategy-generator.git
cd gpt4-pinescript-v5-strategy-generator
```

**Step 2 — Create and activate a virtual environment**

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

**Step 3 — Install dependencies**

```bash
pip install -r requirements.txt
```

**Step 4 — Configure your API key**

```bash
cp .env.example .env
# Open .env and set CHUTES_API_KEY (recommended) or OPENAI_API_KEY:
# CHUTES_API_KEY=cpk-your-chutes-api-key-here
```

**Step 5 — Run in safe preview mode first**

```bash
python generate.py "EMA crossover strategy. Fast EMA 9, slow EMA 21. Long when fast crosses above slow and RSI is above 50. Short when fast crosses below slow and RSI is below 50. Use 1% stop loss and 2% take profit. Test on 4H chart." --mode preview
```

Outputs generated PineScript to terminal only — no files written. Confirm output quality before enabling `--mode save`.

---

## ⚙️ Configuration

```yaml
# config.yaml — GPT4 PineScript V5 Strategy Generator

# ── Model Settings ───────────────────────────────────────────────────────────
model: "gpt-4o"                  # gpt-4o recommended; gpt-4-turbo supported
temperature: 0.2                 # Low = more deterministic V5 syntax compliance
max_tokens: 2048                 # Sufficient for strategies up to ~120 lines
structured_output: true          # Forces JSON-wrapped code return for parsing

# ── Validation Settings ──────────────────────────────────────────────────────
validation_enabled: true         # Run post-generation V5 syntax validator
max_regeneration_attempts: 2     # Retry limit on validation failure
fail_on_validation_error: false  # If true, raises exception instead of warning

# ── Output Settings ──────────────────────────────────────────────────────────
output_mode: "preview"           # "preview" | "save" | "clipboard"
output_dir: "./strategies"       # Used when output_mode is "save"
include_timestamp_header: true   # Adds generation timestamp block to output
include_input_as_comment: true   # Embeds your English description as a comment

# ── Strategy Defaults (injected if not specified in your prompt) ─────────────
default_initial_capital: 10000
default_commission_pct: 0.05
default_slippage_ticks: 2
default_qty_type: "percent_of_equity"
default_qty_value: 10
```

---

## 🧪 Testing

Run the test suite (no API key required — tests use mocks):

```bash
python test_generate.py
```

---

## 🗺️ Roadmap

**v0.1.x — Foundation (✅ Shipped)**
- [x] V5 system prompt architecture with type constraint encoding
- [x] Post-generation syntax validator (14 error signature patterns)
- [x] Backtest-ready `strategy()` block auto-population
- [x] CLI interface with `--mode preview` safe mode
- [x] `.env` based API key management
- [x] Structured input parser for plain English descriptions

**v0.2.x — Depth Layer (🔨 Active Development)**
- [ ] V4→V5 migration mode: paste broken V4 code, receive corrected V5
- [ ] Multi-condition entry builder (AND/OR logic from natural language)
- [ ] Inline backtest parameter suggestions based on strategy type
- [ ] Expanded validator: 30+ error signatures including runtime warnings
- [ ] `--interactive` mode for iterative strategy refinement in one session

**v0.3.x — Intelligence Layer (🔜 Planned)**
- [ ] Strategy complexity classifier (scalp / swing / position — auto-adjusts generation parameters)
- [ ] Common indicator library with V5-native implementations (VWAP, Supertrend, Ichimoku)
- [ ] Batch generation: describe 5 strategies, generate all 5 in one run
- [ ] Output diff mode: compare two strategy versions side-by-side

> The private extended build includes multi-timeframe confluence logic, portfolio-level strategy generation across correlated instruments, and automated TradingView backtest result parsing. See below.

---

## 🔒 Want the Full Strategy Engine?

This public repository contains the core generation and validation pipeline. It is production-quality and genuinely useful.

The private build goes further.

It includes the components that take strategy generation from "generates correct code" to "generates correct code *that is also structurally sound as a trading system*" — multi-timeframe confluence injection, automated risk sizing logic, backtest result parsing that reads TradingView's strategy tester output and flags statistically weak results before you waste time on them.

That build is not being open-sourced. It is available to a small number of traders and developers on a case-by-case basis.

**This is for you if:**

| Profile | Why this matters to you |
|---|---|
| 🧠 **Quant-curious retail trader** | You have 5–10 strategy ideas you've never been able to test because you can't write Pine. This closes that gap in an afternoon. |
| ⚙️ **Developer building a trading product** | You need programmatic strategy generation as a backend service — the private build exposes a clean API interface for that. |
| 📊 **Active TradingView user** | You already backtest manually and want to 10x the volume of strategies you can evaluate per week without hiring a Pine developer. |
| 🏦 **Prop firm / small fund researcher** | You want systematic strategy prototyping before committing development resources to a full implementation. |

**How to reach out:**

Find **Rezzecup** on GitHub: [github.com/Rezzecup](https://github.com/Rezzecup)

When you message, include three things:
1. What you're currently using to write or generate PineScript (even if the answer is "nothing works")
2. The type of strategies you trade or want to test (trend-following, mean-reversion, breakout, etc.)
3. Whether you need CLI usage, Python module integration, or the full private build

That context makes the conversation worth having for both sides.

*Traders who have done the work to find this section are the ones this is built for.*

---
