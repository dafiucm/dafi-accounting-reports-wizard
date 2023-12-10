import io
import logging

from colorama import Fore

from config.config import logger


class CapturingLogger:

    @staticmethod
    def capture_html_logs(func):
        buffer = io.StringIO()
        handler = logging.StreamHandler(buffer)
        handler.setLevel(logging.DEBUG)

        formatter = CapturingLogger.AsciiToHtmlFormatter()
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        result = func()

        log_contents = buffer.getvalue()
        buffer.close()

        return result, log_contents

    class AsciiToHtmlFormatter(logging.Formatter):
        CLASSES = {
            logging.DEBUG: "debug",
            logging.INFO: "info",
            logging.WARNING: "warning",
            logging.ERROR: "error",
            logging.CRITICAL: "critical",
        }

        REPLACEMENTS = {
            Fore.LIGHTGREEN_EX: "<span class=\"lightgreen-ex\">",
            Fore.RESET: "</span>",
            "\n": "<br>",
            "\t": "&emsp;"
        }

        def format(self, record):
            output = record.msg

            for key, value in self.REPLACEMENTS.items():
                output = output.replace(key, value)

            return f"<p class=\"{self.CLASSES.get(record.levelno)}\">{output}</p>"
