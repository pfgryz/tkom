import pytest

from src.lexer.lexer import Lexer
from src.lexer.token_kind import TokenKind
from src.parser.ast.access import Access
from src.parser.ast.cast import Cast
from src.parser.ast.enum_declaration import EnumDeclaration
from src.parser.ast.expressions.binary_operation_type import \
    EBinaryOperationType
from src.parser.ast.expressions.bool_operation_type import EBoolOperationType
from src.parser.ast.expressions.compare_type import ECompareMode
from src.parser.ast.expressions.unary_operation_type import EUnaryOperationType
from src.parser.ast.is_compare import IsCompare
from src.parser.ast.name import Name
from src.parser.ast.variant_access import VariantAccess
from src.parser.errors import SyntaxExpectedTokenException, SyntaxException
from src.parser.parser import Parser
from src.utils.buffer import StreamBuffer


# region Utilities

def create_parser(content: str, consume_first: bool = False) -> Parser:
    buffer = StreamBuffer.from_str(content)
    lexer = Lexer(buffer)
    parser = Parser(lexer)

    # Read first token
    if consume_first:
        parser.consume()

    return parser


# endregion

# region Helper Methods

def test_consume():
    parser = create_parser("1 test", True)

    first = parser.consume()
    second = parser.consume()

    assert first.kind == TokenKind.Integer
    assert second.kind == TokenKind.Identifier


def test_consume_if_matching():
    parser = create_parser("1 test", True)

    token = parser.consume_if(TokenKind.Integer)

    assert token is not None
    assert token.kind == TokenKind.Integer


def test_consume_if_not_matching():
    parser = create_parser("1 test", True)

    token = parser.consume_if(TokenKind.Identifier)

    assert token is None


def test_consume_match_matching():
    parser = create_parser("1 test", True)

    first = parser.consume_match([TokenKind.Identifier, TokenKind.Integer])
    second = parser.consume_match([TokenKind.Identifier, TokenKind.Integer])

    assert first is not None
    assert second is not None
    assert first.kind == TokenKind.Integer
    assert second.kind == TokenKind.Identifier


def test_consume_match_not_matching():
    parser = create_parser("y = 3", True)

    token = parser.consume_match([TokenKind.Fn, TokenKind.Mut])

    assert token is None


def test_expect_exists():
    parser = create_parser("x = 3", True)

    token = parser.expect(TokenKind.Identifier)

    assert token.kind == TokenKind.Identifier


def test_expect_missing():
    parser = create_parser("mut x", True)

    with pytest.raises(SyntaxExpectedTokenException):
        parser.expect(TokenKind.Fn)


def test_expect_conditional_exists():
    parser = create_parser("x + y", True)

    token = parser.expect_conditional(TokenKind.Identifier, False)

    assert token.kind == TokenKind.Identifier


def test_expect_conditional_exists_required():
    parser = create_parser("y = 5", True)

    token = parser.expect_conditional(TokenKind.Identifier, True)

    assert token.kind == TokenKind.Identifier


def test_expect_conditional_missing():
    parser = create_parser("123 * c", True)

    token = parser.expect_conditional(TokenKind.Identifier, False)

    assert token is None


def test_expect_conditional_missing_required():
    parser = create_parser("fn main()", True)

    with pytest.raises(SyntaxExpectedTokenException):
        parser.expect_conditional(TokenKind.Identifier, True)


def test_expect_match_exists():
    parser = create_parser("mut x = 3", True)

    token = parser.expect_match([TokenKind.Mut, TokenKind.Identifier])

    assert token is not None
    assert token.kind == TokenKind.Mut


def test_expect_match_missing():
    parser = create_parser("fn main()", True)

    with pytest.raises(SyntaxExpectedTokenException):
        parser.expect_match([TokenKind.Mut, TokenKind.Identifier])


# endregion

# region Parse Methods

# endregion

# region Parse Functions


