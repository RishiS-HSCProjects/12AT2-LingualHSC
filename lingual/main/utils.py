from enum import Enum

from flask import url_for

from lingual.main.forms import (
    ChangePasswordForm,
    ClearKanjiDataForm,
    ClearPractisedKanjiForm,
    DeleteAccountConfirmation,
    ResetGrammarProgressForm,
)

class AccountActionTypes(Enum):
    CHANGE_PASSWORD = 'change-password'
    JP_RESET_GRAMMAR = 'jp-reset-grammar'
    JP_CLEAR_PRACTISED_KANJI = 'jp-clear-practised-kanji'
    JP_CLEAR_KANJI_DATA = 'jp-clear-kanji-data'
    DELETE = 'delete'

    def get_modal(self):
        if self == self.CHANGE_PASSWORD:
            form = ChangePasswordForm()
            form.set_action(url_for('main.account', action=self.value))
            return form

        if self == self.JP_RESET_GRAMMAR:
            form = ResetGrammarProgressForm()
            form.set_action(url_for('main.account', action=self.value))
            return form

        if self == self.JP_CLEAR_PRACTISED_KANJI:
            form = ClearPractisedKanjiForm()
            form.set_action(url_for('main.account', action=self.value))
            return form

        if self == self.JP_CLEAR_KANJI_DATA:
            form = ClearKanjiDataForm()
            form.set_action(url_for('main.account', action=self.value))
            return form

        if self == self.DELETE:
            form = DeleteAccountConfirmation()
            from flask_login import current_user
            form.set_email(current_user.email) # type: ignore
            form.set_action(url_for('main.account', action=self.value))
            return form

        return None
