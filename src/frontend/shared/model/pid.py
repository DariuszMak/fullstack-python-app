from __future__ import annotations


class PID:
    def __init__(self, kp: float = 0.0, ki: float = 0.0, kd: float = 0.0) -> None:
        self._kp = float(kp)
        self._ki = float(ki)
        self._kd = float(kd)
        self._prev_error = 0.0
        self._integral = 0.0

    def update(self, error: float) -> float:
        self._integral += error
        derivative = error - self._prev_error
        self._prev_error = error
        return self._kp * error + self._ki * self._integral + self._kd * derivative

    def reset(self) -> None:
        self._prev_error = 0.0
        self._integral = 0.0
