from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import CustomUser, FarmerProfile, BuyerProfile


class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('email', 'phone', 'full_name', 'role')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class CustomUserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        help_text='Raw passwords are not stored. Use the change-password form to update them.'
    )

    class Meta:
        model = CustomUser
        fields = (
            'email', 'phone', 'full_name', 'role', 'password',
            'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'
        )


class FarmerProfileInline(admin.StackedInline):
    model = FarmerProfile
    can_delete = False
    extra = 0
    max_num = 1
    verbose_name_plural = 'Farmer Profile'


class BuyerProfileInline(admin.StackedInline):
    model = BuyerProfile
    can_delete = False
    extra = 0
    max_num = 1
    verbose_name_plural = 'Buyer Profile'


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ('email', 'full_name', 'phone', 'role', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'phone', 'full_name')
    ordering = ('-created_at',)
    inlines = [FarmerProfileInline, BuyerProfileInline]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'full_name', 'role', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )


@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'village', 'district', 'state', 'farm_size_acres')
    search_fields = ('user__full_name', 'user__email', 'district', 'state', 'village')
    list_filter = ('state', 'district')


@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'business_name', 'buyer_type', 'district', 'state')
    search_fields = ('business_name', 'user__full_name', 'user__email', 'gstin')
    list_filter = ('buyer_type', 'state')
