from .domain import MatchAggregateState

class MatchStateProjector:
    def initial(self, fixture_id, home_team_id, away_team_id):
        return MatchAggregateState(
            fixture_id,-1,0,home_team_id,away_team_id,0,0,0,0,0
        )

    def apply(self, state, event):
        if event.fixture_id != state.fixture_id:
            raise ValueError("Event farklı fixture'a ait")
        if event.sequence <= state.last_sequence:
            raise ValueError("Event sequence geriye gidemez")
        minute = max(state.minute, int(event.payload.get("minute", state.minute)))
        hg, ag = state.home_goals, state.away_goals
        hr, ar = state.home_red_cards, state.away_red_cards
        team = event.payload.get("team_id")
        if event.event_type == "GOAL":
            if team == state.home_team_id: hg += 1
            elif team == state.away_team_id: ag += 1
        elif event.event_type == "RED_CARD":
            if team == state.home_team_id: hr += 1
            elif team == state.away_team_id: ar += 1
        elif event.event_type == "SCORE_CORRECTION":
            hg = int(event.payload["home_goals"])
            ag = int(event.payload["away_goals"])
        return MatchAggregateState(
            state.fixture_id,event.sequence,minute,state.home_team_id,
            state.away_team_id,hg,ag,hr,ar,state.processed_events+1
        )
