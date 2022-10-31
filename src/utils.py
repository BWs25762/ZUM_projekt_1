import os


def get_root_dir():
    return os.path.dirname(__file__)


def get_data_dir():
    return os.path.join(get_root_dir(), "data")


if __name__ == "__main__":
    print(get_root_dir())
    print(get_data_dir())

