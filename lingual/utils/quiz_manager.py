from enum import Enum, auto # Auto import required for children to use auto() without importing it themselves.
from wtforms import IntegerField, SelectMultipleField, SubmitField, ValidationError
from wtforms.validators import DataRequired
from lingual.utils.modals import ModalForm

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

    @property
    def is_enabled(self) -> bool:
        """ Optional method to indicate if the quiz type is currently enabled or not.
            This can be used to disable quiz types that are not yet implemented or temporarily unavailable.
            Override in subclasses if needed. By default, all quiz types are enabled. """
        return True

    def get_modal(self) -> "QuizForm":
        """ Method to return a modal form for quiz configuration.
        Override in subclasses if specific configuration is needed for the quiz type.
        If not overridden, preset Quizzes options will be selected with no way for
        users to edit them.  
        """

        raise NotImplementedError(f"No modal implemented for quiz type: {self.name}")

class QuizForm(ModalForm):
    """ Base form for quiz configuration. Specific quiz types can extend this form to add more fields as needed. """
    title = "QUIZ_TITLE"
    description = "QUIZ_DESCRIPTION"

    submit = SubmitField("Generate Quiz")
    
    def __init__(self, **kwargs):
        """ Override __init__ to set the title and description of the form based on class attributes. """
        super().__init__(**kwargs)
        self.title = getattr(self.__class__, "title", "Quiz Configuration")

class LessonQuizConfigForm(QuizForm):
    title = "Lesson Quiz Configuration"

    max_questions = IntegerField(
        "Max Questions",
        validators=[DataRequired()],
        default=10
    )

    lessons = SelectMultipleField(
        "Lessons",
        choices=[]
    )

    def set_lesson_choices(self, choices: list[tuple[str, str]]) -> None:
        self.lessons.choices = choices # type: ignore
        lesson_values = [value for value, _ in choices] # Build a new list of choice values, omitting the labels

        # Default to all lessons only when opening the form initially.
        selected_values = self.lessons.data or [] # Get the currently selected values (if any)
        if not self.is_submitted() and not selected_values: # Ensure form has not been submitted to avoid overwriting selections
            self.lessons.data = lesson_values # Select all lessons by default if no selections have been made yet.
            return

        if not selected_values:
            # If the form was submitted but no lessons were selected, we should not default to all lessons.
            self.lessons.data = []
            return # Exit and allow for validation error

        # Keep only values that still exist in the configured choices.
        if any(value not in lesson_values for value in selected_values): # If any value is not in the new choice list, choices need to be reset
            # This prevents edge cases where a user might have selected lessons that are no longer available due to changes in the lesson list.
            self.lessons.data = [value for value in selected_values if value in lesson_values]

    def validate_max_questions(self, field):
        """ Overwrite this method in subclasses to provide specific validation for max questions if needed. """

        # No integer validation is needed here since WTForms can handle that.
        if ((data := field.data) < 5) or (data > 50):
            # Ensure max questions are between 5 and 50 
            raise ValidationError("Max questions must be between 5 and 50.")

    def validate_lessons(self, field):
        """ Validate that at least one lesson is selected. """
        if not field.data:
            raise ValidationError("Please select at least one lesson.")
