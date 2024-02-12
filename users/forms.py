from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, PasswordChangeForm, SetPasswordForm
from .models import Profile, Department


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "description"]


class UpdateDepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "description"]


class PwdResetConfirmForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label='New password', widget=forms.PasswordInput(
            attrs={'class': 'form-control mb-3', 'placeholder': 'New Password', 'id': 'form-newpass'}))
    new_password2 = forms.CharField(
        label='Repeat password', widget=forms.PasswordInput(
            attrs={'class': 'form-control mb-3', 'placeholder': 'New Password', 'id': 'form-new-pass2'}))


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control mb-3', 'placeholder': 'Username/Email :', 'id': 'login-username'}))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'Password :',
            'id': 'login-pwd',
        }
    ))


class PwdChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Old Password', widget=forms.PasswordInput(
            attrs={'class': 'form-control mb-3', 'placeholder': 'Old Password', 'id': 'old_password'}))
    new_password1 = forms.CharField(
        label='New password', widget=forms.PasswordInput(
            attrs={'class': 'form-control mb-3', 'placeholder': 'New Password', 'id': 'new_password'}))
    new_password2 = forms.CharField(
        label='Repeat password', widget=forms.PasswordInput(
            attrs={'class': 'form-control mb-3', 'placeholder': 'Retype New Password', 'id': 'retype_new_password'}))


class PwdResetForm(PasswordResetForm):
    email = forms.EmailField(max_length=254, widget=forms.TextInput(
        attrs={'class': 'form-control mb-3', 'placeholder': 'Email', 'id': 'form-email'}))

    def clean_email(self):
        email = self.cleaned_data['email']
        test = User.objects.filter(email=email)
        if not test:
            raise forms.ValidationError(
                'Unfortunatley we can not find that email address')
        return email


class UserEditForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Firstname', min_length=4, max_length=50, widget=forms.TextInput(
            attrs={'class': 'form-control mb-3', 'placeholder': 'Firstname', 'id': 'form-firstname'}))

    last_name = forms.CharField(
        label='Lastname', min_length=4, max_length=50, widget=forms.TextInput(
            attrs={'class': 'form-control mb-3', 'placeholder': 'Lastname', 'id': 'form-lastname'}))

    # email = forms.EmailField(
    #     max_length=200, widget=forms.TextInput(
    #         attrs={'class': 'form-control mb-3', 'placeholder': 'Email', 'id': 'form-email'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name')

    #
    #     def clean_email(self):
    #         email = self.cleaned_data['email']
    #         if User.objects.filter(email=email).exists():
    #             raise forms.ValidationError(
    #                 'Please use another Email, that is already taken')
    #         return email
    #
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['last_name'].required = False
        # self.fields['email'].required = False


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['gender', 'photo', 'bod', 'mobile', 'profile2department', 'email_atasan', 'cpmd', 'secretary', 'pic_epica']

        # widgets = {
        #     'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': '5'}),
        # }


class InputBulkUserForm(forms.Form):
    file_content = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control'}))
