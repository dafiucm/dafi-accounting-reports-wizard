import datetime
import os
import re

from PyPDF2 import PdfReader
from colorama import Fore

from config.config import g_tmp_path, g_ignored_strings, g_number_of_pages_regex, g_date_regex, \
    g_months, g_total_report_amount_regex, g_budget_position_header_regex, g_budget_positions, logger, \
    g_budget_position_total_amount_regex, g_transaction_first_line_regex, g_transaction_second_line_regex, \
    g_report_object_regex
from src.models.CumulativeExpenseReport import CumulativeExpenseReport
from src.models.CumulativeExpenseReportTransaction import CumulativeExpenseReportTransaction
from src.utils.date import format_date
from src.utils.math import parse_es_float, format_es_float
from src.valueobjects.BudgetPosition import BudgetPosition


class CumulativeExpenseReportProcessor:

    def process_report(self,
                       file_name: str,
                       real_path: str
                       ) -> CumulativeExpenseReport:
        context = CumulativeExpenseReportProcessor.ExecutionContext(
            file_name=file_name,
            real_path=real_path
        )

        return context.process_report()

    class ExecutionContext:

        def __init__(self, file_name: str, real_path: str):
            self.file_name = file_name
            self.real_path = real_path
            self.raw_text_source = None
            self.clean_text_source = None
            self.report = None
            self.current_budget_position_code = None
            self.budget_position_totals = {}
            self.current_transaction = None

        def extract_text(self) -> None:
            reader = PdfReader(self.real_path)
            self.raw_text_source = "\n".join([page.extract_text() for page in reader.pages])

        def extract_request_data(self) -> None:
            match = re.search(g_report_object_regex, self.raw_text_source)
            self.report.object_id = match.group("object_id")
            self.report.object_name = match.group("object_name")

        def extract_number_of_pages(self) -> None:
            match = re.search(g_number_of_pages_regex, self.raw_text_source)
            self.report.number_of_pages = int(match.group("number_of_pages"))

        def extract_date(self) -> None:
            match = re.search(g_date_regex, self.raw_text_source)
            self.report.date = datetime.date(
                year=int(match.group("year")),
                month=g_months[match.group("month")],
                day=int(match.group("day"))
            )

        def extract_total_amount(self) -> None:
            match = re.search(g_total_report_amount_regex, self.raw_text_source)
            self.report.total_amount = parse_es_float(match.group("total_amount"))

        def log_metadata(self) -> None:
            logger.info(f"Procesando informe \"{self.file_name}\"")
            logger.info(f"Entrada: {self.real_path}")
            logger.info(f"Id. del objeto: {self.report.object_id}")
            logger.info(f"Nombre del objeto: {self.report.object_name}")
            logger.info(f"Número de páginas: {self.report.number_of_pages}")
            logger.info(f"Fecha del informe: {format_date(self.report.date)}")
            logger.info(f"Importe total del informe: {format_es_float(self.report.total_amount)} €")

        def extract_clean_text(self) -> None:
            text = self.raw_text_source

            for ignored_string in g_ignored_strings:
                text = re.sub(ignored_string, '', text)

            self.clean_text_source = text

        def process_budget_position_header_line(self, line: str) -> bool:
            match = re.search(g_budget_position_header_regex, line)

            if match is None:
                return False

            code = match.group("code")

            if next((bp for bp in self.report.budget_positions if bp.code == code), None) is not None:
                logger.error(f"La posición {code} está duplicada")
                raise Exception(f"La posición {code} está duplicada")

            if match.group("code") in g_budget_positions:
                budget_position = g_budget_positions[code]
                logger.info(Fore.LIGHTGREEN_EX + f"✓ Posición presupuestaria {code} encontrada")
                if match.group("name") != budget_position.name:
                    logger.warning(f"! La posición {code} tiene un nombre diferente al registrado: {match.group('name')} != {budget_position.name}")
            else:
                logger.warning(f"! No se encontró la posición {code}")
                budget_position = BudgetPosition(
                    code=code,
                    name=match.group("name"),
                    budget_chapter="UNKNOWN"
                )

            self.report.add_budget_position(budget_position)
            self.current_budget_position_code = budget_position.code

            return True

        def process_budget_position_total_amount_line(self, line: str) -> bool:
            match = re.search(g_budget_position_total_amount_regex, line)

            if match is None:
                return False

            total_amount = parse_es_float(match.group("total_amount"))
            self.budget_position_totals[self.current_budget_position_code] = total_amount

            return True

        def process_transaction_first_line(self, line: str) -> bool:
            match = re.search(g_transaction_first_line_regex, line)

            if match is None:
                return False

            if self.current_transaction is not None:
                self.report.add_transaction(self.current_transaction)

            self.current_transaction = CumulativeExpenseReportTransaction.from_report_first_line(
                document_type_code=match.group("document_type"),
                document_number=match.group("document_number"),
                document_position=match.group("document_position"),
                document_date=match.group("document_date"),
                budget_position_code=match.group("budget_position_code"),
                description=match.group("description"),
                amount=parse_es_float(match.group("amount")),
                excluded_from_total=False if match.group("asterisk") is None else True
            )

            return True

        def process_transaction_second_line(self, line: str) -> bool:
            match = re.search(g_transaction_second_line_regex, line)

            if match is None:
                return False

            self.current_transaction.complete_with_report_second_line(
                reference=match.group("reference"),
                vendor_id=match.group("vendor_id"),
                vendor_name=match.group("vendor_name")
            )

            return True

        def validate_total_report_amount_with_budget_position_totals(self) -> None:
            total_amount = 0

            for budget_position_total in self.budget_position_totals.values():
                total_amount += budget_position_total

            if abs(total_amount - self.report.total_amount) > 0.01:
                logger.error(f"El importe total del informe no coincide con la suma de todas las posiciones: {format_es_float(total_amount)} != {format_es_float(self.report.total_amount)}")
                raise Exception(f"El importe total del informe no coincide con la suma de todas las posiciones: {format_es_float(total_amount)} != {format_es_float(self.report.total_amount)}")
            else:
                logger.info(Fore.LIGHTGREEN_EX + f"✓ El importe total del informe coincide con la suma de todas las posiciones" + Fore.RESET)

        def validate_budget_position_totals_with_per_position_transactions(self) -> None:
            for budget_position_code, total in self.budget_position_totals.items():
                total_amount = 0

                for transaction in self.report.transactions:
                    if transaction.budget_position_code == budget_position_code and not transaction.excluded_from_total:
                        total_amount += transaction.amount

                if abs(total_amount - total) > 0.01:
                    logger.error(f"El total de la posición {budget_position_code} no coincide con la suma de sus movimientos: {format_es_float(total_amount)} != {format_es_float(total)}")
                    raise Exception(f"El total de la posición {budget_position_code} no coincide con la suma de sus movimientos: {format_es_float(total_amount)} != {format_es_float(total)}")
                else:
                    logger.info(
                        Fore.LIGHTGREEN_EX + f"✓ El total de la posición {budget_position_code} coincide con la suma de sus movimientos" + Fore.RESET)

        def process_clean_text(self) -> None:
            for line in self.clean_text_source.splitlines():
                if line.strip() == "":
                    continue

                if self.process_budget_position_header_line(line):
                    continue

                if self.process_budget_position_total_amount_line(line):
                    continue

                if self.process_transaction_first_line(line):
                    continue

                if self.process_transaction_second_line(line):
                    continue

            self.report.add_transaction(self.current_transaction)

        def process_report(self) -> CumulativeExpenseReport:
            self.extract_text()

            self.report = CumulativeExpenseReport(self.file_name)

            self.extract_request_data()
            self.extract_number_of_pages()
            self.extract_date()
            self.extract_total_amount()

            self.log_metadata()

            self.extract_clean_text()
            self.process_clean_text()

            self.validate_total_report_amount_with_budget_position_totals()
            self.validate_budget_position_totals_with_per_position_transactions()

            return self.report