def test_parse_function_declaration_simple():
    parser = create_parser("fn m() {}", True)

    function = parser.parse_function_declaration()

    assert function is not None
    assert function.name.identifier == "m"
    assert len(function.parameters) == 0
    # @TODO: assert len(function.body) == 0


def test_parse_function_declaration_with_parameters():
    parser = create_parser("fn main(argc: i32, mut argv: str) {}", True)

    function = parser.parse_function_declaration()

    assert function is not None
    assert function.name.identifier == "main"
    assert len(function.parameters) == 2


def test_parse_function_declaration_with_return_type():
    parser = create_parser("fn get_name(item: Entity::Item) -> str {}", True)

    function = parser.parse_function_declaration()

    assert function is not None
    assert function.name.identifier == "get_name"
    assert len(function.parameters) == 1
    assert function.returns.identifier == "str"


def test_parse_parameters_empty():
    parser = create_parser("", True)

    parameters = parser.parse_parameters()

    assert parameters is not None
    assert len(parameters) == 0


def test_parse_parameters_single():
    parser = create_parser("x: i32", True)

    parameters = parser.parse_parameters()

    assert parameters is not None
    assert len(parameters) == 1


def test_parse_parameters_many():
    parser = create_parser("x: i32, mut y: Entity::Item", True)

    parameters = parser.parse_parameters()

    assert parameters is not None
    assert len(parameters) == 2


def test_parse_parameters_missing_parameter_after_comma():
    parser = create_parser("x: i32, ", True)

    with pytest.raises(SyntaxException):
        parser.parse_parameters()


def test_parse_parameter_simple():
    parser = create_parser("x: i32", True)

    parameter = parser.parse_parameter()

    assert parameter is not None
    assert parameter.name.identifier == "x"
    assert parameter.type.identifier == "i32"
    assert not parameter.mutable


def test_parse_parameter_mutable():
    parser = create_parser("mut y: Item", True)

    parameter = parser.parse_parameter()

    assert parameter is not None
    assert parameter.name.identifier == "y"
    assert parameter.type.identifier == "Item"
    assert parameter.mutable


def test_parse_parameter_missing_colon():
    parser = create_parser("mut y f32", True)

    with pytest.raises(SyntaxExpectedTokenException):
        parser.parse_parameter()


def test_parse_parameter_missing_identifier_after_mut():
    parser = create_parser("mut : f32", True)

    with pytest.raises(SyntaxExpectedTokenException):
        parser.parse_parameter()


def test_parse_parameter_junk():
    parser = create_parser(": f32", True)

    parameter = parser.parse_parameter()

    assert parameter is None


# endregion

# region Parse Structs


def test_parse_struct_empty():
    parser = create_parser("struct Item {}", True)

    struct = parser.parse_struct_declaration()

    assert struct is not None
    assert struct.name.identifier == "Item"
    assert len(struct.fields) == 0


def test_parse_struct_with_fields():
    parser = create_parser("struct Item { value: i32; }", True)

    struct = parser.parse_struct_declaration()

    assert struct is not None
    assert struct.name.identifier == "Item"
    assert len(struct.fields) == 1
    assert struct.fields[0].name.identifier == "value"
    assert struct.fields[0].type.identifier == "i32"


def test_parse_field_declaration():
    parser = create_parser("value: i32;", True)

    field = parser.parse_field_declaration()

    assert field is not None
    assert field.name.identifier == "value"
    assert field.type.identifier == "i32"


def test_parse_field_declaration_missing_semicolon():
    parser = create_parser("value: i32", True)

    with pytest.raises(SyntaxExpectedTokenException):
        parser.parse_field_declaration()


# endregion

# region Parse Enum

def test_parse_enum_declaration_empty():
    parser = create_parser("enum Entity {}", True)

    enum = parser.parse_enum_declaration()

    assert enum is not None
    assert enum.name.identifier == "Entity"
    assert len(enum.variants) == 0


def test_parse_enum_declaration_with_structs():
    parser = create_parser("enum Elem { struct Button {}; struct Div {}; }",
                           True)

    enum = parser.parse_enum_declaration()

    assert enum is not None
    assert enum.name.identifier == "Elem"
    assert len(enum.variants) == 2
    assert enum.variants[0].name.identifier == "Button"
    assert enum.variants[1].name.identifier == "Div"


