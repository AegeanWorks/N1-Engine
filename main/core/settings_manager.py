import json
import os
import logging
import tempfile

# Default values, can be imported from config.py to keep them central
from main.config import (
    MIN_BASELINE_DAYS,
    MIN_INTERVENTION_DAYS,
    MIN_DATA_POINTS,
    MAX_SAFE_METRICS
)

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1


class SettingsManager:
    def __init__(self, settings_file="settings.json"):
        self.settings_file = settings_file
        self.defaults = {
            "min_baseline_days": MIN_BASELINE_DAYS,
            "min_intervention_days": MIN_INTERVENTION_DAYS,
            "min_data_points": MIN_DATA_POINTS,
            "max_safe_metrics": MAX_SAFE_METRICS,
        }
        self.settings = self.defaults.copy()
        self.load_settings()

    def _validated(self, raw) -> dict:
        """Keep known keys whose values are positive integers; else default."""
        settings = self.defaults.copy()
        if not isinstance(raw, dict):
            return settings
        for key, default in self.defaults.items():
            value = raw.get(key, default)
            if isinstance(value, bool) or not isinstance(value, int):
                logger.warning(f"Ignoring non-integer setting '{key}': {value!r}")
                continue
            if value < 1:
                logger.warning(f"Ignoring out-of-range setting '{key}': {value!r}")
                continue
            settings[key] = value
        return settings

    def load_settings(self):
        if not os.path.exists(self.settings_file):
            self.settings = self.defaults.copy()
            return self.settings

        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                user_settings = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Could not load settings file '{self.settings_file}': {e}. Using defaults.")
            self.settings = self.defaults.copy()
            return self.settings

        if not isinstance(user_settings, dict):
            logger.error(f"Settings file '{self.settings_file}' is not an object. Using defaults.")
            self.settings = self.defaults.copy()
            return self.settings

        version = user_settings.get("version")
        if version is not None and version != SCHEMA_VERSION:
            logger.error(
                f"Settings file '{self.settings_file}' uses version {version!r}; "
                f"this build supports {SCHEMA_VERSION}. Using defaults without rewriting it."
            )
            self.settings = self.defaults.copy()
            return self.settings

        # A file without a version predates schema 1 and migrates on the next save.
        self.settings = self._validated(user_settings)
        return self.settings

    def save_settings(self) -> bool:
        payload = {"version": SCHEMA_VERSION, **self.settings}
        directory = os.path.dirname(os.path.abspath(self.settings_file))
        temporary = None
        try:
            handle, temporary = tempfile.mkstemp(
                prefix=".settings-", suffix=".tmp", dir=directory
            )
            with os.fdopen(handle, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=4)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary, self.settings_file)
            temporary = None
            logger.info(f"Settings saved to '{self.settings_file}'.")
            return True
        except (OSError, TypeError, ValueError) as e:
            logger.error(f"Could not save settings to '{self.settings_file}': {e}.")
            return False
        finally:
            if temporary and os.path.exists(temporary):
                try:
                    os.remove(temporary)
                except OSError:
                    logger.warning(f"Could not remove temporary settings file {temporary}.")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        if key in self.defaults:
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                logger.warning(f"Refused invalid value for setting '{key}': {value!r}")
                return
            self.settings[key] = value
        else:
            logger.warning(f"Attempted to set an unknown setting: '{key}'")

# Global instance
settings_manager = SettingsManager()
