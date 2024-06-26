from tests.parser.test_parser import create_parser


def test_parser_e2e():
    program = """
    enum UI {
        struct Window {
            name: str;
            components: List;
        };
        
        enum Component {
        
        };
    }
    
    fn add_component_to_window(mut window: UI::Window, component: UI::Component) -> Result {
        if (component is UI::Component::Button) {
            let btn = component as UI::Component::Button;
            if (btn.enabled || btn.active && btn.allowAllowEvents) {
                register_click_handler(window, btn);
            }
        }
    
        if (list_contains(window.components, component)) {
            return Result::Error {};
        }
        
        window.components = list_add(window.components, component);
        return Result::Ok { value = window; };
    }
    
    fn main(args: Sys::Args) {
        create_main_window();
    
        mut let window: UI::Window = get_main_window();
        let component: UI::Component;
        component = create_component("Btn");
        
        let t: i32 = (2 + 3) * 2 / 1 - 0;
        while (t > 0) {
            t = t - 1;
            sleep(1);
        }
        
        match (add_component_to_window(window, component)) {
            Result::Err _ => {
                return;
            };
            Result::Ok w => {
                window = w;
            };
        }
    }
    """

    parser = create_parser(program)

    parser.parse()
