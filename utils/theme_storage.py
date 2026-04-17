from abc import ABC, abstractmethod
from typing import Optional
import json
import os


class ThemeStorage(ABC):
    """Abstract base class for theme storage backends."""

    @abstractmethod
    def save_theme(self, name: str, data: dict) -> bool:
        """Save a theme by name. Returns True on success."""
        pass

    @abstractmethod
    def load_theme(self, name: str) -> Optional[dict]:
        """Load a theme by name. Returns None if not found."""
        pass

    @abstractmethod
    def list_themes(self) -> list[str]:
        """Return list of all saved theme names."""
        pass

    @abstractmethod
    def delete_theme(self, name: str) -> bool:
        """Delete a theme by name. Returns True on success."""
        pass


class LocalFileStorage(ThemeStorage):
    """
    Local JSON file backend — wraps existing save_custom_theme() logic.
    Used in development and as fallback when no DB is configured.
    """

    def __init__(self, themes_dir: str = "themes/json"):
        self.themes_dir = themes_dir
        os.makedirs(themes_dir, exist_ok=True)

    def _path(self, name: str) -> str:
        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_"))
        return os.path.join(self.themes_dir, f"{safe_name}.json")

    def save_theme(self, name: str, data: dict) -> bool:
        try:
            with open(self._path(name), "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False

    def load_theme(self, name: str) -> Optional[dict]:
        path = self._path(name)
        if not os.path.exists(path):
            return None
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return None

    def list_themes(self) -> list[str]:
        if not os.path.exists(self.themes_dir):
            return []
        return [
            f.replace(".json", "")
            for f in os.listdir(self.themes_dir)
            if f.endswith(".json")
        ]

    def delete_theme(self, name: str) -> bool:
        path = self._path(name)
        if not os.path.exists(path):
            return False
        try:
            os.remove(path)
            return True
        except Exception:
            return False