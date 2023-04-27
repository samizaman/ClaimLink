from decimal import Decimal

MIN_SCORE = Decimal("0")
MAX_SCORE = Decimal("100")


def normalize_score(score, min_score, max_score):
    return (score - min_score) / (max_score - min_score)
