import os
import subprocess


def get_root_dir():
    return os.path.dirname(__file__)


def get_data_dir():
    return os.path.join(get_root_dir(), "data")


def enable_ec_write_access():
    subprocess.run(["sudo", "modprobe", "-r", "ec_sys"])
    # subprocess.run([sudo modprobe -r ec_sys])
    # subprocess.run([sudo modprobe ec_sys write_support=1])
    subprocess.run(["sudo", "modprobe", "ec_sys", "write_support=1"])


if __name__ == "__main__":
    print(get_root_dir())
    print(get_data_dir())

