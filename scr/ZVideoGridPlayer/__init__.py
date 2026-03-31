# zvideogridplayer/__init__.py
"""ZVideoGridPlayer - Multi-video grid player."""

__version__ = "1.2.0"
__author__ = "Alexey Melnikov"
__description__ = "Modern multi-video grid player with OpenCV"

from .main import VideoGridPlayer, main

__all__ = ["VideoGridPlayer", "main"]