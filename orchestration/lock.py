"""Process lock mechanism to prevent overlapping daily executions on Windows."""

import os
import sys
import logging
from pathlib import Path
from typing import Optional
from config.settings import settings

logger = logging.getLogger(__name__)


class SingleInstanceLock:
    """Acquires an exclusive file lock to prevent concurrent executions."""

    def __init__(self, lock_file: Optional[Path] = None):
        self.lock_file = lock_file or (settings.data_dir / "pipeline.lock")
        self.acquired = False

    def acquire(self) -> bool:
        """Attempt to acquire exclusive single-instance lock."""
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)

        if self.lock_file.exists():
            # Check if previous process is still alive
            try:
                with open(self.lock_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                pid = int(content) if content.isdigit() else None

                if pid and self._is_process_running(pid):
                    logger.warning(
                        f"Another instance of the SEO Automation Pipeline is already running (PID {pid}). "
                        f"Aborting execution to prevent conflicts."
                    )
                    return False
                else:
                    logger.info(f"Removing stale lock from inactive PID {pid}.")
                    self.lock_file.unlink(missing_ok=True)
            except Exception as e:
                logger.debug(f"Error inspecting lock file: {e}")
                self.lock_file.unlink(missing_ok=True)

        try:
            with open(self.lock_file, "w", encoding="utf-8") as f:
                f.write(str(os.getpid()))
            self.acquired = True
            return True
        except Exception as e:
            logger.error(f"Failed to create lock file: {e}")
            return False

    def release(self) -> None:
        """Release the file lock upon pipeline completion."""
        if self.acquired:
            try:
                if self.lock_file.exists():
                    self.lock_file.unlink()
                self.acquired = False
            except Exception as e:
                logger.debug(f"Error releasing lock file: {e}")

    def _is_process_running(self, pid: int) -> bool:
        """Check if process with given PID is currently active on Windows."""
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            SYNCHRONIZE = 0x00100000
            process = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
            if process != 0:
                kernel32.CloseHandle(process)
                return True
            return False
        except Exception:
            return False

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError("Could not acquire exclusive single-instance lock. Another run is active.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
