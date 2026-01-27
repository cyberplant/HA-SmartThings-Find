DOMAIN = "smartthings_find"

CONF_JSESSIONID = "jsessionid"

CONF_ACTIVE_MODE_SMARTTAGS = "active_mode_smarttags"
CONF_ACTIVE_MODE_OTHERS = "active_mode_others"

CONF_ACTIVE_MODE_SMARTTAGS_DEFAULT = True
CONF_ACTIVE_MODE_OTHERS_DEFAULT = False

CONF_UPDATE_INTERVAL = "update_interval"
CONF_UPDATE_INTERVAL_DEFAULT = 120

BATTERY_LEVELS = {
    'FULL': 100,
    'MEDIUM': 50,
    'LOW': 15,
    'VERY_LOW': 5
}

# Version information for debugging
VERSION = "0.3.0-dev"
# This will be updated manually when we make significant changes
BUILD_DATE = "2026-01-27"
BUILD_INFO = f"v{VERSION}-{BUILD_DATE}"
