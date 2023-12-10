from datetime import datetime


class CumulativeExpenseReportTransaction:

    def __init__(self,
                 document_type_code: str = None,
                 document_number: str = None,
                 document_position: str = None,
                 document_date: datetime.date = None,
                 reference: str = None,
                 budget_position_code: str = None,
                 vendor_id: str = None,
                 vendor_name: str = None,
                 description: str = None,
                 amount: float = None,
                 excluded_from_total: bool = False,
                 ):
        self.document_type_code = document_type_code
        self.document_number = document_number
        self.document_position = document_position
        self.document_date = document_date
        self.reference = reference
        self.budget_position_code = budget_position_code
        self.vendor_id = vendor_id
        self.vendor_name = vendor_name
        self.description = description
        self.amount = amount
        self.excluded_from_total = excluded_from_total

    @staticmethod
    def from_report_first_line(
            document_type_code: str = None,
            document_number: str = None,
            document_position: str = None,
            document_date: datetime.date = None,
            budget_position_code: str = None,
            description: str = None,
            amount: float = None,
            excluded_from_total: bool = False,
    ) -> 'CumulativeExpenseReportTransaction':
        return CumulativeExpenseReportTransaction(
            document_type_code=document_type_code,
            document_number=document_number,
            document_position=document_position,
            document_date=document_date,
            budget_position_code=budget_position_code,
            description=description,
            amount=amount,
            excluded_from_total=excluded_from_total,
        )

    def complete_with_report_second_line(
            self,
            reference: str = None,
            vendor_id: str = None,
            vendor_name: str = None,
    ):
        self.reference = reference
        self.vendor_id = vendor_id
        self.vendor_name = vendor_name

    def __str__(self):
        return "A"
