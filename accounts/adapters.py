"""Custom django-allauth adapter for social account sign-ups."""

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Assigns the 'student' role to users created via Google (or any social)
    sign-up and populates first/last name from the provider profile.
    Auto-generates a username from the email to skip the intermediate signup form.
    """

    def is_auto_signup_allowed(self, request, sociallogin):
        """Always allow auto-signup — skip the intermediate form."""
        return True

    def pre_social_login(self, request, sociallogin):
        """
        If a user with this email already exists, connect the Google
        account to that existing user instead of creating a new one.
        """
        super().pre_social_login(request, sociallogin)

        # If the social account is already connected, nothing to do
        if sociallogin.is_existing:
            return

        email = sociallogin.account.extra_data.get('email')
        if not email:
            return

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            existing_user = User.objects.get(email=email)
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            pass

    def populate_user(self, request, sociallogin, data):
        """Auto-populate user fields so allauth can skip the signup form."""
        user = super().populate_user(request, sociallogin, data)

        # Generate a username from the email prefix if not already set
        if not user.username and data.get('email'):
            base_username = data['email'].split('@')[0]
            user.username = self._generate_unique_username(base_username)

        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        # Assign default student role
        user.role = 'student'

        # Populate name fields from the Google profile if missing
        extra_data = sociallogin.account.extra_data or {}
        if not user.first_name:
            user.first_name = extra_data.get('given_name', '')
        if not user.last_name:
            user.last_name = extra_data.get('family_name', '')

        user.save()
        return user

    @staticmethod
    def _generate_unique_username(base):
        """Append a number if the base username is already taken."""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        username = base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1
        return username
