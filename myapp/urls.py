from django.urls import path

# 🛑 LALA BHAI UPDATE: Humne naye password wale functions bhi import kar liye hain
from .views import (
    signup, login, verify_otp, resend_otp, logout,
    forgot_password_request, forgot_password_reset, change_password, 
    student_list, student_detail, dashboard_stats
)

urlpatterns = [
    # ==========================================
    # 🛡️ AUTHENTICATION APIs
    # ==========================================
    path('signup/', signup, name='signup'),
    path('login/', login, name='login'),
    path('verify-otp/', verify_otp, name='verify-otp'),
    path('resend-otp/', resend_otp, name='resend-otp'),
    path('logout/', logout, name='logout'),

    # ==========================================
    # 🔑 PASSWORD MANAGEMENT APIs (NAYE RASTE)
    # ==========================================
    path('forgot-password-request/', forgot_password_request, name='forgot-password-request'),
    path('forgot-password-reset/', forgot_password_reset, name='forgot-password-reset'),
    path('change-password/', change_password, name='change-password'),

    # ==========================================
    # 👨‍🎓 STUDENT APIs & DASHBOARD
    # ==========================================
    path('students/', student_list, name='student-list'),
    path('students/<int:pk>/', student_detail, name='student-detail'),
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
]