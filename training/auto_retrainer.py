"""Background continuous-learning coordinator for the AJAX intent model.

Chat interactions are collected immediately, but retraining is deliberately
batched. This keeps inference responsive and prevents a training run for every
single user message.
"""

import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from config.config_loader import BASE_DIR, config
from core.logger import ajax_logger, error_logger

STATE_FILE = os.path.join(BASE_DIR, "data", "auto_training_state.json")


class AutoTrainingManager:
    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._training_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._state = self._load_state()

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _timestamp(value: Any) -> float:
        if not value:
            return 0.0
        try:
            return datetime.fromisoformat(str(value)).timestamp()
        except (TypeError, ValueError):
            return 0.0

    def _load_state(self) -> Dict[str, Any]:
        if not os.path.exists(STATE_FILE):
            return {
                "status": "idle",
                "last_trained_sample_count": 0,
                "last_attempt_at": None,
                "last_success_at": None,
                "last_error": None,
            }
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            error_logger.warning(f"Auto-training state load notice: {exc}")
            return {}

    def _save_state(self) -> None:
        try:
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            with self._state_lock:
                payload = dict(self._state)
            temp_path = f"{STATE_FILE}.tmp"
            with open(temp_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
            os.replace(temp_path, STATE_FILE)
        except Exception as exc:
            error_logger.warning(f"Auto-training state save notice: {exc}")

    def _update_state(self, **changes: Any) -> None:
        with self._state_lock:
            self._state.update(changes)
        self._save_state()

    @staticmethod
    def _approved_sample_count() -> int:
        from database.crud import get_training_examples
        return len(get_training_examples(approved_only=True))

    def start(self) -> None:
        if not config.auto_training_enabled or os.environ.get("VERCEL"):
            ajax_logger.info("Automatic intent retraining is disabled for this runtime.")
            return
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="ajax-auto-training",
            daemon=True,
        )
        self._thread.start()
        ajax_logger.info(
            "Automatic intent retraining enabled: "
            f"{config.auto_training_min_new_samples} new samples, "
            f"every {config.auto_training_check_interval_seconds}s."
        )

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        self._thread = None

    def _run_loop(self) -> None:
        if self._stop_event.wait(config.auto_training_initial_delay_seconds):
            return
        while not self._stop_event.is_set():
            try:
                self.maybe_retrain()
            except Exception as exc:
                error_logger.exception(f"Automatic retraining loop error: {exc}")
            if self._stop_event.wait(config.auto_training_check_interval_seconds):
                break

    def _run_training(self, reason: str, sample_count: Optional[int] = None) -> Dict[str, Any]:
        if not self._training_lock.acquire(blocking=False):
            return {"success": False, "status": "already_running"}

        try:
            count_before = sample_count if sample_count is not None else self._approved_sample_count()
            self._update_state(
                status="training",
                last_attempt_at=self._now_iso(),
                last_error=None,
                last_reason=reason,
            )
            ajax_logger.info(
                f"Starting automatic intent retraining ({reason}, "
                f"{count_before} approved samples)."
            )

            from training.train import train_from_sources
            train_from_sources()

            count_after = self._approved_sample_count()
            self._update_state(
                status="idle",
                last_trained_sample_count=count_after,
                last_success_at=self._now_iso(),
                last_error=None,
            )
            ajax_logger.info(
                f"Automatic intent retraining completed successfully ({count_after} samples)."
            )
            return {"success": True, "status": "completed", "sample_count": count_after}
        except Exception as exc:
            error_logger.exception(f"Automatic intent retraining failed: {exc}")
            self._update_state(status="error", last_error=str(exc))
            return {"success": False, "status": "error", "error": str(exc)}
        finally:
            self._training_lock.release()

    def maybe_retrain(self) -> Dict[str, Any]:
        if not config.auto_training_enabled:
            return {"success": False, "status": "disabled"}
        try:
            current_count = self._approved_sample_count()
        except Exception as exc:
            error_logger.warning(f"Could not count training samples: {exc}")
            return {"success": False, "status": "count_error"}

        with self._state_lock:
            last_count = int(self._state.get("last_trained_sample_count", 0) or 0)
            last_attempt_at = self._state.get("last_attempt_at")
        pending = max(0, current_count - last_count)
        if pending < config.auto_training_min_new_samples:
            return {"success": False, "status": "waiting", "pending_samples": pending}

        if time.time() - self._timestamp(last_attempt_at) < config.auto_training_cooldown_seconds:
            return {"success": False, "status": "cooldown", "pending_samples": pending}

        return self._run_training("automatic threshold", sample_count=current_count)

    def retrain_now(self) -> Dict[str, Any]:
        """Run a manual/admin-triggered training job through the same lock."""
        return self._run_training("manual request")

    def get_status(self) -> Dict[str, Any]:
        try:
            current_count = self._approved_sample_count()
        except Exception:
            current_count = None
        with self._state_lock:
            state = dict(self._state)
        last_count = int(state.get("last_trained_sample_count", 0) or 0)
        state.update({
            "enabled": bool(config.auto_training_enabled and not os.environ.get("VERCEL")),
            "running": bool(self._thread and self._thread.is_alive()),
            "training_in_progress": self._training_lock.locked(),
            "current_approved_samples": current_count,
            "pending_samples": max(0, current_count - last_count) if current_count is not None else None,
            "min_new_samples": config.auto_training_min_new_samples,
            "check_interval_seconds": config.auto_training_check_interval_seconds,
            "cooldown_seconds": config.auto_training_cooldown_seconds,
        })
        return state


auto_training_manager = AutoTrainingManager()
