from flask_wtf import FlaskForm

class ModalForm(FlaskForm):
    """ Base form for modals. """
    title = "MODAL_TITLE"
    description = "MODAL_DESCRIPTION"
    action = ""

    def set_action(self, action_url: str) -> None:
        """ Method to set the form action URL. This allows dynamic setting of the form's target endpoint. """
        self.action = action_url

    def __init__(self, **kwargs):
        """ Override __init__ to set the title and description of the form based on class attributes. """
        super().__init__(**kwargs)
        self.title = getattr(self.__class__, "title", "Modal Form")
        self.description = getattr(self.__class__, "description", "")
