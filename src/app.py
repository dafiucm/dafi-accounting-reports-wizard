from flask import Flask

from config.config import g_http_port, logger
from src.services.CumulativeExpenseReportExcelGenerator import CumulativeExpenseReportExcelGenerator
from src.services.CumulativeExpenseReportProcessor import CumulativeExpenseReportProcessor

g_welcome_ascii_art = '''
    ____  ___    __________
   / __ \/   |  / ____/  _/
  / / / / /| | / /_   / /  
 / /_/ / ___ |/ __/ _/ /   
/_____/_/  |_/_/   /___/   

Accounting Reports Wizard
Delegación de Estudiantes de la Facultad de Informática de la UCM
Created with <3 by Juan Carrión
'''


class App:

    instance = None

    def __init__(self):
        self.flask = None
        self.cumulative_expense_report_processor = None
        self.cumulative_expense_report_excel_generator = None

    @staticmethod
    def print_welcome() -> None:
        logger.info(g_welcome_ascii_art)

    @staticmethod
    def init() -> None:
        if App.instance is not None:
            raise RuntimeError('App has already been initialized.')

        App.instance = App()

        App.instance.flask = Flask(
            __name__,
            static_folder="../resources/static",
            template_folder="../resources/templates"
        )

        # noinspection PyUnresolvedReferences
        import src.routes

        App.instance.cumulative_expense_report_processor = CumulativeExpenseReportProcessor()
        App.instance.cumulative_expense_report_excel_generator = CumulativeExpenseReportExcelGenerator()

    @staticmethod
    def run() -> None:
        App.init()
        App.print_welcome()
        App.instance.flask.run(port=g_http_port)
