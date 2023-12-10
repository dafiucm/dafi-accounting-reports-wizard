import locale
import os
import re

import xlsxwriter
from PyPDF2 import PdfReader
from colorama import Fore

from config.config import g_tmp_path, g_ignored_strings, g_request_regex, g_number_of_pages_regex, g_date_regex, \
    g_months, g_total_report_amount_regex, g_budget_position_header_regex, g_budget_positions, logger, \
    g_budget_position_total_amount_regex, g_transaction_first_line_regex, g_transaction_second_line_regex
from src.models.Transaction import Transaction


def get_request_data(text: str) -> dict:
    match = re.search(g_request_regex, text)
    return {
        "id": match.group("request_id"),
        "name": match.group("request_name")
    }


def get_number_of_pages(text: str) -> int:
    match = re.search(g_number_of_pages_regex, text)
    return int(match.group("number_of_pages"))


def get_date(text: str) -> dict:
    match = re.search(g_date_regex, text)
    return {
        "day": int(match.group("day")),
        "month": g_months[match.group("month")],
        "year": int(match.group("year"))
    }


def parse_amount(amount: str) -> float:
    return float(amount.replace(".", "").replace(",", "."))


def get_total_report_amount(text: str) -> float:
    match = re.search(g_total_report_amount_regex, text)
    return parse_amount(match.group("total_report_amount"))


def format_amount(amount: float) -> str:
    return locale.format_string("%.2f", amount, True, True)


def log_metadata(file_name: str, real_path: str, request_data: dict, number_of_pages: int, date: dict, total_report_amount: float) -> None:
    logger.info(f"Processing {file_name}...")
    logger.info(f"Input: {real_path}")
    logger.info(f"Request ID: {request_data['id']}")
    logger.info(f"Request name: {request_data['name']}")
    logger.info(f"Number of pages: {number_of_pages}")
    logger.info(f"Date: {date['day']}/{date['month']}/{date['year']}")
    logger.info(f"Total request amount: {format_amount(total_report_amount)} €")


def clean_text(text: str) -> str:
    # Ignore strings in list
    for ignored_string in g_ignored_strings:
        text = re.sub(ignored_string, '', text)

    return text


def get_budget_position_header_from_line(text: str) -> dict:
    match = re.search(g_budget_position_header_regex, text)
    return {
        "code": match.group("code"),
        "name": match.group("name")
    }


def validate_budget_position_header(budget_position_header: dict) -> None:
    if budget_position_header["code"] not in g_budget_positions:
        logger.warning(f"! Budget position {budget_position_header['code']} not found in budget positions list")
    else:
        logger.info(Fore.LIGHTGREEN_EX + f"✓ Budget position {budget_position_header['code']} found")

        if budget_position_header["name"] != g_budget_positions[budget_position_header["code"]].name:
            logger.warning(f"! Budget position {budget_position_header['code']} name mismatch: {budget_position_header['name']} != {g_budget_positions[budget_position_header['code']].name}")


def validate_total_report_amount(budget_position_totals: dict, total_report_amount: float) -> None:
    total_amount = 0

    for budget_position_total in budget_position_totals.values():
        total_amount += budget_position_total

    if abs(total_amount - total_report_amount) > 0.01:
        logger.error(f"Total report amount mismatch: {format_amount(total_amount)} != {format_amount(total_report_amount)}")
    else:
        logger.info(Fore.LIGHTGREEN_EX + f"✓ Total report amount equals per-budget-position sum" + Fore.RESET)


def validate_per_budget_position_sum(budget_position_totals: dict, transactions: list) -> None:
    for budget_position_code, total in budget_position_totals.items():
        total_amount = 0

        for transaction in transactions:
            if transaction.budget_position_code == budget_position_code and not transaction.excluded_from_total:
                total_amount += transaction.amount

        if abs(total_amount - total) > 0.01:
            logger.error(f"Total amount for budget position {budget_position_code} mismatch: {format_amount(total_amount)} != {format_amount(total)}")
        else:
            logger.info(Fore.LIGHTGREEN_EX + f"✓ Total amount for budget position {budget_position_code} equals per-transaction sum" + Fore.RESET)


