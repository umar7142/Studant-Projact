import random
from django.core.mail import send_mail
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User

from .models import Student, OTPRecord
from .serializers import StudentSerializer, UserSerializer

# =====================================================================
# AUTHENTICATION APIs (Signup, Login, 2FA Verification, Password Mgmt)
# =====================================================================

@api_view(['POST'])
@permission_classes([AllowAny]) 
def signup(request):
    """
    Registers a new user account, sets the initial state to inactive, 
    and dispatches an OTP to the provided email for verification.
    """
    name = request.data.get('name') 
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')

    # 1. Payload Validation
    if not all([username, password, email, name]):
        return Response({"error": "All fields (Name, Username, Email, Password) are required."}, status=status.HTTP_400_BAD_REQUEST)

    # 2. Prevent Duplicate Entries
    if User.objects.filter(username=username).exists():
        return Response({"error": "This username is already taken."}, status=status.HTTP_400_BAD_REQUEST)
        
    if User.objects.filter(email=email).exists():
        return Response({"error": "This email is already registered."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 3. Create User Profile (Locked until email is verified)
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = name
        user.is_active = False 
        user.save()
        
        # 4. Generate 6-Digit Security OTP
        otp = str(random.randint(100000, 999999))
        
        # 5. Store OTP in Database
        OTPRecord.objects.create(user=user, otp_code=otp)
        
        # 6. Dispatch Verification Email
        subject = "Student OS - Verify Your Account"
        message = f"Hello {user.first_name},\n\nYour enterprise account has been provisioned.\n\nYour verification OTP is: {otp}\n\nPlease enter this code in the portal to activate your account."
        from_email = None 
        
        send_mail(subject, message, from_email, [user.email])

        return Response({
            "message": f"Account created successfully. OTP has been sent to {user.email}.",
            "username": user.username
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": f"Internal Server Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny]) 
def login(request):
    """
    Validates user credentials and triggers a 2FA OTP to the registered email.
    Works for both active and pending-verification accounts.
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    try:
        user = User.objects.get(username=username)
        
        # Verify Credentials
        if user.check_password(password):
            if not user.email:
                return Response({"error": "No email associated with this account. Cannot dispatch OTP."}, status=status.HTTP_400_BAD_REQUEST)

            # Generate and overwrite any existing OTPs for security
            otp = str(random.randint(100000, 999999))
            OTPRecord.objects.filter(user=user).delete()
            OTPRecord.objects.create(user=user, otp_code=otp)
            
            # Dispatch 2FA Email
            subject = "Student OS - Login Verification"
            message = f"Hello {user.first_name or user.username},\n\nYour secure login OTP is: {otp}\n\nPlease do not share this code with anyone."
            from_email = None
            
            try:
                send_mail(subject, message, from_email, [user.email])
                return Response({"message": f"OTP sent successfully to {user.email}."})
            except Exception as e:
                return Response({"error": f"Failed to dispatch email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"error": "Invalid credentials provided."}, status=status.HTTP_401_UNAUTHORIZED)
            
    except User.DoesNotExist:
        return Response({"error": "User account not found."}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny]) 
def verify_otp(request):
    """
    Validates the provided OTP. Upon successful validation, activates the user
    and initializes the login session.
    """
    username = request.data.get('username')
    otp_code = request.data.get('otp_code')
    
    try:
        user = User.objects.get(username=username)
        otp_record = OTPRecord.objects.get(user=user)
        
        # Strict OTP Check
        if otp_record.otp_code == str(otp_code):
            user.is_active = True
            user.save()
            auth_login(request, user)
            
            # Destroy OTP record after successful use
            otp_record.delete()
            
            return Response({
                "message": "OTP Verified. Login successful.", 
                "user": {"id": user.id, "username": user.username}
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid OTP code. Please try again."}, status=status.HTTP_400_BAD_REQUEST)
            
    except (User.DoesNotExist, OTPRecord.DoesNotExist):
        return Response({"error": "User or OTP record not found. Please request a new OTP."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    """Generates and dispatches a fresh OTP for the user."""
    username = request.data.get('username')
    
    try:
        user = User.objects.get(username=username)
        new_otp = str(random.randint(100000, 999999))
        
        # Replace old OTP with the new one
        OTPRecord.objects.filter(user=user).delete()
        OTPRecord.objects.create(user=user, otp_code=new_otp)
        
        subject = "Student OS - Your New Verification Code"
        message = f"Hello {user.first_name or user.username},\n\nYour new verification OTP is: {new_otp}\n\nRegards,\nSecurity Team"
        from_email = None
        
        send_mail(subject, message, from_email, [user.email])
        return Response({"message": "A fresh OTP has been sent to your email."}, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({"error": "User account not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"Internal Server Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =====================================================================
# PASSWORD MANAGEMENT MODULE
# =====================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_request(request):
    """Initiates the password recovery process by sending an OTP."""
    username = request.data.get('username')
    try:
        user = User.objects.get(username=username)
        if not user.email:
            return Response({"error": "No email linked to this account for recovery."}, status=status.HTTP_400_BAD_REQUEST)

        otp = str(random.randint(100000, 999999))
        OTPRecord.objects.filter(user=user).delete()
        OTPRecord.objects.create(user=user, otp_code=otp)
        
        subject = "Student OS - Password Reset Request"
        message = f"Hello {user.first_name or user.username},\n\nWe received a request to reset your password.\n\nYour Password Reset OTP is: {otp}\n\nIf you did not request this, please ignore this email safely."
        from_email = None
        
        send_mail(subject, message, from_email, [user.email])
        return Response({"message": "Password recovery OTP has been dispatched to your email."}, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({"error": "Username not found in the system."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_reset(request):
    """Verifies recovery OTP and updates the user's password."""
    username = request.data.get('username')
    otp_code = request.data.get('otp_code')
    new_password = request.data.get('new_password')

    if not all([username, otp_code, new_password]):
        return Response({"error": "Username, OTP, and New Password are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(username=username)
        otp_record = OTPRecord.objects.get(user=user)
        
        if otp_record.otp_code == str(otp_code):
            # Cryptographically hash and save the new password
            user.set_password(new_password)
            user.save()
            
            # Security measure: Destroy OTP after use
            otp_record.delete() 
            
            return Response({"message": "Password reset successfully. You can now log in with your new credentials."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid OTP code provided."}, status=status.HTTP_400_BAD_REQUEST)
            
    except (User.DoesNotExist, OTPRecord.DoesNotExist):
        return Response({"error": "Invalid request sequence. Please initiate the password reset process first."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def change_password(request):
    """Allows an authenticated user to update their password after verifying the old one."""
    username = request.data.get('username')
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    if not all([username, old_password, new_password]):
        return Response({"error": "Username, Old Password, and New Password are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(username=username)
        
        # Authenticate current password before allowing change
        if user.check_password(old_password):
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "The old password provided is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
            
    except User.DoesNotExist:
        return Response({"error": "User account not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny]) 
def logout(request):
    """Destroys the current user session."""
    auth_logout(request)
    return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)


# =====================================================================
# CORE APPLICATION APIs (Student Management & Analytics)
# =====================================================================

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def student_list(request):
    """Handles fetching all students (GET) and adding a new student (POST)."""
    if request.method == 'GET':
        students = Student.objects.all()
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'POST':
        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny])
def student_detail(request, pk):
    """Handles fetching, updating, or deleting a specific student record."""
    try:
        student = Student.objects.get(pk=pk)
    except Student.DoesNotExist:
        return Response({'error': 'Student record not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = StudentSerializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = StudentSerializer(student, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK) 
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        student.delete()
        return Response({'message': 'Student record deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
    

@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_stats(request):
    """Aggregates system metrics for the administrative dashboard."""
    try:
        total_students = Student.objects.count()
        unique_classes = Student.objects.values('class_name').distinct().count()
        unique_courses = Student.objects.values('course').distinct().count()
        
        return Response({
            "total_students": total_students,
            "total_classes": unique_classes,
            "total_courses": unique_courses
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
