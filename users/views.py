from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib import messages
from .forms import RegisterForm, ProfileForm, CustomPasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView

def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return redirect("users:register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect("users:register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect("users:register")

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()

        messages.success(request, "Account created successfully! Please login.")
        return redirect("users:login")

    return render(request, "registration/register.html")

@login_required
def profile(request):
    return render(request, "users/profile.html")

@login_required
def edit_profile(request):
    profile = request.user.profile  

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        avatar = request.FILES.get("avatar")

        # update user
        user = request.user
        user.username = username
        user.email = email
        user.save()

        # update profile
        if avatar:
            profile.avatar = avatar
            profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("users:profile")

    return render(request, "users/edit_profile.html", {
        "user": request.user,
        "profile": profile
    })

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect("books:catalog")
        else:
            messages.error(request, "Email or password incorrect!")
            return redirect("users:login")   

    return render(request, "registration/login.html")

def logout_view(request):
    logout(request)
    return redirect("users:login")

# @login_required
# def change_password(request):
#     if request.method == "POST":
#         form = PasswordChangeForm(user=request.user, data=request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Password successfully changed.")
#             return redirect("users:profile")
#     else:
#         form = PasswordChangeForm(user=request.user)

#     # Ubah label agar lebih jelas
#     form.fields["old_password"].label = "Old Password"
#     form.fields["new_password1"].label = "New Password"
#     form.fields["new_password2"].label = "Confirm New Password"

#     return render(request, "users/password_change_form.html", {"form": form})

class MyPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = "users/password_change_form.html"
    success_url = reverse_lazy("users:password_change_done")