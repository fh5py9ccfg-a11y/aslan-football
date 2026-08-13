from football_core import MatchEvent, MatchStateService

def test_match_state_rebuild():
    events = [
        MatchEvent("f1", 1, "GOAL", 12, "HOME"),
        MatchEvent("f1", 2, "RED_CARD", 40, "AWAY"),
        MatchEvent("f1", 3, "GOAL", 75, "AWAY"),
    ]
    state = MatchStateService().rebuild("f1", events)
    assert state.home_goals == 1
    assert state.away_goals == 1
    assert state.away_red_cards == 1
    assert state.minute == 75
