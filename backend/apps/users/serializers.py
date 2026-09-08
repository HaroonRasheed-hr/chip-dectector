from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.users.models import User


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        normalized = value.lower()
        if User.objects.filter(email=normalized).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return normalized

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'created_at', 'updated_at')
        read_only_fields = fields
