from django.urls import path
from .views import (
    login_view,
    signup,
    verify_otp,
    resend_otp,
    logout_view,
    profile,
)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('signup/', signup, name='signup'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('resend-otp/', resend_otp, name='resend_otp'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile, name='profile'),
]

