import json
import subprocess
from desktop_parser import parse_desktop_files

OUTPUT_FILE = "app_index.json"


def scan_snap():
    apps = []
    try:
        result = subprocess.check_output(["snap", "list"], text=True)
        lines = result.splitlines()[1:]

        for line in lines:
            name = line.split()[0]
            apps.append({
                "name": name.capitalize(),
                "exec": name,
                "source": "snap",
                "type": "unknown",
                "keywords": []
            })
    except Exception:
        pass

    return apps


def scan_flatpak():
    apps = []
    try:
        result = subprocess.check_output(["flatpak", "list", "--app"], text=True)
        for line in result.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                name = parts[0]
                exec_cmd = f"flatpak run {parts[1]}"
                apps.append({
                    "name": name,
                    "exec": exec_cmd,
                    "source": "flatpak",
                    "type": "unknown",
                    "keywords": []
                })
    except Exception:
        pass

    return apps


def build_app_index():
    apps = []
    apps += parse_desktop_files()
    apps += scan_snap()
    apps += scan_flatpak()

    # убираем дубликаты
    unique = {}
    for app in apps:
        key = app["exec"]
        unique[key] = app

    return list(unique.values())


def save_index(apps):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(apps, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    apps = build_app_index()
    save_index(apps)
    print(f"Найдено приложений: {len(apps)}")
