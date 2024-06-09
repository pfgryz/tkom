from multimethod import multimethod

from src.common.position import Position
from src.interface.ivisitor import IVisitor
from src.interpreter.box import Box
from src.interpreter.operations.operation_registry import OperationRegistry
from src.interpreter.operations.operations_registry import OperationsRegistry
from src.interpreter.stack.frame import Frame
from src.interpreter.errors import UndefinedFunctionError
from src.interpreter.functions.functions_registry import FunctionsRegistry
from src.interpreter.stack.value import Value
from src.interpreter.stack.variable import Variable
from src.interpreter.types.typename import TypeName
from src.interpreter.types.types_registry import TypesRegistry
from src.interpreter.visitors.functions_collector import FunctionsCollector
from src.interpreter.visitors.name_visitor import NameVisitor
from src.interpreter.visitors.semantic.fn_call_validator import FnCallValidator
from src.interpreter.visitors.semantic.new_struct_validator import \
    NewStructValidator
from src.interpreter.visitors.semantic.return_validator import ReturnValidator
from src.interpreter.visitors.types_collector import TypesCollector
from src.parser.ast.cast import Cast
from src.parser.ast.constant import Constant
from src.parser.ast.expressions.binary_operation import BinaryOperation
from src.parser.ast.expressions.binary_operation_type import \
    EBinaryOperationType
from src.parser.ast.expressions.bool_operation import BoolOperation
from src.parser.ast.expressions.bool_operation_type import EBoolOperationType
from src.parser.ast.expressions.compare import Compare
from src.parser.ast.expressions.compare_type import ECompareType
from src.parser.ast.expressions.unary_operation import UnaryOperation
from src.parser.ast.expressions.unary_operation_type import EUnaryOperationType
from src.parser.ast.is_compare import IsCompare
from src.parser.ast.module import Module
from src.parser.ast.name import Name
from src.parser.ast.node import Node
from src.parser.ast.statements.assignment import Assignment
from src.parser.ast.statements.block import Block
from src.parser.ast.statements.variable_declaration import VariableDeclaration
from src.parser.interface.itree_like_expression import ITreeLikeExpression


