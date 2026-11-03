import unittest
from scripts.replay_historical_seasons import replay,truth

def fixture():
    ids=range(1,7)
    games=[]
    for week in range(1,5):
        for a,b in ((1,2),(3,4),(5,6)):
            games.append({"stage":"regular_season","decided":True,"matchup_period":week,
                "home_team_id":a,"away_team_id":b,"home_score":100+a,"away_score":100+b})
    return {"season":2024,"teams":[{"team_id":i,"team_name":str(i)} for i in ids],"matchups":games}
class ReplayTests(unittest.TestCase):
    def test_future_outcomes_cannot_change_predictions(self):
        s=fixture()
        t=[{"season":2024,"week":w,"team_id":i,"reconciled":"true","projected":100+i}
           for w in range(1,5) for i in range(1,7)]
        a,_=replay([s],t,cutoffs=(2,),trials=20,weights=(0,))
        changed=fixture()
        for g in changed["matchups"]:
            if g["matchup_period"]>2:
                g["home_score"]=200;g["away_score"]=1
        b,_=replay([changed],t,cutoffs=(2,),trials=20,weights=(0,))
        self.assertEqual([r["playoff_probability"] for r in a],
                         [r["playoff_probability"] for r in b])
        self.assertEqual([r["championship_probability"] for r in a],
                         [r["championship_probability"] for r in b])
    def test_future_espn_projection_cannot_change_predictions(self):
        s=fixture()
        t=[{"season":2024,"week":w,"team_id":i,"reconciled":"true","projected":100+i}
           for w in range(1,5) for i in range(1,7)]
        a,_=replay([s],t,cutoffs=(2,),trials=20,weights=(0,))
        for r in t:
            if r["week"]>2:r["projected"]=999
        b,_=replay([s],t,cutoffs=(2,),trials=20,weights=(0,))
        self.assertEqual(a,b)
    def test_incomplete_season_excluded(self):
        s=fixture();s["matchups"][-1]["decided"]=False
        a,skips=replay([s],[],cutoffs=(2,),trials=10)
        self.assertFalse(a);self.assertEqual(skips[0]["reason"],"regular season incomplete")
if __name__=="__main__":unittest.main()
