from src.table.operation.base import ILOp


class NOT(ILOp):
    def __init__(self, operand: ILOp):
        self.operand = operand

    def execute(self) -> bool:
        return not self.operand.execute()

    def to_string(self) -> str:
        return f"(NOT {self.operand.to_string()})"
