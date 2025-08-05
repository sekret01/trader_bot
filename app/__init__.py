"""
Управление через консоль пока доступно только для Windows.
На unix-системах программа может быть запущена только в режиме start_app
"""

import platform
PLATFORM = platform.system()

from .logger import Logger
from .asset_templates import CandleTemplate
from .asset_templates import Strategy, TrendFollowing
from .control_hub import ControlHub
from .csv_saver import CSV_Saver

if PLATFORM == "Windows":
    from .console import Console