def test_parse_enum_declaration_with_enums():
    parser = create_parser("enum Elem { enum Button { }; }", True)

    enum = parser.parse_enum_declaration()

    assert enum is not None
    assert enum.name.identifier == "Elem"
    assert len(enum.variants) == 1
    assert isinstance(enum.variants[0], EnumDeclaration)
    assert enum.variants[0].name.identifier == "Button"


def test_parse_enum_declaration_with_deeply_nested():
    parser = create_parser(
        """
        enum Elem {
            enum Button {
                struct Disabled {};
                struct Active {};
            };
        }
        """,
        True)

    enum = parser.parse_enum_declaration()

    assert enum is not None
    assert enum.name.identifier == "Elem"
    assert len(enum.variants) == 1
    assert isinstance(enum.variants[0], EnumDeclaration)
    assert len(enum.variants[0].variants) == 2
    assert enum.variants[0].variants[0].name.identifier == "Disabled"


# endregion

# region Parse Statements

def test_parse_return_statement_void():
    parser = create_parser("return", True)

    return_statement = parser.parse_return_statement()

    assert return_statement is not None
    assert return_statement.value is None


def test_parse_return_statement_with_value():
    parser = create_parser("return 5", True)

    return_statement = parser.parse_return_statement()

    assert return_statement is not None
    assert return_statement.value is not None
    assert return_statement.value.value == 5


# endregion

# region Parse Access


def test_parse_access_single():
    parser = create_parser("person", True)

    access = parser.parse_access()

    assert access is not None
    assert isinstance(access, Name)
    assert access.identifier == "person"


def test_parse_access_standard():
    parser = create_parser("person.name", True)

    access = parser.parse_access()

    assert access is not None
    assert isinstance(access, Access)
    assert isinstance(access.name, Name)
    assert isinstance(access.parent, Name)
    assert access.name.identifier == "name"
    assert access.parent.identifier == "person"


def test_parse_access_nested():
    parser = create_parser("person.name.value", True)

    access = parser.parse_access()

    assert access is not None
    assert isinstance(access, Access)
    assert isinstance(access.name, Name)
    assert isinstance(access.parent, Access)
    assert access.name.identifier == "value"
    assert access.parent.name.identifier == "name"
    assert access.parent.parent.identifier == "person"


def test_parse_access_missing_identifier_after_period():
    parser = create_parser("person.", True)

    with pytest.raises(SyntaxExpectedTokenException):
        parser.parse_access()


def test_parse_variant_access_single():
    parser = create_parser("Entity", True)

    access = parser.parse_variant_access()

    assert access is not None
    assert isinstance(access, Name)
    assert access.identifier == "Entity"


def test_parse_variant_access_standard():
    parser = create_parser("Entity::Item", True)

    variant_access = parser.parse_variant_access()

    assert variant_access is not None
    assert isinstance(variant_access, VariantAccess)
    assert isinstance(variant_access.name, Name)
    assert isinstance(variant_access.parent, Name)
    assert variant_access.name.identifier == "Item"
    assert variant_access.parent.identifier == "Entity"


def test_parse_variant_access_nested():
    parser = create_parser("Entity::Item::Sword", True)

    variant_access = parser.parse_variant_access()

    assert variant_access is not None
    assert isinstance(variant_access, VariantAccess)
    assert isinstance(variant_access.name, Name)
    assert isinstance(variant_access.parent, VariantAccess)
    assert variant_access.name.identifier == "Sword"
    assert variant_access.parent.name.identifier == "Item"
    assert variant_access.parent.parent.identifier == "Entity"


def test_parse_variant_access_missing_identifier_after_double_colon():
    parser = create_parser("Entity::", True)

    with pytest.raises(SyntaxExpectedTokenException):
        parser.parse_variant_access()


