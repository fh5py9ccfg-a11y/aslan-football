from apps.api.app.streaming_analytics import LiveMatchEvent, StreamingAnomalyDetector

def ev(eid, ts, xg):
    return LiveMatchEvent("m1",eid,"SHOT","home",None,10,ts,xg,None,"provider")

def test_bursty_high_xg_has_higher_anomaly():
    normal=(ev("e1",100,.1),ev("e2",110,.1),ev("e3",120,.1))
    anomaly=(ev("e1",100,.1),ev("e2",101,.9),ev("e3",130,.2))
    assert StreamingAnomalyDetector.calculate(anomaly) > StreamingAnomalyDetector.calculate(normal)
