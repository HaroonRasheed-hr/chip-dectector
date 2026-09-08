"""Named-logger accessors for the four log files required by spec A.6.2.

Each accessor returns the Python logger configured in ``LOGGING`` (see
``config/settings/base.py``) so the rest of the codebase never touches
file handlers directly.
"""
import logging


def get_runtime_logger() -> logging.Logger:
    """General application runtime events → ``logs/runtime.log``."""
    return logging.getLogger('visionpulse.runtime')


def get_errors_logger() -> logging.Logger:
    """All captured errors across every domain → ``logs/errors.log``."""
    return logging.getLogger('visionpulse.errors')


def get_inference_logger() -> logging.Logger:
    """Inference-specific failures and diagnostics → ``logs/inference.log``."""
    return logging.getLogger('visionpulse.inference')


def get_warnings_logger() -> logging.Logger:
    """System-level warnings and non-critical issues → ``logs/warnings.log``."""
    return logging.getLogger('visionpulse.warnings')


def get_mqtt_logger() -> logging.Logger:
    """MQTT broker / publisher / subscriber events → ``logs/mqtt.log``."""
    return logging.getLogger('visionpulse.mqtt')


def get_mqtt_result_logger() -> logging.Logger:
    """Structured MQTT publish/subscribe records → ``logs/mqtt-result.log``."""
    return logging.getLogger('visionpulse.mqtt.result')
