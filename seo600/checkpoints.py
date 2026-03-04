"""Crash-recovery checkpoint system for SEO600 content generation."""

import json
import os
from datetime import datetime, timezone

CHECKPOINT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "seo600", "checkpoints.json",
)


class CheckpointManager:
    def __init__(self, path: str = CHECKPOINT_PATH):
        self.path = path
        self.generated: list[str] = []
        self.failed: dict[str, str] = {}
        self.last_run: str | None = None
        self.load()

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                data = json.load(f)
            self.generated = data.get("generated", [])
            self.failed = data.get("failed", {})
            self.last_run = data.get("last_run")

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(
                {
                    "generated": self.generated,
                    "failed": self.failed,
                    "last_run": self.last_run,
                },
                f,
                indent=2,
            )

    def is_done(self, key: str) -> bool:
        return key in self.generated

    def mark_done(self, key: str):
        if key not in self.generated:
            self.generated.append(key)
        self.failed.pop(key, None)
        self.last_run = datetime.now(timezone.utc).isoformat()
        self.save()

    def mark_failed(self, key: str, error: str):
        self.failed[key] = error
        self.last_run = datetime.now(timezone.utc).isoformat()
        self.save()

    def status(self) -> dict:
        return {
            "generated": len(self.generated),
            "failed": len(self.failed),
            "last_run": self.last_run,
            "failed_keys": list(self.failed.keys()),
        }
