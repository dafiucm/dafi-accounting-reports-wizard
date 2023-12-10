import logging

from colorama import Fore, Style


class CustomFormatter(logging.Formatter):

    reset = Style.RESET_ALL
    pre = Fore.WHITE + "%(name)s - %(levelname)s - " + Fore.RESET
    message = "%(message)s"

    FORMATS = {
        logging.DEBUG: pre + Fore.LIGHTBLUE_EX + message + reset,
        logging.INFO: pre + Fore.LIGHTWHITE_EX + message + reset,
        logging.WARNING: pre + Fore.LIGHTYELLOW_EX + message + reset,
        logging.ERROR: pre + Fore.LIGHTRED_EX + message + reset,
        logging.CRITICAL: pre + Fore.LIGHTRED_EX + message + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
