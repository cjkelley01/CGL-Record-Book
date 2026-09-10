# CGL Record Book Scope

## Historical boundary

The official CGL statistical era begins in 2024. Earlier league history will not be mixed into calculated records unless it can be verified from a reliable source.

A separate **League Legend** section may preserve pre-2024 stories without presenting them as part of the verified statistical database.

## Source-of-truth order

1. Preserved raw ESPN responses
2. Normalized tables generated from those responses
3. Explicit commissioner corrections, stored with a reason and audit trail
4. Narrative material clearly labeled as legend or recollection

## Planned entities

- Manager: a person across seasons
- Franchise: the continuing competitive identity assigned by league policy
- Team season: one ESPN team in one season
- Matchup: regular-season or playoff contest
- Weekly score and standing
- Roster snapshot, draft selection, and transaction
- Season award and record-book entry
- Commissioner correction

Manager, franchise, and team-season identities remain separate. Team names can change, managers can enter or leave, and ESPN team IDs may not be stable permanent identity keys.

## Planned record categories

- Championships, runner-up finishes, playoff appearances, byes, playoff wins, and seed performance
- Wins, losses, ties, winning percentage, points for, points against, and streaks
- Weekly scoring records, margins, closest wins, highest-scoring losses, lowest-scoring wins, and combined score
- Head-to-head records
- Draft, transaction, roster, and lineup records where historical data supports them

## Verification rules

- Regular season and playoffs are classified from season-specific ESPN settings, not hard-coded week assumptions.
- Scores retain ESPN's original numeric precision.
- Ties remain ties unless an ESPN tiebreak result is explicitly represented.
- Vacant or renamed teams do not silently create new managers.
- Every calculated record is traceable to a source season and matchup.
- Commissioner corrections never overwrite the raw ESPN archive.
