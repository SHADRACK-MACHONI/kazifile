from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    CATEGORY_CHOICES = [
        ('id', 'Identification'),
        ('academic', 'Academic'),
        ('certificate', 'Certification'),
        ('cv', 'CV/Resume'),
        ('reference', 'Reference Letter'),
        ('other', 'Other'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True, default='other')
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.owner.username})"


class ShareLink(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='share_links')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Share link for {self.document.title}"


class AccessLog(models.Model):
    ACTION_CHOICES = [
        ('share_created', 'Share Link Created'),
        ('viewed', 'Document Viewed/Downloaded'),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='access_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_action_display()} - {self.document.title} at {self.timestamp}"