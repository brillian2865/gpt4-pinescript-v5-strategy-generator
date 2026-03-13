"""
Post-Generation Syntax Validator — 14 V5 error signature patterns.
Fails on deprecated V4 syntax or missing required V5 structure.
"""

import re
from typing import List, Tuple


# 14 validation patterns: (pattern, error_message, is_negative=check for absence)
VALIDATION_PATTERNS: List[Tuple[re.Pattern, str, bool]] = [
    # 1. Must have @version=5
    (re.compile(r"//@version=5|@version=5", re.I), "Missing //@version=5", True),
    # 2. Must NOT use study()
    (re.compile(r"\bstudy\s*\("), "Deprecated: use strategy() or indicator() instead of study()", False),
    # 3. Must NOT use bare security()
    (re.compile(r"(?<!request\.)\bsecurity\s*\("), "Deprecated: use request.security() not security()", False),
    # 4. Must NOT use iff()
    (re.compile(r"\biff\s*\("), "Deprecated: use ternary ? : instead of iff()", False),
    # 5. Must have strategy() call
    (re.compile(r'\bstrategy\s*\('), "Missing strategy() declaration", True),
    # 6. strategy() should have commission_type
    (re.compile(r"commission_type\s*="), "strategy() missing commission_type", True),
    # 7. strategy() should have commission_value
    (re.compile(r"commission_value\s*="), "strategy() missing commission_value", True),
    # 8. strategy() should have initial_capital or default_qty
    (re.compile(r"initial_capital\s*="), "strategy() missing initial_capital", True),
    # 9. strategy.exit must have from_entry
    (re.compile(r"strategy\.exit\s*\([^)]*from_entry\s*=", re.DOTALL), "strategy.exit() should include from_entry", True),
    # 10. Must NOT use transp= (deprecated)
    (re.compile(r"\btransp\s*="), "Deprecated: use color.new() instead of transp", False),
    # 11. Use ta. for crossover/crossunder
    (re.compile(r"(?<!ta\.)(?<!\.)crossover\s*\("), "Use ta.crossover() not bare crossover()", False),
    (re.compile(r"(?<!ta\.)(?<!\.)crossunder\s*\("), "Use ta.crossunder() not bare crossunder()", False),
    # 12. strategy.entry must be present if strategy.exit exists
    (re.compile(r"strategy\.entry\s*\("), "Should use strategy.entry() for entries", True),
    # 13. Use input.int/input.float not old input
    # Allow both - input() is still valid in V5 for some cases; input.int/float preferred
    # 14. No old offset() standalone
    (re.compile(r"(?<!\.)offset\s*\("), "Deprecated: offset() - use ta.valuewhen or shift", False),
]


def validate_pinescript_v5(code: str) -> Tuple[bool, List[str]]:
    """
    Validate PineScript V5 code against 14 error patterns.
    Returns (is_valid, list of error messages).
    """
    errors: List[str] = []
    code_clean = code.strip()

    for pattern, msg, must_be_present in VALIDATION_PATTERNS:
        found = bool(pattern.search(code_clean))
        if must_be_present:
            if not found:
                errors.append(msg)
        else:
            if found:
                errors.append(msg)

    # Extra: if strategy.exit exists, check from_entry is used
    if "strategy.exit" in code_clean and "from_entry" not in code_clean:
        errors.append("strategy.exit() requires from_entry parameter")

    return len(errors) == 0, errors
