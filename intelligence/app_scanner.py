import os
import json
import subprocess
from datetime import datetime

DESKTOP_DIRS = [
    "/usr/share/applications",
    os.path.expanduser("~/.local/share/applications")
]

OUTPUT_FILE = "intelligence/app_index.json"


def scan_desktop_apps():
    apps = []

    for directory in DESKTOP_DIRS:
        if not os.path.exists(directory):
            continue

        for file in os.listdir(directory):
            if not file.endswith(".desktop"):
                continue

            path = os.path.join(directory, file)
            app = parse_desktop_file(path)

            if app:
                apps.append(app)

    return apps


def parse_desktop_file(path):
    name = None
    exec_cmd = None
    categories = []

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("Name="):
                    name = line.strip().split("=", 1)[1]
                elif line.startswith("Exec="):
                    exec_cmd = line.strip().split("=", 1)[1].split()[0]
                elif line.startswith("Categories="):
                    categories = line.strip().split("=", 1)[1].split(";")
    except:
        return None

    if not name or not exec_cmd:
        return None

    return {
        "name": name,
        "exec": exec_cmd,
        "type": "gui",
        "source": "desktop",
        "categories": categories,
        "aliases": []
    }


def scan_cli_commands():
    apps = []
    try:
        result = subprocess.run(
            ["bash", "-c", "compgen -c"],
            capture_output=True,
            text=True
        )
        commands = set(result.stdout.splitlines())

        for cmd in commands:
            apps.append({
                "name": cmd,
                "exec": cmd,
                "type": "cli",
                "source": "path",
                "categories": ["cli"],
                "aliases": []
            })
    except:
        pass

    return apps


def main():
    print("🔍 Scanning Linux applications...")

    desktop_apps = scan_desktop_apps()
    cli_apps = scan_cli_commands()

    all_apps = desktop_apps + cli_apps

    data = {
        "generated_at": datetime.now().isoformat(),
        "os": "linux",
        "apps": all_apps
    }

    os.makedirs("intelligence", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Found {len(all_apps)} applications")
    print(f"📄 Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