def test_parse_type_builtin():
    parser = create_parser("i32", True)

    typ = parser.parse_type()

    assert typ is not None
    assert isinstance(typ, Name)
    assert typ.identifier == "i32"


def test_parse_type_struct():
    parser = create_parser("Sword", True)

    typ = parser.parse_type()

    assert typ is not None
    assert isinstance(typ, Name)
    assert typ.identifier == "Sword"


def test_parse_type_variant():
    parser = create_parser("Entity::Sword", True)

    typ = parser.parse_type()

    assert typ is not None
    assert isinstance(typ, VariantAccess)
    assert typ.name.identifier == "Sword"
    assert typ.parent.identifier == "Entity"


# endregion

# region Parse Expressions

def test_parse_or_expression_pure():
    parser = create_parser("34", True)

    term = parser.parse_expression()

    assert term is not None
    assert term.value == 34


def test_parse_or_expression_default():
    parser = create_parser("7 || 9", True)

    term = parser.parse_expression()

    assert term is not None
    assert term.op == EBoolOperationType.Or
    assert term.left.value == 7
    assert term.right.value == 9


def test_parse_or_expression_many():
    parser = create_parser("0 || 4 || 5", True)

    term = parser.parse_expression()

    assert term is not None
    assert term.op == EBoolOperationType.Or
    assert term.left.op == EBoolOperationType.Or


def test_parse_or_expression_hierarchy():
    parser = create_parser("0 || 4 && 5", True)

    term = parser.parse_expression()

    assert term is not None
    assert term.op == EBoolOperationType.Or
    assert term.right.op == EBoolOperationType.And


def test_parse_or_expression_missing_right():
    parser = create_parser("10 || ", True)

    with pytest.raises(SyntaxException):
        parser.parse_expression()


def test_parse_and_expression_pure():
    parser = create_parser("34", True)

    term = parser.parse_and_expression()

    assert term is not None
    assert term.value == 34


def test_parse_and_expression_default():
    parser = create_parser("7 && 9", True)

    term = parser.parse_and_expression()

    assert term is not None
    assert term.op == EBoolOperationType.And
    assert term.left.value == 7
    assert term.right.value == 9


def test_parse_and_expression_many():
    parser = create_parser("0 && 4 && 5", True)

    term = parser.parse_and_expression()

    assert term is not None
    assert term.op == EBoolOperationType.And
    assert term.left.op == EBoolOperationType.And


def test_parse_and_expression_missing_right():
    parser = create_parser("10 && ", True)

    with pytest.raises(SyntaxException):
        parser.parse_and_expression()


def test_parse_relation_expression_pure():
    parser = create_parser("34", True)

    term = parser.parse_relation_expression()

    assert term is not None
    assert term.value == 34


def test_parse_relation_expression_equal():
    parser = create_parser("3 == 4", True)

    term = parser.parse_relation_expression()

    assert term is not None
    assert term.mode == ECompareMode.Equal
    assert term.left.value == 3
    assert term.right.value == 4


def test_parse_relation_expression_not_equal():
    parser = create_parser("3 != 4", True)

    term = parser.parse_relation_expression()

    assert term is not None
    assert term.mode == ECompareMode.NotEqual


def test_parse_relation_expression_greater():
    parser = create_parser("3 > 4", True)

    term = parser.parse_relation_expression()

    assert term is not None
    assert term.mode == ECompareMode.Greater


def test_parse_relation_expression_less():
    parser = create_parser("3 < 4", True)

    term = parser.parse_relation_expression()

    assert term is not None
    assert term.mode == ECompareMode.Less


def test_parse_relation_expression_missing_right():
    parser = create_parser("10 == ", True)

    with pytest.raises(SyntaxException):
        parser.parse_relation_expression()


def test_parse_additive_term_pure():
    parser = create_parser("34", True)

    term = parser.parse_additive_term()

    assert term is not None
    assert term.value == 34


def test_parse_additive_term_add():
    parser = create_parser("7 + 9", True)

    term = parser.parse_additive_term()

    assert term is not None
    assert term.op == EBinaryOperationType.Add
    assert term.left.value == 7
    assert term.right.value == 9


