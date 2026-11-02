import unittest
from scripts.replay_historical_weights import replay
class ChronologyTests(unittest.TestCase):
    def test_no_current_week_training(self):
        teams=[]
        games=[]
        for week in range(1,5):
            for tid,score in ((1,100+week),(2,90)):
                teams.append({"season":2024,"week":week,"team_id":tid,"reconciled":"true",
                              "projected":100 if tid==1 else 90,"reconstructed_actual":score})
            games.append({"season":2024,"week":week,"matchup_id":week,"home_team":1,
                          "away_team":2,"home_win":1})
        rows,selected=replay(teams,games,1)
        self.assertEqual(len(rows),33)
        self.assertEqual([r["week"] for r in selected],[3,4])
        self.assertEqual([r["prior_training_matchups"] for r in selected],[1,2])
    def test_current_week_outcome_cannot_change_own_probability(self):
        teams=[]
        for week in (1,2):
            for tid in (1,2):
                teams.append({"season":2024,"week":week,"team_id":tid,"reconciled":"true",
                              "projected":100,"reconstructed_actual":110 if tid==1 else 90})
        g={"season":2024,"week":2,"matchup_id":2,"home_team":1,"away_team":2,"home_win":1}
        a,_=replay(teams,[g],1)
        b,_=replay(teams,[dict(g,home_win=0)],1)
        self.assertEqual([r["home_probability"] for r in a],
                         [r["home_probability"] for r in b])
if __name__=="__main__":unittest.main()
