import os
import uuid

import xlsxwriter

from config.config import g_tmp_path, logger
from src.models.CumulativeExpenseReport import CumulativeExpenseReport


class CumulativeExpenseReportExcelGenerator:

    def generate(self, report: CumulativeExpenseReport) -> uuid.UUID:
        logger.info("Generating Excel file")

        output_file_id = uuid.uuid4()
        new_path = os.path.join(g_tmp_path, output_file_id.__str__() + ".xlsx")

        workbook = xlsxwriter.Workbook(new_path)
        worksheet = workbook.add_worksheet()

        worksheet.write(0, 0, "Posición presupuestaria")
        worksheet.write(0, 1, "Importe previsto")
        worksheet.write(0, 2, "Importe anotado")
        worksheet.write(0, 3, "Capítulo")
        worksheet.write(0, 4, "Tipo transacción")
        worksheet.write(0, 5, "Tipo doc.")
        worksheet.write(0, 6, "Nº documento")
        worksheet.write(0, 7, "Posición")
        worksheet.write(0, 8, "Referencia")
        worksheet.write(0, 9, "NIF acreedor")
        worksheet.write(0, 10, "Posición presupuestaria o cl. coste y denom. cl. coste")

        row = 2

        for budget_position in report.budget_positions:
            worksheet.write(row, 0, budget_position.compound_name())
            row += 1

            for transaction in [t for t in report.transactions if t.budget_position_code == budget_position.code]:
                if transaction.excluded_from_total:
                    worksheet.write(row, 1, transaction.amount)
                else:
                    worksheet.write(row, 2, transaction.amount)

                worksheet.write(row, 3, budget_position.budget_chapter)
                worksheet.write(row, 4, "Gasto")
                worksheet.write(row, 5, transaction.document_type_code)
                worksheet.write(row, 6, transaction.document_number)
                worksheet.write(row, 7, transaction.document_position)
                worksheet.write(row, 8, transaction.reference)
                worksheet.write(row, 9, transaction.vendor_id)
                worksheet.write(row, 10, transaction.vendor_name)

                row += 1

            row += 1

        workbook.close()

        logger.info("Excel file generated")

        return output_file_id