class Interpreter(IVisitor[Node]):

    # region Dunder Methods

    def __init__(self):
        # Stack
        self._frame = Frame[str, Variable]()
        self._value: Box[Value]() = Box[Value]()

        # Collectors
        self._types_collector = TypesCollector()
        self._functions_collector = FunctionsCollector(
            self._types_collector.types_registry
        )

        # Operations
        self._operations_registry = OperationsRegistry()

        # Validators
        self._fn_call_validator = FnCallValidator(
            self._functions_collector.functions_registry
        )
        self._new_struct_validator = NewStructValidator(
            self._types_collector.types_registry
        )
        self._return_validator = ReturnValidator()

        # Other
        self._name_visitor = NameVisitor()

        # Fill with basic operations @TODO: Move it somewhere

        def mul_int_int(x: Value, y: Value) -> Value:
            return Value(
                type_name=x.type_name,
                value=x.value * y.value
            )

        self._operations_registry.bool_operations.register_operation(
            EBoolOperationType.And,
            TypeName("*"),
            TypeName("&"),
            lambda x, y: Value(type_name=TypeName("bool"), value=bool(x.value) and bool(y.value))
        )
        self._operations_registry.compare.register_operation(
            ECompareType.Equal,
            TypeName("*"),
            TypeName("&"),
            lambda x, y: Value(type_name=TypeName("bool"), value=x.value == y.value)
        )

        self._operations_registry.binary_operations.register_operation(
            EBinaryOperationType.Multiply,
            TypeName("i32"),
            TypeName("i32"),
            lambda x, y: mul_int_int(x, y)
        )
        self._operations_registry.unary_operations.register_operation(
            EUnaryOperationType.Minus,
            TypeName("i32"),
            None,
            lambda x: Value(type_name=x.type_name, value=-x.value)
        )
        self._operations_registry.cast.register_operation(
            "as",
            TypeName("i32"),
            TypeName("i32"),
            lambda x: x
        )

        # @TODO: Make it unviersal
        # @TODO: This can be used to all, should include relation between enums also
        self._operations_registry.is_compare.register_operation(
            "is",
            TypeName("*"),
            TypeName("*"),
            lambda x, y: Value(type_name=TypeName("bool"),
                               value=x.type_name == y)
        )

    # endregion

    # region Properties

    @property
    def types_registry(self) -> TypesRegistry:
        return self._types_collector.types_registry

    @property
    def functions_registry(self) -> FunctionsRegistry:
        return self._functions_collector.functions_registry

    @property
    def operations_registry(self) -> OperationsRegistry:
        return self._operations_registry

    # endregion

    # region Frames Management

    def create_frame(self):
        self._frame = Frame(self._frame)

    def drop_frame(self):
        self._frame = self._frame.parent

    # endregion

    # region Module

    @multimethod
    def visit(self, module: Module) -> None:
        self._types_collector.visit(module)
        self._functions_collector.visit(module)
        self._fn_call_validator.visit(module)
        self._new_struct_validator.visit(module)
        self._return_validator.visit(module)

    def run(self, name: str):
        if not (main := self.functions_registry.get_function(name)):
            raise UndefinedFunctionError(name, Position(1, 1))
        print('RUN')
        # Create context
        main.call(self)

    # endregion

    # region Statements

    @multimethod
    def visit(self, block: Block):
        self.create_frame()
        print('Hi, i block')

        for statement in block.body:
            self.visit(statement)

        for v in self._frame.items():
            print(v)

        self.drop_frame()

    @multimethod
    def visit(self, variable_declaration: VariableDeclaration) -> None:
        # Get name
        self._name_visitor.visit(variable_declaration.name)
        name = self._name_visitor.name.take()

        # Get mutable state
        mutable = variable_declaration.mutable

        # Get type
        self._name_visitor.visit(variable_declaration.declared_type)
        declared_type = self._name_visitor.type.take()

        # Get value
        self.visit(variable_declaration.value)
        value = self._value.take()

        self._frame.set(
            name,
            Variable(
                mutable=mutable,
                value=value
            ),
            chain=False
        )

    @multimethod
    def visit(self, assignment: Assignment) -> None:
        # Get name
        self._name_visitor.visit(assignment.access)
        name = self._name_visitor.name.take()

        # Get variable
        variable = self._frame.get(name)

        # Get value
        self.visit(assignment.value)
        value = self._value.take()

        variable.value = value
        self._frame.set(
            name,
            variable
        )

    # endregion

    # region Expressions

    @multimethod
    def visit(self, expression: BoolOperation) -> None:
        self._operation(
            expression,
            self._operations_registry.bool_operations
        )

    @multimethod
    def visit(self, expression: Compare) -> None:
        self._operation(
            expression,
            self._operations_registry.compare
        )

    @multimethod
    def visit(self, expression: BinaryOperation) -> None:
        self._operation(
            expression,
            self._operations_registry.binary_operations
        )

    def _operation(
            self,
            expression: ITreeLikeExpression | Compare,
            registry: OperationRegistry
    ):
        self.visit(expression.left)
        left = self._value.take()
        self.visit(expression.right)
        right = self._value.take()

        operation = registry.get_operation(
            expression.op,
            left.type_name,
            right.type_name
        )
        self._value.put(
            operation(left, right)
        )

    @multimethod
    def visit(self, expression: UnaryOperation) -> None:
        self.visit(expression.operand)
        operand = self._value.take()

        operation = self._operations_registry.unary_operations.get_operation(
            expression.op,
            operand.type_name
        )

        self._value.put(
            operation(operand)
        )

    @multimethod
    def visit(self, expression: Cast) -> None:
        self.visit(expression.value)
        value = self._value.take()

        self._name_visitor.visit(expression.to_type)
        to_type = self._name_visitor.type.take()

        operation = self._operations_registry.cast.get_operation(
            "as",
            value.type_name,
            to_type
        )

        self._value.put(
            operation(value)
        )

    @multimethod
    def visit(self, expression: IsCompare) -> None:
        self.visit(expression.value)
        value = self._value.take()

        self._name_visitor.visit(expression.is_type)
        is_type = self._name_visitor.type.take()

        operation = self._operations_registry.is_compare.get_operation(
            "is",
            value.type_name,
            is_type
        )

        self._value.put(
            operation(value, is_type)
        )

    @multimethod
    def visit(self, constant: Constant) -> None:
        type_name = TypeName.parse(constant.type.to_name())
        self._value.put(
            Value(
                type_name=type_name,
                value=constant.value
            )
        )

    # endregion

    # region Names

    @multimethod
    def visit(self, name: Name) -> None:
        self._value.put(
            self._frame.get(name.identifier).value
        )

    # endregion
