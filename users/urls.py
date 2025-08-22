from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import MyPasswordChangeView

app_name = "users"
urlpatterns = [
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"), 
    # path("password_change_form/", views.change_password, name="password_change_form"),

    path(
    "password/change/",
    MyPasswordChangeView.as_view(),
    name="password_change"
    ),

    path("password/change/done/", 
        auth_views.PasswordChangeDoneView.as_view(
            template_name="users/password_change_done.html"
        ), 
        name="password_change_done"),
]
