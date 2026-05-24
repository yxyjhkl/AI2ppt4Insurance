"""Progress tracking utility for PPT generation."""
from __future__ import annotations
import asyncio
from typing import Callable, Optional


class ProgressTracker:
    """Tracks and reports progress for long-running tasks."""
    
    def __init__(self, total_steps: int = 100):
        self.total_steps = total_steps
        self.current_step = 0
        self.current_stage = ""
        self.current_message = ""
        self._callbacks: list[Callable[[dict], None]] = []
        self._async_callbacks: list[Callable[[dict], asyncio.coroutines]] = []
    
    def add_callback(self, callback: Callable[[dict], None]):
        """Add a synchronous callback."""
        self._callbacks.append(callback)
    
    def add_async_callback(self, callback: Callable[[dict], asyncio.coroutines]):
        """Add an asynchronous callback."""
        self._async_callbacks.append(callback)
    
    def _notify(self):
        """Notify all callbacks with current progress."""
        progress = {
            "step": self.current_step,
            "total": self.total_steps,
            "percentage": int((self.current_step / self.total_steps) * 100),
            "stage": self.current_stage,
            "message": self.current_message,
        }
        
        for callback in self._callbacks:
            try:
                callback(progress)
            except Exception:
                pass
        
        for callback in self._async_callbacks:
            try:
                asyncio.create_task(callback(progress))
            except Exception:
                pass
    
    def set_stage(self, stage: str, message: str = "", step: Optional[int] = None):
        """Set current stage and optionally update step."""
        self.current_stage = stage
        self.current_message = message
        if step is not None:
            self.current_step = step
        self._notify()
    
    def advance(self, steps: int = 1, message: str = ""):
        """Advance progress by given steps."""
        self.current_step = min(self.current_step + steps, self.total_steps)
        if message:
            self.current_message = message
        self._notify()
    
    def complete(self, message: str = "完成"):
        """Mark progress as complete."""
        self.current_step = self.total_steps
        self.current_message = message
        self._notify()
    
    @property
    def is_complete(self) -> bool:
        """Check if progress is complete."""
        return self.current_step >= self.total_steps
