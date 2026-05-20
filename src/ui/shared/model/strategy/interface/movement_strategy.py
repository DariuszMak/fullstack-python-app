from __future__ import annotations

from abc import ABC, abstractmethod


class MovementStrategy(ABC):
    @abstractmethod
    def update(self, current_value: float, target_value: float) -> float:
        raise NotImplementedError

    def reset(self) -> None:
        return None
