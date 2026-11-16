from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
import secrets


class EmailVerificationOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_otps')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Verification OTP'
        verbose_name_plural = 'Email Verification OTPs'

    @classmethod
    def generate_otp(cls, user):
        # Invalidate previous unverified OTPs for this user
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        code = f"{secrets.randbelow(900000) + 100000}"
        expiry = timezone.now() + datetime.timedelta(minutes=10)
        return cls.objects.create(
            user=user,
            otp_code=code,
            expires_at=expiry
        )

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at and self.attempts < 5

    def __str__(self):
        return f"OTP for {self.user.username} ({self.otp_code})"

