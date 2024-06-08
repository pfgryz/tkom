from src.interpreter.types.enum_implementation import EnumImplementation
from src.interpreter.types.struct_implementation import StructImplementation
from src.interpreter.visitors.types_collector import TypesCollector
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.utils.buffer import StreamBuffer


def types_collector():
    program = """
    struct Rectangle {
        width: i32;
    }

    struct Square {
        side: i32;
    }

    struct Complex {
        a: Square;
    }

    struct Group {
        left: Square;
        right: Square;
    }
    
    enum Std {
        struct String {};
        struct Optional {};
    }
    
    enum UI {
        struct Window{
            name: Std::String;
            components: Std::Optional;
        };
        struct Square {};
        enum Color {
            struct Red {};
            struct Green{};
        };
    }
    """
    buffer = StreamBuffer.from_str(program)
    lexer = Lexer(buffer)
    parser = Parser(lexer)
    collector = TypesCollector()
    collector.visit(parser.parse())

    registry = collector._types_registry
    for type, value in registry._types.items():
        # print(type, value)
        if isinstance(value, EnumImplementation):
            print('Enum: ', value.name, '|', type)
            for v in value.variants.values():
                print('\t', v.name, v.declared_type)
        elif isinstance(value, StructImplementation):
            print('Struct: ', value.name, "|", type)
            for k, v in value.fields.items():
                print('\t', k, ':', v)
    print('Done!')


if __name__ == '__main__':
    types_collector()
