from enum import Enum

from flask import url_for

from lingual.main.forms import DeleteAccountConfirmation

class AccountActionTypes(Enum):
    DELETE = 'delete'

    def get_modal(self):
        if self == self.DELETE:
            form = DeleteAccountConfirmation(
                title = "Delete Account",
                description = "Are you sure you want to delete your account?"
            )
            form.set_action(url_for('main.account', action='delete'))
            return form
        return None

pass