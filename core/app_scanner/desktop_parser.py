import os
import configparser

DESKTOP_DIRS = [
    "/usr/share/applications",
    os.path.expanduser("~/.local/share/applications")
]

def parse_desktop_files():
    apps = []

    for directory in DESKTOP_DIRS:
        if not os.path.exists(directory):
            continue

        for file in os.listdir(directory):
            if not file.endswith(".desktop"):
                continue

            path = os.path.join(directory, file)
            config = configparser.ConfigParser(interpolation=None)

            try:
                config.read(path, encoding="utf-8")
                entry = config["Desktop Entry"]

                if entry.get("NoDisplay") == "true":
                    continue

                name = entry.get("Name")
                exec_cmd = entry.get("Exec")

                if not name or not exec_cmd:
                    continue

                exec_cmd = exec_cmd.split()[0]  # убираем %U %F и т.д.

                apps.append({
                    "name": name,
                    "exec": exec_cmd,
                    "source": "desktop",
                    "type": "unknown",
                    "keywords": []
                })

            except Exception:
                continue

    return apps
