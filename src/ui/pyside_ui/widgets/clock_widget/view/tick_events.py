from __future__ import annotations

from typing import Protocol


class TickObserver(Protocol):
    def on_tick(self) -> None: ...


class TickEventSubject:
    def __init__(self) -> None:
        self._observers: list[TickObserver] = []

    def subscribe(self, observer: TickObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: TickObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self) -> None:
        observers_snapshot = tuple(self._observers)

        for observer in observers_snapshot:
            observer.on_tick()
