"""Optimal projected legal lineups from ESPN roster entries.

Accepts normalized player entries and league lineup slots. Missing projections
are not zero: they invalidate the affected roster/week. Bench/IR slots are not
starter slots; position eligibility must come from ESPN's eligibleSlots.
"""
from functools import lru_cache

NON_STARTER_SLOTS = {20, 21, 22, 23, 24, 25}


def optimize_lineup(players, starting_slots):
    """Return highest projected legal lineup or raise on missing/incomplete data.

    players: [{player_id, projection, eligible_slots, available=True}]
    starting_slots: list of ESPN numeric lineup slot IDs (including duplicate slots).
    """
    if not starting_slots:
        raise ValueError("Starting slots must be provided")
    if any(not isinstance(slot, int) or slot in NON_STARTER_SLOTS for slot in starting_slots):
        raise ValueError("Only starting lineup slot IDs are allowed")
    clean = []
    seen = set()
    for player in players:
        pid = player["player_id"]
        if pid in seen:
            raise ValueError("Duplicate roster player")
        seen.add(pid)
        projection = player.get("projection")
        if projection is None:
            raise ValueError(f"Missing projection for roster player {pid}")
        if not isinstance(projection, (int, float)) or isinstance(projection, bool):
            raise ValueError("Projection must be numeric")
        if player.get("available", True):
            clean.append((pid, float(projection), frozenset(player.get("eligible_slots", []))))
    if len(clean) < len(starting_slots):
        raise ValueError("Insufficient available players for a legal lineup")
    # Most-constrained slots first reduces search space.
    ordered_slots = sorted(enumerate(starting_slots), key=lambda entry:
                           sum(entry[1] in p[2] for p in clean))
    options = [tuple(i for i, player in enumerate(clean) if slot in player[2])
               for _, slot in ordered_slots]
    if any(not candidates for candidates in options):
        raise ValueError("A required lineup position has no eligible player")

    @lru_cache(None)
    def solve(slot_index, used):
        if slot_index == len(ordered_slots):
            return (0.0, ())
        best = None
        for i in options[slot_index]:
            if used & (1 << i):
                continue
            rest = solve(slot_index + 1, used | (1 << i))
            if rest is None:
                continue
            candidate = (clean[i][1] + rest[0], (i,) + rest[1])
            if best is None or candidate[0] > best[0]:
                best = candidate
        return best

    answer = solve(0, 0)
    if answer is None:
        raise ValueError("No legal lineup exists for available players")
    assignments = [{"slot_id": slot, "player_id": clean[i][0],
                    "projected_points": round(clean[i][1], 3)}
                   for (_, slot), i in zip(ordered_slots, answer[1])]
    return {"projected_points": round(answer[0], 3),
            "lineup": assignments}
