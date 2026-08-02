"""Componentes de UI reutilizables y tipos de mensajes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Message:
    """Mensaje para comunicación entre hilos y la UI."""

    type: str
    payload: Any = None


class TimerLabel:
    """Etiqueta de temporizador con formato MM:SS."""

    def __init__(self, label: Any) -> None:
        self._label = label
        self._running = False
        self._after_id: Optional[str] = None
        self._seconds = 0

    @property
    def seconds(self) -> int:
        return self._seconds

    def start(self, parent_widget: Any) -> None:
        self._parent = parent_widget
        self._running = True
        self._seconds = 0
        self._label.configure(text="00:00")
        self._schedule_tick()

    def stop(self) -> None:
        self._running = False
        if self._after_id is not None:
            self._label.after_cancel(self._after_id)
            self._after_id = None

    def pause(self) -> None:
        self._running = False
        if self._after_id is not None:
            self._label.after_cancel(self._after_id)
            self._after_id = None

    def resume(self) -> None:
        self._running = True
        self._schedule_tick()

    def reset(self) -> None:
        self.stop()
        self._seconds = 0
        self._label.configure(text="00:00")

    def _schedule_tick(self) -> None:
        self._after_id = self._label.after(1000, self._tick)

    def _tick(self) -> None:
        if self._running:
            self._seconds += 1
            minutes = self._seconds // 60
            secs = self._seconds % 60
            self._label.configure(text=f"{minutes:02d}:{secs:02d}")
        self._schedule_tick()
