from django.db import models
from django.contrib.auth.models import User # OTP model ke liye yeh import zaroori hai

# ==========================================
# STUDENT MODEL (Aapka Purana Code)
# ==========================================
class Student(models.Model):
    registration_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    email = models.EmailField(unique=True)
    class_name = models.CharField(max_length=50)
    course = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# ==========================================
# OTP RECORD MODEL (Naya Code)
# ==========================================
class OTPRecord(models.Model):
    # Har user ke sath sirf 1 OTP record jura hoga
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # 6 digit ka code save karne ki jagah
    otp_code = models.CharField(max_length=6)
    
    # Yeh automatically time save karega ke OTP kab bana tha (taake hum expiry check kar sakein)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - OTP: {self.otp_code}"