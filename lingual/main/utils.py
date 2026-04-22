from enum import Enum
from flask import url_for
from lingual.main.forms import (
    ChangePasswordForm,
    ClearKanjiDataForm,
    ClearPractisedKanjiForm,
    DeleteAppConfirmation,
    DeleteAccountConfirmation,
    ResetGrammarProgressForm,
    UpdateInfoForm,
)

class AccountActionTypes(Enum):
    """ Enum for different types of account actions that can be performed on the account page, such as changing password, updating info, deleting account/app, and various Japanese-specific actions. Each type corresponds to a specific form/modal that will be rendered when the action is triggered. """
    CHANGE_PASSWORD = 'change-password'
    UPDATE_INFO = 'update-info'
    DELETE_APP = 'delete-app'
    JP_RESET_GRAMMAR = 'jp-reset-grammar'
    JP_CLEAR_PRACTISED_KANJI = 'jp-clear-practised-kanji'
    JP_CLEAR_KANJI_DATA = 'jp-clear-kanji-data'
    DELETE = 'delete'

    def get_modal(self):
        """ Return the appropriate form/modal object for each account action type, with the form's action URL set to the corresponding route for handling that action. """

        form = None # Initialise form variable

        if self == self.CHANGE_PASSWORD:
            form = ChangePasswordForm()
            form.set_action(url_for('main.account', action=self.value))

        elif self == self.UPDATE_INFO:
            form = UpdateInfoForm()
            form.set_action(url_for('main.account', action=self.value))

        elif self == self.JP_RESET_GRAMMAR:
            form = ResetGrammarProgressForm()
            form.set_action(url_for('main.account', action=self.value))

        elif self == self.JP_CLEAR_PRACTISED_KANJI:
            form = ClearPractisedKanjiForm()
            form.set_action(url_for('main.account', action=self.value))

        elif self == self.JP_CLEAR_KANJI_DATA:
            form = ClearKanjiDataForm()
            form.set_action(url_for('main.account', action=self.value))

        elif self == self.DELETE:
            form = DeleteAccountConfirmation()
            from flask_login import current_user
            form.set_email(current_user.email)
            form.set_action(url_for('main.account', action=self.value))

        elif self == self.DELETE_APP:
            form = DeleteAppConfirmation()
            form.set_action(url_for('main.account', action=self.value))
        
        return form # Return form if valid type
