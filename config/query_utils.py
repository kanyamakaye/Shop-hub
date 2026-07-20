def is_decimal_string(value):
    """True if `value` (typically a raw querystring param) is safe to pass into a
    numeric filter — a non-negative number with at most one decimal point."""
    return value.replace('.', '', 1).isdigit()
