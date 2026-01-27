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

def get_commit_hash():
    """Get the current git commit hash."""
    try:
        import subprocess
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'], 
                                      cwd=__file__.rsplit('/', 3)[0]).decode().strip()
    except:
        return "unknown"

COMMIT_HASH = get_commit_hash()
