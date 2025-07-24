import abc
import threading

class AssetTemplate(threading.Thread):

    def __init__(self, *args, **kwargs):
        super().__init__()
        pass

    def run(self): pass

    def main_loop(self): pass

    def stop(self): pass