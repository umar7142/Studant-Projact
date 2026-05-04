from django.db import models
from django.contrib.auth.models import User

# =====================================================================
# CORE APPLICATION MODELS
# =====================================================================

class Student(models.Model):
    """
    Represents a student entity in the system.
    Stores core academic and personal details for system operations.
    """
    registration_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    email = models.EmailField(unique=True)
    class_name = models.CharField(max_length=50)
    course = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# =====================================================================
# AUTHENTICATION & SECURITY MODELS
# =====================================================================

class OTPRecord(models.Model):
    """
    Manages One-Time Passwords (OTP) for user verification, 2FA, and password resets.
    Maintains a strict one-to-one relationship with the Django User model.
    """
    # Links the OTP strictly to a single user instance. Deletes OTP if user is removed.
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Stores the generated 6-digit verification token
    otp_code = models.CharField(max_length=6)
    
    # Automatically timestamps creation to facilitate expiry logic and security audits
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - OTP: {self.otp_code}"