def test_parse_additive_term_sub():
    parser = create_parser("0 - 4", True)

    term = parser.parse_additive_term()

    assert term is not None
    assert term.op == EBinaryOperationType.Sub
    assert term.left.value == 0
    assert term.right.value == 4


def test_parse_additive_term_nested_hierarchy():
    parser = create_parser("0 - 4 * 5", True)

    term = parser.parse_additive_term()

    assert term is not None
    assert term.op == EBinaryOperationType.Sub
    assert term.right.op == EBinaryOperationType.Multiply


def test_parse_additive_term_missing_right():
    parser = create_parser("10 - ", True)

    with pytest.raises(SyntaxException):
        parser.parse_additive_term()


def test_parse_multiplicative_term_pure():
    parser = create_parser("34", True)

    term = parser.parse_multiplicative_term()

    assert term is not None
    assert term.value == 34


def test_parse_multiplicative_term_multiply():
    parser = create_parser("3 * 4", True)

    term = parser.parse_multiplicative_term()

    assert term is not None
    assert term.left.value == 3
    assert term.right.value == 4
    assert term.op == EBinaryOperationType.Multiply


def test_parse_multiplicative_term_divide():
    parser = create_parser("10 / 5", True)

    term = parser.parse_multiplicative_term()

    assert term is not None
    assert term.left.value == 10
    assert term.right.value == 5
    assert term.op == EBinaryOperationType.Divide


def test_parse_multiplicative_term_nested():
    parser = create_parser("3 / 4 * 5", True)

    term = parser.parse_multiplicative_term()

    assert term is not None
    assert term.right.value == 5
    assert term.op == EBinaryOperationType.Multiply
    assert term.left.op == EBinaryOperationType.Divide
    assert term.left.left.value == 3
    assert term.left.right.value == 4


def test_parse_multiplicative_term_missing_right():
    parser = create_parser("10 * ", True)

    with pytest.raises(SyntaxException):
        parser.parse_multiplicative_term()


def test_parse_unary_term_pure():
    parser = create_parser("34", True)

    term = parser.parse_unary_term()

    assert term is not None
    assert term.value == 34


def test_parse_unary_term_minus():
    parser = create_parser("- 4", True)

    term = parser.parse_unary_term()

    assert term is not None
    assert term.operand.value == 4
    assert term.op == EUnaryOperationType.Minus


def test_parse_unary_term_negate():
    parser = create_parser("! true", True)

    term = parser.parse_unary_term()

    assert term is not None
    assert term.operand.value == True
    assert term.op == EUnaryOperationType.Negate


def test_parse_term_int_literal():
    parser = create_parser("34", True)

    term = parser.parse_term()

    assert term is not None
    assert term.value == 34


def test_parse_term_float_literal():
    parser = create_parser("3.14", True)

    term = parser.parse_term()

    assert term is not None
    assert term.value == 3.14


def test_parse_term_string_literal():
    parser = create_parser("\"Hello World\"", True)

    term = parser.parse_term()

    assert term is not None
    assert term.value == "Hello World"


def test_parse_term_boolean_literal():
    parser = create_parser("false", True)

    term = parser.parse_term()

    assert term is not None
    assert not term.value


def test_parse_term_access():
    parser = create_parser("user.name", True)

    term = parser.parse_term()

    assert term is not None
    assert isinstance(term, Access)
    assert term.name.identifier == "name"


def test_parse_term_cast():
    parser = create_parser("user.name as Name", True)

    term = parser.parse_term()

    assert term is not None
    assert isinstance(term, Cast)
    assert term.value.name.identifier == "name"
    assert term.type.identifier == "Name"


def test_parse_term_is_compare():
    parser = create_parser("user.name is Name", True)

    term = parser.parse_term()

    assert term is not None
    assert isinstance(term, IsCompare)
    assert term.value.name.identifier == "name"
    assert term.type.identifier == "Name"

# endregion
