from enum import Enum, auto # Auto import required for childen to use auto() without importing it themselves.=
from flask_wtf import FlaskForm

class TypeEnum(Enum):
    """
    Base enum for quiz types. Each quiz type should inherit from this and define its own members.
    This allows for type safety and easy retrieval of quiz types.

    Example usage:
    ```
    class ModuleTypes(TypeEnum):
        GRAMMAR = quiz_manager.auto()
        VOCAB = quiz_manager.auto()
        ALPHABET = quiz_manager.auto()
    ```
    """

    def __str__(self) -> str:
        """ Do not override. """
        return self.label # Simple string representation is the label of the enum member.

    def __repr__(self) -> str:
        """ Do not override. """
        return f"<{self.__class__.__name__}.{self.name}(value={self.value})>"

    @property
    def label(self) -> str:
        """ Human-readable name for the quiz type. By default, it title-cases the enum member name.
            Override this method in subclasses if a different naming convention is desired.
        """
        return self.name.title()
    
    @property
    def description(self) -> str:
        """ Optional method to provide a description for the quiz type.
            This will be used in the quiz interface to give users more context about the quiz type.
            Override in subclasses if needed. """
        return ""

    def get_modal(self) -> "QuizForm":
        """ Method to return a modal form for quiz configuration.
        Override in subclasses if specific configuration is needed for the quiz type.
        If not overridden, preset Quizzes options will be selected with no way for
        users to edit them.  
        """

        raise NotImplementedError(f"No modal implemented for quiz type: {self.name}")

class QuizForm(FlaskForm):
    """ Base form for quiz configuration. Specific quiz types can extend this form to add more fields as needed. """
    title = "QUIZ_TITLE"
    description = "QUIZ_DESCRIPTION"
    action = ""

    def set_action(self, action_url: str) -> None:
        """ Method to set the form action URL. This allows dynamic setting of the form's target endpoint. """
        self.action = action_url
