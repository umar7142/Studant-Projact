from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Student

# =====================================================================
# AUTHENTICATION SERIALIZERS
# =====================================================================

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User authentication.
    Handles data validation and secure user instance creation.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        # Security constraint: Ensure the password is never exposed in API responses
        extra_kwargs = {'password': {'write_only': True}} 

    def create(self, validated_data):
        """
        Overrides the default create method to ensure the password 
        is cryptographically hashed before saving to the database.
        """
        user = User.objects.create_user(**validated_data)
        return user


# =====================================================================
# CORE APPLICATION SERIALIZERS
# =====================================================================

class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer for Student records.
    Transforms Student model instances into JSON format and vice versa.
    """
    class Meta:
        model = Student
        fields = '__all__'
