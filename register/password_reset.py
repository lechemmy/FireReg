from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class RestrictedPasswordResetForm(PasswordResetForm):
    """
    Custom password reset form that only allows superusers and fire marshals to reset their passwords.
    """
    def clean_email(self):
        email = self.cleaned_data["email"]

        # Check if the email exists in the system
        if not User.objects.filter(email=email).exists():
            raise ValidationError(_("There is no user registered with this email address."))

        # Check if the user is a superuser or fire marshal
        user = User.objects.get(email=email)
        fire_marshal_group = Group.objects.filter(name='Fire Marshal').first()

        if not (user.is_superuser or (fire_marshal_group and user.groups.filter(id=fire_marshal_group.id).exists())):
            raise ValidationError(_("Only superusers and fire marshals can reset their passwords."))

        return email

class RestrictedPasswordResetView(PasswordResetView):
    """
    Custom password reset view that uses the restricted form.
    """
    form_class = RestrictedPasswordResetForm
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = '/accounts/password_reset/done/'
    from_email = None  # Uses DEFAULT_FROM_EMAIL from settings
