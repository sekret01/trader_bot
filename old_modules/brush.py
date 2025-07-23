import os


ESC = "\033["
DEFAULT = ESC + "0;0;0m"


def brush_start():
    """ Call cmd for coloring """
    os.system('')


class Brush:
    def __init__(self):
        os.system('')

    @staticmethod
    def clear() -> None: os.system('cls')

    @staticmethod
    def black(text: str) -> str: return ESC + "30m" + text + DEFAULT

    @staticmethod
    def red(text: str) -> str: return ESC + "31m" + text + DEFAULT

    @staticmethod
    def green(text: str) -> str: return ESC + "32m" + text + DEFAULT

    @staticmethod
    def yellow(text: str) -> str: return ESC + "33m" + text + DEFAULT

    @staticmethod
    def blue(text: str) -> str: return ESC + "34m" + text + DEFAULT

    @staticmethod
    def purple(text: str) -> str: return ESC + "35m" + text + DEFAULT

    @staticmethod
    def light_blue(text: str) -> str: return ESC + "36m" + text + DEFAULT

    @staticmethod
    def gray(text: str) -> str: return ESC + "37m" + text + DEFAULT


if __name__ == "__main__":
    os.system('')
