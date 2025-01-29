from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    email_otp = models.CharField(max_length=6, null=True, blank=True)
    
class FileConversion(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='file_conversion')
    original_file = models.FileField(upload_to='uploads/')
    converted_file = models.FileField(upload_to='converted/')
    conversion_type = models.CharField(max_length=50)  # "PDF to Image" or "Image to PDF"
    created_at = models.DateTimeField(auto_now_add=True)
    download_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.user
    
