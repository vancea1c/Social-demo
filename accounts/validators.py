import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _



class StrongPasswordValidator:
    def __call__(self, password, user=None):
        errors = []
        
        if len(password) < 8:
            errors.append(_("Your password must have at least 8 characters."))

        if not re.search(r"[A-Z]", password):
            errors.append(
                _("Your password must contain at least one UPPER CASE (A-Z).")
            )

        if not re.search(r"[a-z]", password):
            errors.append(
                _("Your password must contain at least one lower case (a-z).")
            )

        if not re.search(r"\d", password):
            errors.append(_("Your password must contain at least one digit (0-9)."))

        symbol_pattern = r'[!@#$%^&*()_+\-=\[\]{};\'":\\|,.<>\/?]'
        if not re.search(symbol_pattern, password):
            errors.append(
                _("Your password must contain at least one symbol (ex: !, @, #, etc...)")
            )
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Your password must have at least 8 characters"
            "and contain at least one of each of the followings: "
            "UPPER CASE, lower case, digit and symbol."
        )


class UsernameValidator:
    def __call__(self, username, user=None):
        errors = []

        if len(username) < 1:
            errors.append(_("Please choose a username."))

        if len(username) < 3:
            errors.append(_("Your Username is too short."))
            
        if len(username) > 20:
            errors.append(_("Username cannot exceed 20 characters."))

        pattern = r"^[a-zA-Z0-9_.]+$"
        if not re.match(pattern, username):
            errors.append(
                _("Usernames can only use letters, numbers, underscores and periods.")
            )

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Your username must have at least 3 characters"
            "and can only contain letters, numbers, "
            "underscores and periods."
        )

class FirstNameValidator:
    def __call__(self, first_name, user=None):
        errors = []

        if len(first_name) < 1:
            errors.append(_("Please choose a first name."))

        if len(first_name) < 3:
            errors.append(_("Your first name is too short."))

        if len(first_name) > 30:
            errors.append(_("First name cannot exceed 30 characters."))
        pattern = r"^[a-zA-Z]+$"
        if not re.match(pattern, first_name):
            errors.append(
                _("First names can only use letters (a-z, A-Z).")
            )
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Your first name must have at least 3 characters"
            "and cannot exceed 30 characters."
        )
        
class LastNameValidator:
    def __call__(self, last_name, user=None):
        errors = []

        if len(last_name) < 1:
            errors.append(_("Please choose a last name."))

        if len(last_name) < 3:
            errors.append(_("Your last name is too short."))

        if len(last_name) > 20:
            errors.append(_("Last name cannot exceed 20 characters."))
            
        pattern = r"^[a-zA-Z]+$"
        if not re.match(pattern, last_name):
            errors.append(
                _("Last names can only use letters (a-z, A-Z).")
            )

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Your last name must have at least 3 characters"
            "and cannot exceed 20 characters."
        )
