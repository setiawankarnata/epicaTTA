from django.urls import path
from . import views
from .forms import UserLoginForm, PwdChangeForm, PwdResetForm, PwdResetConfirmForm
from django.contrib.auth import views as auth_views

app_name = 'users'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name="registration/login.html",
                                                authentication_form=UserLoginForm), name='login'),
    path('password_change/',
         auth_views.PasswordChangeView.as_view(template_name="registration/password_change_form.html",
                                               form_class=PwdChangeForm), name='pwdchange'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html',
                                                                 form_class=PwdResetForm), name='password_reset'),
    path('password_reset_confirm/<uid64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html',
                                                     form_class=PwdResetConfirmForm), name='password_reset_confirm'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('list_department/', views.list_department, name='list_department'),
    path('input_department/', views.InputDepartmentView.as_view(), name='input_department'),
    path('update_department/<uuid:id>/', views.UpdateDepartmentView.as_view(), name='update_department'),
    path('delete_department/<uuid:id>/', views.DeleteDepartmentView.as_view(), name='delete_department'),
    path('input_bulk_users/', views.InputBulkUsersView.as_view(), name='input_bulk_users'),
]