def process_cleaned_text(text: str, total_report_amount: float) -> list:
    found_budget_positions = []

    current_budget_position_code = None

    budget_position_totals = {}

    current_transaction = None

    transactions = []

    for line in text.splitlines():
        # Empty line
        if line.strip() == "":
            continue

        # Budget position header line
        if re.search(g_budget_position_header_regex, line):
            budget_position_header = get_budget_position_header_from_line(line)
            validate_budget_position_header(budget_position_header)

            if budget_position_header["code"] in found_budget_positions:
                raise Exception(f"Budget position {budget_position_header['code']} duplicated")

            found_budget_positions.append(budget_position_header["code"])

            current_budget_position_code = budget_position_header["code"]

            continue

        # Budget position total amount line
        if re.search(g_budget_position_total_amount_regex, line):
            total_amount = parse_amount(re.search(g_budget_position_total_amount_regex, line).group("total_amount"))
            budget_position_totals[current_budget_position_code] = total_amount
            continue

        # First transaction line
        match = re.search(g_transaction_first_line_regex, line)
        if match:
            if current_transaction is not None:
                transactions.append(current_transaction)

            current_transaction = Transaction.from_report_first_line(
                document_type_code=match.group("document_type"),
                document_number=match.group("document_number"),
                document_position=match.group("document_position"),
                document_date=match.group("document_date"),
                budget_position_code=match.group("budget_position_code"),
                description=match.group("description"),
                amount=parse_amount(match.group("amount")),
                excluded_from_total=False if match.group("asterisk") is None else True
            )
            continue

        # Second transaction line
        match = re.search(g_transaction_second_line_regex, line)
        if match:
            current_transaction.complete_with_report_second_line(
                reference=match.group("reference"),
                vendor_id=match.group("vendor_id"),
                vendor_name=match.group("vendor_name")
            )

            continue

    transactions.append(current_transaction)

    validate_total_report_amount(budget_position_totals, total_report_amount)

    validate_per_budget_position_sum(budget_position_totals, transactions)

    return transactions


def write_transactions_to_xlsx(file_name: str, transactions: list) -> None:
    new_file_name = file_name.replace(".pdf", ".xlsx")
    new_path = os.path.realpath(g_tmp_path + new_file_name)

    workbook = xlsxwriter.Workbook(new_path)
    worksheet = workbook.add_worksheet()

    worksheet.write(0, 0, "Posición presupuestaria")
    worksheet.write(0, 1, "Importe anotado")
    worksheet.write(0, 2, "Capítulo")
    worksheet.write(0, 3, "Tipo transacción")
    worksheet.write(0, 4, "Tipo doc.")
    worksheet.write(0, 5, "Nº documento")
    worksheet.write(0, 6, "Posición")
    worksheet.write(0, 7, "Referencia")
    worksheet.write(0, 8, "NIF acreedor")
    worksheet.write(0, 9, "Posición presupuestaria o cl. coste y denom. cl. coste")

    row = 2

    for budget_position in g_budget_positions.values():
        worksheet.write(row, 0, budget_position.compound_name())
        row += 1

        for transaction in [t for t in transactions if t.budget_position_code == budget_position.code]:
            worksheet.write(row, 1, transaction.amount)
            worksheet.write(row, 2, budget_position.budget_chapter)
            worksheet.write(row, 3, "Gasto")
            worksheet.write(row, 4, transaction.document_type_code)
            worksheet.write(row, 5, transaction.document_number)
            worksheet.write(row, 6, transaction.document_position)
            worksheet.write(row, 7, transaction.reference)
            worksheet.write(row, 8, transaction.vendor_id)
            worksheet.write(row, 9, transaction.vendor_name)

            row += 1

        row += 1

    workbook.close()


def process_file(file_name: str) -> None:
    real_path = os.path.realpath(g_tmp_path + file_name)
    reader = PdfReader(real_path)

    text = "\n".join([page.extract_text() for page in reader.pages])

    request_id_and_name = get_request_data(text)
    number_of_pages = get_number_of_pages(text)
    date = get_date(text)
    total_report_amount = get_total_report_amount(text)

    log_metadata(file_name, real_path, request_id_and_name, number_of_pages, date, total_report_amount)

    cleaned_text = clean_text(text)

    transactions = process_cleaned_text(cleaned_text, total_report_amount)

    write_transactions_to_xlsx(file_name, transactions)


if __name__ == "__main__":
    files = [file for file in os.listdir(g_tmp_path) if file.endswith(".pdf")]

    for file in files:
        process_file(file)
