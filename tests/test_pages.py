import pytest
from streamlit.testing.v1 import AppTest

from dss5105 import llm, memory, records


@pytest.fixture(autouse=True)
def offline(tmp_path, monkeypatch):
    monkeypatch.setattr(records, "DEFAULT_STORE_PATH", tmp_path / "plan.sqlite3")
    monkeypatch.setattr(memory, "DEFAULT_MEMORY_PATH", tmp_path / "memory.sqlite3")
    monkeypatch.setattr(llm, "get_model", lambda **kwargs: pytest.fail("pages never call a model on load"))


def lab():
    from dss5105 import lab_page

    lab_page.render()


def memory_view():
    from dss5105 import memory_page

    memory_page.render()


def test_lab_replays_the_simulator_and_reports_the_course_checks():
    app = AppTest.from_function(lab, default_timeout=60).run()
    assert not app.exception and not app.error
    verdicts = [caption.value for caption in app.caption if caption.value.startswith(("\u2713", "\u26a0"))]
    assert len(verdicts) == 4
    assert verdicts[0].startswith("\u2713 **Lateness**")
    app.selectbox(key="lab_preset").set_value("fairness").run()
    assert not app.exception
    assert any(v.startswith("\u2713 **Fairness**") for v in (c.value for c in app.caption))
    app.selectbox(key="lab_preset").set_value("custom").run()
    app.slider(key="lab_lateness_custom").set_value(0.0)
    app.slider(key="lab_defects_custom").set_value(0.0).run()
    assert not app.exception and "not all zero" in app.error[0].value


def test_memory_page_shows_layers_and_archives_only_after_confirmation():
    app = AppTest.from_function(memory_view, default_timeout=30).run()
    assert not app.exception and not app.error
    assert [tab.label for tab in app.tabs] == ["Rules (0)", "Bookings (0)", "Log (0)", "Profile", "Plan"]
    assert app.button(key="archive_plan").disabled
    app.checkbox(key="confirm_archive").check().run()
    app.button(key="archive_plan").click().run()
    assert not app.exception and app.success
