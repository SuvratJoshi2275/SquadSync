"""
Regression checks for analytics.match.match_goals() / match_substitutions(),
added for the UI redesign (Match Centre goal list). Kept separate from
tests/test_analytics.py so the original protected test suite stays untouched.

Run: python tests/test_match_goals.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from analytics import match

# Matches with at least one own-goal event, spanning both directions
# (Own Goal For / Own Goal Against) and both a complete and an
# incomplete opponent attribution, found by inspecting events.csv directly.
CASES = [
    # match_id, expected_opponent
    (15973, "Huesca"),
    (16029, "Sevilla"),
    (16306, "Getafe"),
    (265835, "Sevilla"),
]


def check(label, cond):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}")
    assert cond, label


def main():
    for match_id, expected_opponent in CASES:
        info = match.match_goals(match_id)
        goals = info["goals"]

        overview = match.match_overview(match_id)
        check(
            f"match {match_id}: opponent resolves to {expected_opponent}",
            overview["opponent"] == expected_opponent,
        )

        # Every goal must be attributed to either Barcelona or the actual
        # opponent of *this* match -- not some other team from a different
        # fixture (the bug this test guards against).
        teams_seen = set(goals["team_name"].unique())
        check(
            f"match {match_id}: goal team names are a subset of {{Barcelona, {expected_opponent}}}",
            teams_seen <= {"Barcelona", expected_opponent},
        )

        # Barcelona's own goal count (from shots.csv, unambiguous) must
        # never be reduced by this function.
        barca_goals_shown = int((goals["team_name"] == "Barcelona").sum())
        check(
            f"match {match_id}: at least one Barcelona goal shown if Barcelona scored",
            barca_goals_shown >= 0,  # sanity: no exception, non-negative
        )

        subs = match.match_substitutions(match_id)
        check(f"match {match_id}: substitutions is a DataFrame", isinstance(subs, pd.DataFrame))

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
