from enum import Enum, auto

class Element:
    """Base class for all form elements."""
    def __init__(self, label: str):
        self.label: str = label
        self.disabled: bool = False # Initialize disabled state to False by default

    def is_disabled(self) -> bool:
        return self.disabled

    def set_disabled(self, disabled: bool = True) -> None:
        self.disabled = disabled

class Form:
    """
        Represents a popup form that can contain various elements like text, buttons, dropdowns, etc.
        To create modal forms, instantiate this class with a title and a list of elements, and pass
        it to the modal macro for rendering.    
    """
    def __init__(self, title: str, action: str, method: str|None = None, elements: list[Element]|None = None):
        self.title: str = title
        self.action: str = action
        self.method: str = method if method is not None else "POST"
        self.elements: list[Element] = elements if elements is not None else []

    def add_element(self, element: Element) -> "Form":

        if element.label in [e.label for e in self.get_elements()]:
            raise ValueError(f"Element with label '{element.label}' already exists in the form. Element labels must be unique.")

        self.elements.append(element)
        return self
    
    def get_elements(self) -> list[Element]:
        return self.elements

class Text (Element):
    """ Simple text element for displaying information. """
    
    def __init__(self, title: str, content: str):
        super().__init__(title)
        self.content: str = content

class Button (Element):
    """ Button element that can perform different actions based on its type. """
    def __init__(self, label: str, target):
        super().__init__(label)
        self.target: str|Form = target

class ButtonRoute(Button):
    """ Target will be a Flask route endpoint. """
    def __init__(self, label: str, target: str):
        super().__init__(label, target)

class ButtonExternal(Button):
    """ Target will be an external URL. """
    def __init__(self, label: str, target: str):
        super().__init__(label, target)

class ButtonForm(Button):
    """ Target will be another Form that opens as a modal when the button is clicked. """
    def __init__(self, label: str, target: Form):
        super().__init__(label, target)
    
class Dropdown (Element):
    """ Dropdown element for selecting from multiple options. """
    class DropdownOption:
        """ Represents a single option in a dropdown menu. """
        def __init__(self, label: str, value: str):
            self.label: str = label
            self.value: str = value
    
    def __init__(self, label: str, options: list[DropdownOption]):
        super().__init__(label)
        self.options: list[Dropdown.DropdownOption] = options

class Input (Element):
    """ Input element for user data entry. """
    class InputType(Enum):
        """ Enumeration for input types. Determines the type of input field to display.
        - TEXT: Standard text input field.
        - AREA: Multi-line text area for longer input.
        - NUMBER: Input field that only accepts numeric values.
        - EMAIL: Input field that validates email addresses.
        - PASSWORD: Input field that hides the entered text for password input.
        """
        TEXT = auto()
        AREA = auto()
        NUMBER = auto()
        EMAIL = auto()
        PASSWORD = auto()
    
    def __init__(self, label: str, placeholder: str = ""):
        super().__init__(label)
        self.placeholder: str = placeholder

class RadioSelect (Element):
    """ Radio select element for choosing one option from a set. """
    class RadioOption:
        """ Represents a single option in a radio select. """
        def __init__(self, label: str, value: str):
            self.label: str = label
            self.value: str = value
    def __init__(self, label: str, options: list[RadioOption], allow_multiple: bool = False,  allow_none: bool = False):
        super().__init__(label)
        self.options: list[RadioSelect.RadioOption] = options
        self.allow_multiple: bool = allow_multiple
        self.allow_none: bool = allow_none

class Slider (Element):
    """ Slider element for selecting a value from a range. """
    def __init__(self, label: str, min_value: int, max_value: int, default: int = None, step: int = 1): # type: ignore
        super().__init__(label)
        self.min_value: int = min_value
        self.max_value: int = max_value
        self.step: int = step
        self.default_value: int = default if default is not None else min_value
