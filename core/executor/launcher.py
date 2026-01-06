import subprocess


def launch_app(exec_cmd):
    subprocess.Popen(exec_cmd.split())
