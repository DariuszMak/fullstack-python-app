from __future__ import annotations

from src.ui.pyside_ui.widgets.clock_widget.view.tick_events import TickEventSubject, TickObserver


class DummyObserver(TickObserver):
    def __init__(self) -> None:
        self.count = 0

    def on_tick(self) -> None:
        self.count += 1


class DummyObserverAlt(TickObserver):
    def __init__(self) -> None:
        self._value = 0

    def on_tick(self) -> None:
        self._value += 5


def test_single_observer_receives_ticks() -> None:
    subject = TickEventSubject()
    obs = DummyObserver()
    subject.subscribe(obs)

    subject.notify()
    subject.notify()

    assert obs.count == 2


def test_multiple_observers_receive_ticks() -> None:
    subject = TickEventSubject()
    obs1 = DummyObserver()
    obs2 = DummyObserverAlt()

    subject.subscribe(obs1)
    subject.subscribe(obs2)

    subject.notify()

    assert obs1.count == 1
    assert obs2._value == 5


def test_unsubscribed_observer_no_longer_receives_ticks() -> None:
    subject = TickEventSubject()
    obs = DummyObserver()

    subject.subscribe(obs)
    subject.notify()

    subject.unsubscribe(obs)
    subject.notify()

    assert obs.count == 1


def test_duplicate_subscription_is_ignored() -> None:
    subject = TickEventSubject()
    obs = DummyObserver()

    subject.subscribe(obs)
    subject.subscribe(obs)

    subject.notify()

    assert obs.count == 1


def test_unsubscribe_nonexistent_observer_does_nothing() -> None:
    subject = TickEventSubject()
    obs = DummyObserver()

    subject.unsubscribe(obs)
    subject.notify()

    assert obs.count == 0
