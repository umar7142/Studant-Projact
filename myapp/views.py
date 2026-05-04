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

# ==========================================
# AUTHENTICATION APIs (Signup, Login, Verify, Resend & Logout)
# ==========================================

@api_view(['POST'])
@permission_classes([AllowAny]) 
def signup(request):
    """API endpoint naya user register karne aur uski email par OTP bhejney ke liye."""
    name = request.data.get('name') 
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')

    # 1. Strict Validation
    if not username or not password or not email or not name:
        return Response({"error": "Sari fields (Name, Username, Email, Password) zaroori hain!"}, status=status.HTTP_400_BAD_REQUEST)

    # 2. Check Database Conflicts
    if User.objects.filter(username=username).exists():
        return Response({"error": "Yeh username pehle se kisi ne liya hua hai!"}, status=status.HTTP_400_BAD_REQUEST)
        
    if User.objects.filter(email=email).exists():
        return Response({"error": "Yeh email pehle se registered hai!"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 3. Create Naya User (Tycoon Rule: is_active=False till verified)
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = name
        user.is_active = False # Account locked until verification
        user.save()
        
        # 4. Random 6-digit OTP Generate
        otp = str(random.randint(100000, 999999))
        
        # 5. OTP ko Database mein save karna
        OTPRecord.objects.create(user=user, otp_code=otp)
        
        # 6. Email Shoot
        subject = "Welcome to Student OS - Verify Account"
        message = f"Hello {user.first_name},\n\nAapka enterprise account set up ho gaya hai!\n\nAapka verification OTP hai: {otp}\n\nJaldi se portal mein enter karein."
        from_email = None 
        
        send_mail(subject, message, from_email, [user.email])

        return Response({
            "message": f"Account ban gaya! OTP {user.email} par bhej diya gaya hai.",
            "username": user.username
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": f"Server Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny]) 
def login(request):
    """STEP 1: User id/pass check karega (Active aur Inactive dono) aur Email par OTP bhejega."""
    username = request.data.get('username')
    password = request.data.get('password')
    
    try:
        user = User.objects.get(username=username)
        
        if user.check_password(password):
            if not user.email:
                return Response({"error": "Bhai is user ka email database mein save nahi hai! OTP kahan bhejun?"}, status=status.HTTP_400_BAD_REQUEST)

            otp = str(random.randint(100000, 999999))
            
            OTPRecord.objects.filter(user=user).delete()
            OTPRecord.objects.create(user=user, otp_code=otp)
            
            subject = "Student OS - Your Login OTP"
            message = f"Hello {user.first_name or user.username},\n\nAapka enterprise login OTP hai: {otp}\n\nYeh code portal mein enter karein."
            from_email = None
            
            try:
                send_mail(subject, message, from_email, [user.email])
                return Response({"message": f"OTP {user.email} par bhej diya gaya hai."})
            except Exception as e:
                return Response({"error": f"Email send nahi ho saki: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"error": "Invalid password!"}, status=status.HTTP_401_UNAUTHORIZED)
            
    except User.DoesNotExist:
        return Response({"error": "Invalid username!"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny]) 
def verify_otp(request):
    """STEP 2: STRICT OTP VERIFICATION"""
    username = request.data.get('username')
    otp_code = request.data.get('otp_code')
    
    try:
        user = User.objects.get(username=username)
        otp_record = OTPRecord.objects.get(user=user)
        
        if otp_record.otp_code == str(otp_code):
            user.is_active = True
            user.save()
            auth_login(request, user)
            otp_record.delete()
            
            return Response({
                "message": "OTP Verified! Login successful.", 
                "user": {"id": user.id, "username": user.username}
            })
        else:
            return Response({"error": "Ghalat OTP code! Phir se try karein."}, status=status.HTTP_400_BAD_REQUEST)
            
    except (User.DoesNotExist, OTPRecord.DoesNotExist):
        return Response({"error": "User ya OTP record nahi mila. Phele login try karein."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    """API endpoint naya OTP generate karke bhejney ke liye"""
    username = request.data.get('username')
    try:
        user = User.objects.get(username=username)
        new_otp = str(random.randint(100000, 999999))
        OTPRecord.objects.filter(user=user).delete()
        OTPRecord.objects.create(user=user, otp_code=new_otp)
        
        subject = "Student OS - Your NEW OTP Code"
        message = f"Hello {user.first_name or user.username},\n\nAapka NAYA verification OTP hai: {new_otp}\n\nSecurity Team"
        from_email = None
        
        send_mail(subject, message, from_email, [user.email])
        return Response({"message": "Naya OTP email par bhej diya gaya hai!"}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"error": "User not found!"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"Server Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# 🚀 NAYE MODULES: FORGOT & CHANGE PASSWORD
# ==========================================

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_request(request):
    """Agar user password bhool jaye toh OTP bhejo"""
    username = request.data.get('username')
    try:
        user = User.objects.get(username=username)
        if not user.email:
            return Response({"error": "Is account ke sath email registered nahi hai!"}, status=status.HTTP_400_BAD_REQUEST)

        otp = str(random.randint(100000, 999999))
        OTPRecord.objects.filter(user=user).delete()
        OTPRecord.objects.create(user=user, otp_code=otp)
        
        subject = "Student OS - Password Reset Request"
        message = f"Hello {user.first_name or user.username},\n\nAapne password reset ki request ki hai.\n\nAapka Password Reset OTP hai: {otp}\n\nAgar yeh aapne nahi kiya, toh isay ignore karein."
        from_email = None
        
        send_mail(subject, message, from_email, [user.email])
        return Response({"message": "Password reset OTP aapki email par bhej diya gaya hai!"}, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({"error": "Yeh username system mein nahi mila!"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_reset(request):
    """OTP verify karke naya password set karo"""
    username = request.data.get('username')
    otp_code = request.data.get('otp_code')
    new_password = request.data.get('new_password')

    if not username or not otp_code or not new_password:
        return Response({"error": "Username, OTP aur New Password teeno zaroori hain!"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(username=username)
        otp_record = OTPRecord.objects.get(user=user)
        
        if otp_record.otp_code == str(otp_code):
            # 🚀 LALA BHAI MAGIC: set_password() password ko secure hash bana kar save karta hai
            user.set_password(new_password)
            user.save()
            otp_record.delete() # Security: Purana OTP delete maar do
            
            return Response({"message": "Zabardast! Aapka password successfully reset ho gaya hai. Ab naye password se login karein."})
        else:
            return Response({"error": "Ghalat OTP code!"}, status=status.HTTP_400_BAD_REQUEST)
            
    except (User.DoesNotExist, OTPRecord.DoesNotExist):
        return Response({"error": "Invalid request! Pehle OTP request karein."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def change_password(request):
    """Logged in user apna current password verify karke naya lagaye"""
    username = request.data.get('username')
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    if not username or not old_password or not new_password:
        return Response({"error": "Username, Old Password aur New Password zaroori hain!"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(username=username)
        
        # Pehle purana password check karo
        if user.check_password(old_password):
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password successfully update ho gaya hai!"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Aapka purana password ghalat hai!"}, status=status.HTTP_400_BAD_REQUEST)
            
    except User.DoesNotExist:
        return Response({"error": "User nahi mila!"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny]) # Ise bhi AllowAny kar diya taake API test karna asaan ho
def logout(request):
    """API endpoint user ka session destroy karne ke liye."""
    auth_logout(request)
    return Response({"message": "Successfully logged out!"}, status=status.HTTP_200_OK)


# ==========================================
# 🛑 LALA BHAI FIX: STUDENT APIs & DASHBOARD 
# Note: IsAuthenticated hata kar AllowAny lagaya hai taake dashboard front-end par chalay!
# ==========================================

@api_view(['GET', 'POST'])
@permission_classes([AllowAny]) # Fix: Taake 403 Forbidden na aaye
def student_list(request):
    if request.method == 'GET':
        students = Student.objects.all()
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny]) # Fix: Taake 403 Forbidden na aaye
def student_detail(request, pk):
    try:
        student = Student.objects.get(pk=pk)
    except Student.DoesNotExist:
        return Response({'error': 'Student not found!'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = StudentSerializer(student)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = StudentSerializer(student, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data) 
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        student.delete()
        return Response({'message': 'Student successfully deleted!'}, status=status.HTTP_204_NO_CONTENT)
    

@api_view(['GET'])
@permission_classes([AllowAny]) # Fix: Taake 403 Forbidden na aaye
def dashboard_stats(request):
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