import datetime

from src.models.CumulativeExpenseReportTransaction import CumulativeExpenseReportTransaction
from src.valueobjects.BudgetPosition import BudgetPosition


class CumulativeExpenseReport:

    def __init__(self, file_name: str):
        self._file_name = file_name
        self._object_id = None
        self._object_name = None
        self._number_of_pages = None
        self._date = None
        self._total_amount = None
        self._budget_positions = []
        self._transactions = []

    # Getters

    @property
    def file_name(self) -> str:
        return self._file_name

    @property
    def object_id(self) -> str:
        return self._object_id

    @property
    def object_name(self) -> str:
        return self._object_name

    @property
    def number_of_pages(self) -> int:
        return self._number_of_pages

    @property
    def date(self) -> datetime.date:
        return self._date

    @property
    def total_amount(self) -> float:
        return self._total_amount

    @property
    def budget_positions(self) -> list:
        return self._budget_positions

    @property
    def transactions(self) -> list:
        return self._transactions

    # Setters

    @object_id.setter
    def object_id(self, object_id: str):
        self._object_id = object_id

    @object_name.setter
    def object_name(self, object_name: str):
        self._object_name = object_name

    @number_of_pages.setter
    def number_of_pages(self, number_of_pages: int):
        self._number_of_pages = number_of_pages

    @date.setter
    def date(self, date: datetime.date):
        self._date = date

    @total_amount.setter
    def total_amount(self, total_amount: float):
        self._total_amount = total_amount

    def add_budget_position(self, budget_position: BudgetPosition):
        self._budget_positions.append(budget_position)

    def add_transaction(self, transaction: CumulativeExpenseReportTransaction):
        self._transactions.append(transaction)
