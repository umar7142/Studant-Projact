from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Student

# ================= AUTHENTICATION SERIALIZER =================
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        # extra_kwargs is liye lagaya taake password API mein wapis show na ho (Security)
        extra_kwargs = {'password': {'write_only': True}} 

    def create(self, validated_data):
        # create_user ka function password ko secure (hash/encrypt) kar deta hai
        user = User.objects.create_user(**validated_data)
        return user


# ================= STUDENT SERIALIZER =================
class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'