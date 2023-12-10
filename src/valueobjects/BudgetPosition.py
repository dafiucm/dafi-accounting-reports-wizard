class BudgetPosition:

    def __init__(self, code: str, name: str, budget_chapter: int):
        self.code = code
        self.name = name
        self.budget_chapter = budget_chapter

    def compound_name(self) -> str:
        return f"{self.code} {self.name}"
