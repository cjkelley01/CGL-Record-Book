import unittest
from scripts.analytics.weekly_forecast import simulate
from scripts.replay_historical_seasons import historical_bracket

def season():
    teams=[{"team_id":i,"team_name":str(i)} for i in range(1,7)]
    matches=[]
    for week in range(1,5):
        for a,b in ((1,2),(3,4),(5,6)):
            matches.append({"stage":"regular_season","decided":True,"matchup_period":week,
                            "home_team_id":a,"away_team_id":b,
                            "home_score":100+a,"away_score":100+b})
    return {"season":2024,"teams":teams,"matchups":matches,"settings":{"playoff_team_count":6}}

class HistoricalBracketTests(unittest.TestCase):
    def test_rejects_incompatible_historical_bracket(self):
        s=season()
        bracket,champ,reason=historical_bracket(s,{"playoffs":set(range(1,7)),
            "rank":{i:i for i in range(1,7)}})
        self.assertIsNone(bracket)
        self.assertIsNotNone(reason)
    def test_accepts_verified_rounds_and_champion(self):
        s=season()
        for rnd,week,pairs in ((1,15,((3,6),(4,5))), (2,16,((1,4),(2,3))), (3,17,((1,2),))):
            for a,b in pairs:
                s["matchups"].append({"stage":"championship_playoffs","playoff_round":rnd,
                    "scoring_periods":[week],"home_team_id":a,"away_team_id":b,
                    "winner":"HOME","decided":True})
        b,c,reason=historical_bracket(s,{"playoffs":set(range(1,7)),
            "rank":{i:i for i in range(1,7)}})
        self.assertEqual(b,((15,),(16,),(17,)))
        self.assertEqual(c,1)
        self.assertIsNone(reason)
    def test_configurable_final_round_and_probability_invariants(self):
        s=season()
        means={i:{w:100+i for w in (15,16,17)} for i in range(1,7)}
        r=simulate(s,means,trials=100,seed=5,playoff_weeks=((15,),(16,),(17,)))
        self.assertAlmostEqual(sum(t["championship_probability"] for t in r["teams"]),1)
        self.assertTrue(all(t["championship_probability"]<=t["playoff_probability"] for t in r["teams"]))
if __name__=="__main__":unittest.main()
