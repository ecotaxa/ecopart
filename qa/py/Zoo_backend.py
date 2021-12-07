#
# Interface avec le back-end de dev
#
import os
import subprocess
import time
from os.path import dirname, realpath
from pathlib import Path

from dev_paths import BACKEND_RUN, BACKEND_VENV

HERE = Path(dirname(realpath(__file__)))
BACKEND_LOG = (HERE / "backend.log").absolute()
BACKEND_PORT = "8001"

FAKE_SPAGH = HERE.parent.resolve()


def generate_backend_conf(part_conf):
    """
        Il faut un config.cfg, comme attendu par le back-end, dans un fichier nommé précisément appli/config.cfg
    """
    config_path = FAKE_SPAGH / "appli" / "config.cfg"
    with open(config_path, "w") as cfg:
        for a_key, a_val in part_conf.items():
            cfg.write("%s=%s\n" % (a_key, a_val))
        cfg.write("""
SECURITY_PASSWORD_HASH="sha512_crypt"
SECURITY_PASSWORD_SALT="dontcare"
""")


def launch_backend():
    args = ["python", BACKEND_RUN, 'uvicorn']
    env = {"PATH": str(BACKEND_VENV / "bin"),
           "APP_PORT": BACKEND_PORT,
           "LEGACY_APP": FAKE_SPAGH}
    out_file = open(BACKEND_LOG, "w")
    working_dir = str(BACKEND_RUN.parent.resolve())
    backend_proc = subprocess.Popen(args=args, env=env, shell=False, cwd=working_dir,
                                    universal_newlines=True, stdout=out_file, stderr=subprocess.STDOUT)
    # OK en théorie il faudrait attendre que le port soit UP
    time.sleep(3)


def kill_backend():
    for a_line in open(BACKEND_LOG).readlines():
        if "Started" in a_line and "process" in a_line:
            child_pid = int(a_line.split("[")[1].split("]")[0])
            os.kill(child_pid, 5)
    # OK en théorie il faudrait attendre que les process disparaissent
    time.sleep(3)


if __name__ == '__main__':
    launch_backend()
    import time

    time.sleep(5)
    kill_backend()
