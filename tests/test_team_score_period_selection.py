"""Regression tests for ESPN matchup-period selection (no ESPN credentials needed)."""
import unittest
from scripts.audit_team_score_uncertainty import official_scores

def game(period, team, total, weekly=None):
    return {"matchupPeriodId":period, "home":{"teamId":team,"totalPoints":total,
            "pointsByScoringPeriod":weekly or {}}}

class ReconciliationTests(unittest.TestCase):
    def test_does_not_select_other_periods(self):
        payload={"schedule":[game(1,1,90),game(2,1,130),game(3,1,175)]}
        actual,audit=official_scores(payload,2)
        self.assertEqual(actual["1"],(130.0,"single_period_totalPoints_CANDIDATE"))
        self.assertEqual(audit["matching_period_games"],1)

    def test_uses_explicit_multiweek_score(self):
        payload={"schedule":[game(17,2,225,{"17":100.0,"18":125.0})]}
        actual,_=official_scores(payload,17)
        self.assertEqual(actual["2"],(100.0,"pointsByScoringPeriod"))

    def test_uses_explicit_week_eighteen_from_multiweek_period(self):
        payload={"schedule":[game(17,2,225,{"17":100.0,"18":125.0})]}
        actual,_=official_scores(payload,18)
        self.assertEqual(actual["2"],(125.0,"pointsByScoringPeriod"))

    def test_multiweek_missing_explicit_week_fails_closed(self):
        payload={"schedule":[game(17,2,225,{"16":90.0,"18":135.0})]}
        actual,_=official_scores(payload,17)
        self.assertEqual(actual,{})

if __name__=="__main__":
    unittest.main()
