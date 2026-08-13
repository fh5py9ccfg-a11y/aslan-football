from apps.api.app.drain_mode import DrainController

def test_drain_mode_tracks_active_requests():
    controller = DrainController()
    controller.begin_request()
    controller.begin_request()
    state = controller.enter(reason='rolling upgrade', now=100)
    assert state.enabled is True
    assert state.active_requests == 2
    controller.finish_request()
    controller.finish_request()
    controller.finish_request()
    assert controller.snapshot().active_requests == 0
    assert controller.exit().enabled is False
