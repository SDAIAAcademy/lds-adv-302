# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Compute every number in the parallel examples of slides/day2.html (a fictional library network,
unrelated to the Shawt case). Standard library only; writes nothing.

    uv run labs/_tools/slide_examples.py
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

# Session 2.1: weighted criteria and how the ranking moves with the weight on impact
WEIGHTS = {"impact": 40, "cost": 30, "readiness": 30}
SCORES = {
    "X lockers": {"impact": 5, "cost": 2, "readiness": 2},
    "Y longer hours": {"impact": 3, "cost": 3, "readiness": 4},
    "Z online hold, do-minimum": {"impact": 2, "cost": 5, "readiness": 5},
}


def weighted(weights):
    return {k: sum(weights[c] * s[c] for c in weights) / 100 for k, s in SCORES.items()}


print("2.1 weighted (40/30/30):", {k: f"{v:.2f}" for k, v in weighted(WEIGHTS).items()})
alt = {"impact": 60, "cost": 20, "readiness": 20}
print("2.1 weighted (60/20/20):", {k: f"{v:.2f}" for k, v in weighted(alt).items()})
# Impact weight w, the rest split equally: X = 5w + 2(1-w), Z = 2w + 5(1-w); X overtakes Z above w
for w in range(0, 101):
    x = weighted({"impact": w, "cost": (100 - w) / 2, "readiness": (100 - w) / 2})
    if x["X lockers"] > x["Z online hold, do-minimum"]:
        print("2.1 X overtakes Z when the impact weight passes", w - 1, "% (equal at 50)")
        break

# Session 2.1: evidence written as evidence
respondents, sample = 333, 900
print(f"2.1 survey: {respondents} of {sample} = {100 * respondents / sample:.1f}%")

# Session 2.2: a share on the wrong base
loans, holds, uncollected = 18_000, 7_500, 2_250
print(f"2.2 uncollected of holds: {100 * uncollected / holds:.1f}%; of all loans: {100 * uncollected / loans:.1f}%")
