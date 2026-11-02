from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, FarmerProfile, BuyerProfile
from .serializers import (
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    UserDetailSerializer,
    FarmerProfileSerializer,
    BuyerProfileSerializer,
)
from .permissions import IsFarmer, IsBuyer


class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Public registration endpoint for Farmers and Buyers.
    Generates JWT tokens immediately upon successful registration.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user = CustomUser.objects.select_related('farmer_profile', 'buyer_profile').get(pk=user.pk)

        # Generate JWT tokens for immediate authentication
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        user_data = UserDetailSerializer(user).data

        return Response(
            {
                "message": f"Account successfully created for {user.full_name}.",
                "user": user_data,
                "access": access_token,
                "refresh": str(refresh),
                "tokens": {
                    "refresh": str(refresh),
                    "access": access_token,
                }
            },
            status=status.HTTP_201_CREATED
        )


class CustomLoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    Public login endpoint returning JWT tokens and standardized user metadata.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    GET /api/v1/auth/me/
    PATCH /api/v1/auth/me/
    Retrieves or updates the currently authenticated user's details and profile.
    """
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return CustomUser.objects.select_related('farmer_profile', 'buyer_profile').get(
            pk=self.request.user.pk
        )


class FarmerProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/v1/farmers/profile/
    PATCH /api/v1/farmers/profile/
    Allows an authenticated Farmer to view and update farm location, size, and language.
    """
    serializer_class = FarmerProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmer]

    def get_object(self):
        profile, _ = FarmerProfile.objects.get_or_create(user=self.request.user)
        return profile


class BuyerProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/v1/buyers/profile/
    PATCH /api/v1/buyers/profile/
    Allows an authenticated Buyer to view and update business info, GSTIN, and location.
    """
    serializer_class = BuyerProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsBuyer]

    def get_object(self):
        profile, _ = BuyerProfile.objects.get_or_create(user=self.request.user)
        return profile
