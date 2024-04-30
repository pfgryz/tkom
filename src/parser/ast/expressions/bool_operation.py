from src.common.location import Location
from src.parser.ast.expressions.bool_operation_type import EBoolOperationType
from src.parser.ast.node import Node


class BoolOperation(Node):
    # region Dunder Methods

    def __init__(self, left: 'Expression', right: 'Expression',
                 op: EBoolOperationType, location: Location):
        super().__init__(location)
        self._left = left
        self._right = right
        self._op = op

    def __repr__(self) -> str:
        return "BoolOperation(left={}, right={}, op={}, location={})".format(
            repr(self.left),
            repr(self.right),
            repr(self.op),
            repr(self.location)
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BoolOperation) \
            and self.left == other.left \
            and self.right == other.right \
            and self.op == other.op

    # endregion

    # region Properties

    @property
    def left(self) -> 'Expression':
        return self._left

    @property
    def right(self) -> 'Expression':
        return self._right

    @property
    def op(self) -> EBoolOperationType:
        return self._op

    # endregion