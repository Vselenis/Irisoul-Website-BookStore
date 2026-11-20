from django.core.validators import RegexValidator
from django.db import models

# Create your models here.

class ContactMessage(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(
            r'^[0-9+()\- ]{6,20}$',
            'Enter a valid phone number: 6 to 20 characters, using digits, spaces and + - ( ).',
        )],
    )
    message = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} - {self.email}'