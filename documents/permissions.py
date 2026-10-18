from accounts.permissions import IsAdminRole
from rest_framework.permissions import IsAuthenticated


class CanUploadDocument(IsAdminRole):
    """Only admins can upload documents."""
    message = "Only administrators can upload documents."


class CanDeleteDocument(IsAdminRole):
    """Only admins can delete documents."""
    message = "Only administrators can delete documents."
