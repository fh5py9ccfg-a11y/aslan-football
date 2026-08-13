import sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.event_sourcing_v6 import *
from aslan_ozaslan.admin.event_sourcing_page import render_event_sourcing_page

class EventSourcingTests(unittest.TestCase):
    def event(self, seq, typ, team=None, minute=0, payload=None):
        data={"minute":minute}
        if team is not None: data["team_id"]=team
        if payload: data.update(payload)
        return DomainEvent(
            f"e{seq}","f1",seq,typ,
            f"2026-08-01T10:{seq:02d}:00+00:00",data
        )

    def test_store_replay_snapshot_verification_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            store=SQLiteEventStore(Path(temp)/"events.db")
            snaps=JsonSnapshotRepository(Path(temp)/"snapshots.json")
            events=[
                self.event(0,"GOAL","home",12),
                self.event(1,"RED_CARD","away",25),
                self.event(2,"GOAL","away",40),
                self.event(3,"SCORE_CORRECTION",minute=45,payload={"home_goals":2,"away_goals":1}),
            ]
            for e in events: self.assertTrue(store.append(e))
            self.assertFalse(store.append(events[0]))
            engine=MatchReplayEngine(store,snaps,snapshot_interval=2)
            first=engine.replay("f1","home","away")
            self.assertEqual((first.state.home_goals,first.state.away_goals),(2,1))
            self.assertEqual(first.state.away_red_cards,1)
            historical=engine.replay("f1","home","away",up_to_sequence=1)
            self.assertEqual((historical.state.home_goals,historical.state.away_goals),(1,0))
            second=engine.replay("f1","home","away")
            self.assertTrue(second.used_snapshot)
            expected=MatchAggregateState("f1",3,45,"home","away",2,1,0,1,4)
            verification=ReplayVerifier().verify(second.state,expected)
            self.assertTrue(verification.valid)
            recovery=CrashRecoveryService(engine).recover("f1","home","away")
            self.assertTrue(recovery.recovered)
            page=render_event_sourcing_page(second,verification)
            self.assertIn("Event Sourcing & Replay",page)

if __name__=="__main__":
    unittest.main()
