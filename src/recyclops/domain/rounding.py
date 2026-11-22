import math


def round_half_up(value: float) -> int:
    """Python's round() rounds halves to even (round(52.5) == 52); indices and percentages read 0.5 as up."""
    return math.floor(value + 0.5)
