import re
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, FarmerProfile, BuyerProfile


class FarmerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerProfile
        fields = [
            'id', 'village', 'district', 'state', 'farm_size_acres',
            'preferred_language', 'latitude', 'longitude', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']


class BuyerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerProfile
        fields = [
            'id', 'business_name', 'buyer_type', 'gstin', 'address',
            'district', 'state', 'latitude', 'longitude', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Unified user detail serializer used across login, registration, and /auth/me/.
    Provides both explicit role profile accessors and a unified 'profile' field.
    """
    farmer_profile = FarmerProfileSerializer(read_only=True, allow_null=True)
    buyer_profile = BuyerProfileSerializer(read_only=True, allow_null=True)
    profile = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'phone', 'full_name', 'role',
            'is_active', 'created_at', 'farmer_profile', 'buyer_profile', 'profile'
        ]
        read_only_fields = ['id', 'email', 'role', 'is_active', 'created_at']

    def get_profile(self, obj):
        if obj.role == CustomUser.Role.FARMER and hasattr(obj, 'farmer_profile'):
            return FarmerProfileSerializer(obj.farmer_profile).data
        elif obj.role == CustomUser.Role.BUYER and hasattr(obj, 'buyer_profile'):
            return BuyerProfileSerializer(obj.buyer_profile).data
        return None


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    # Optional initial profile metadata
    village = serializers.CharField(write_only=True, required=False, allow_blank=True)
    district = serializers.CharField(write_only=True, required=False, allow_blank=True)
    state = serializers.CharField(write_only=True, required=False, allow_blank=True)
    farm_size_acres = serializers.DecimalField(max_digits=7, decimal_places=2, write_only=True, required=False, allow_null=True)
    business_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    buyer_type = serializers.CharField(write_only=True, required=False, allow_blank=True)
    gstin = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'phone', 'full_name', 'role', 'password', 'password_confirm',
            'village', 'district', 'state', 'farm_size_acres', 'business_name', 'buyer_type', 'gstin'
        ]
        read_only_fields = ['id']

    def validate_phone(self, value):
        phone = (value or '').strip()
        if not re.fullmatch(r'\d{10,15}', phone):
            raise serializers.ValidationError('Enter a valid 10 to 15 digit phone number.')
        return phone

    def validate(self, attrs):
        if 'email' in attrs:
            attrs['email'] = attrs['email'].strip().lower()
        if 'full_name' in attrs:
            attrs['full_name'] = attrs['full_name'].strip()

        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        # Ensure role is valid (Admin cannot self-register through this endpoint)
        if attrs.get('role') not in [CustomUser.Role.FARMER, CustomUser.Role.BUYER]:
            raise serializers.ValidationError({"role": "Role must be either FARMER or BUYER."})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        village = validated_data.pop('village', '').strip()
        district = validated_data.pop('district', '').strip()
        state = validated_data.pop('state', '').strip()
        farm_size_acres = validated_data.pop('farm_size_acres', None)
        business_name = validated_data.pop('business_name', '').strip()
        buyer_type = validated_data.pop('buyer_type', BuyerProfile.BuyerType.WHOLESALER)
        gstin = validated_data.pop('gstin', '').strip()

        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(
            password=password,
            **validated_data
        )

        # Update initial profile (idempotent with post_save signal)
        if user.role == CustomUser.Role.FARMER:
            profile, _ = FarmerProfile.objects.get_or_create(user=user)
            if village:
                profile.village = village
            if district:
                profile.district = district
            if state:
                profile.state = state
            if farm_size_acres is not None:
                profile.farm_size_acres = farm_size_acres
            profile.save()
        elif user.role == CustomUser.Role.BUYER:
            profile, _ = BuyerProfile.objects.get_or_create(user=user)
            profile.business_name = business_name or user.full_name
            if district:
                profile.district = district
            if state:
                profile.state = state
            if gstin:
                profile.gstin = gstin
            if buyer_type in BuyerProfile.BuyerType.values:
                profile.buyer_type = buyer_type
            profile.save()

        # Reload updated relations from DB so in-memory cache reflects newly saved fields
        user.refresh_from_db()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Enhanced SimpleJWT serializer that normalizes email, authenticates,
    and returns a standardized UserDetailSerializer payload alongside JWT tokens.
    """
    def validate(self, attrs):
        if 'email' in attrs:
            attrs['email'] = attrs['email'].strip().lower()

        data = super().validate(attrs)
        user = CustomUser.objects.select_related('farmer_profile', 'buyer_profile').get(pk=self.user.pk)
        data['user'] = UserDetailSerializer(user).data
        return data
