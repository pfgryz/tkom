from src.common.location import Location
from src.parser.ast.expressions.term import Term
from src.parser.ast.name import Name
from src.parser.ast.statements.assignment import Assignment
from src.parser.ast.statements.statement import Statement
from src.parser.ast.variant_access import VariantAccess


class NewStruct(Statement, Term):

    # region Dunder Methods

    def __init__(self, variant: Name | VariantAccess, assignments: list[Assignment],
                 location: Location):
        super().__init__(location)

        self._variant = variant
        self._assignments = assignments

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NewStruct) \
            and self.variant == other.variant \
            and self.assignments == other.assignments \
            and super().__eq__(other)

    # endregion

    # region Properties

    @property
    def variant(self) -> Name | VariantAccess:
        return self._variant

    @property
    def assignments(self) -> list[Assignment]:
        return self._assignments

    # endregion
