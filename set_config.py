import configparser

_parser = configparser.ConfigParser()
_parser.read(".configs.ini")


TOKEN: str = _parser["TOKENS"]["token"]
SANDBOX_TOKEN: str = _parser["TOKENS"]["sandbox"]
