from enum import Enum
import logging


class Level(Enum):
    """
    Enum class to define custom logging levels.
    - The `ATTACK` level is set to 14, which is between `DEBUG` (10) and `INFO` (20).
    - The `CREATION` level is set to 16, which is between `DEBUG` (10) and `INFO` (20).
    This allows for more granular control over logging messages.
    """

    DEBUG = logging.DEBUG
    ATTACK = 14
    CREATION = 16
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


logging.addLevelName(Level.CREATION.value, "CREATION")
logging.addLevelName(Level.ATTACK.value, "ATTACK")


class Logger(logging.Logger):
    """
    Custom logger class that provides a singleton instance with a console handler.
    This logger can be used throughout the application to log messages at different levels.
    The level is set to `INFO` by default, but can be changed as needed.
    """

    instance = None

    def __init__(self, name: str):
        super().__init__(name)

        level = Level.INFO.value
        self.setLevel(level)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # Create formatter and add it to the handler
        formatter = logging.Formatter("%(levelname)s - %(message)s\n")
        console_handler.setFormatter(formatter)

        # Add the handler to the logger
        self.addHandler(console_handler)

    @staticmethod
    def get_instance():
        """
        Returns the singleton instance of the Logger.
        If it does not exist, it creates a new one.
        """
        if Logger.instance is None:
            Logger.instance = Logger("attack-smt")
        return Logger.instance

    def creation(self, message: str):
        """
        Logs a message at the `CREATION` level.
        """
        self.log(Level.CREATION.value, message)

    def attack(self, message: str):
        """
        Logs a message at the `ATTACK` level.
        """
        self.log(Level.ATTACK.value, message)

    def set_level(self, level: int):
        """
        Sets the logging level for the logger.
        """
        super().setLevel(level)
        for handler in self.handlers:
            handler.setLevel(level)

    def set_log_file(self, log_file: str):
        """
        Sets the log file for the logger.
        If a file handler already exists, it removes it before adding a new one.
        """
        for handler in self.handlers:
            if isinstance(handler, logging.FileHandler):
                self.removeHandler(handler)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(self.level)
        formatter = logging.Formatter("%(levelname)s - %(message)s\n")
        file_handler.setFormatter(formatter)
        self.addHandler(file_handler)
