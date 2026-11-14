from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),

    # Neon authentication session endpoint
    path(
        'neon/session/',
        views.neon_session,
        name='neon_session'
    ),
]