import importlib
import os

def test_repository_factory_uses_memory_in_test(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")

    import app.settings as settings_module
    import app.repository_factory as factory_module

    importlib.reload(settings_module)
    importlib.reload(factory_module)

    repository = factory_module.build_event_repository()
    assert repository.__class__.__name__ == "InMemoryEventRepository"
