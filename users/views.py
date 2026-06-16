from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.urls import reverse
from .models import CustomUser
from .tokens import account_activation_token
from django.http import HttpResponse


# from django.shortcuts import render, redirect
# from django.contrib.auth import login
# from django.utils.http import urlsafe_base64_decode
# from django.utils.encoding import force_str
# from .models import CustomUser
# from .tokens import account_activation_token



def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate account until email confirmation
            user.save()

            # Send activation email
            current_site = get_current_site(request)
            mail_subject = 'Activate your account'
            message = render_to_string('users/activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            send_mail(mail_subject, message, 'team.dnoizer@gmail.com', [user.email])
            
            return render(request, 'users/registration_complete.html')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})






def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated! You can now log in.')
        return redirect('login') 
    else:
        return HttpResponse('Activation link is invalid!')




# def activate(request, uidb64, token):
#     try:
#         uid = force_str(urlsafe_base64_decode(uidb64))
#         user = CustomUser.objects.get(pk=uid)
#     except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
#         user = None

#     if user is not None and account_activation_token.check_token(user, token):
#         user.is_active = True
#         user.save()
#         login(request, user)
#         return HttpResponse('Thank you for confirming your email. You can now log in.')
#     else:
#         return HttpResponse('Activation link is invalid!')


# def register(request):
#     if request.method == 'POST':
#         form = CustomUserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save()  # Save the user to the database
#             login(request, user)  # Log in the user after registration
#             messages.success(request, "Registration successful!")
#             return redirect('home')  # Redirect to home or any other page
#         else:
#             messages.error(request, "There was an error with your registration.")
#     else:
#         form = CustomUserCreationForm()
    
#     return render(request, 'users/register.html', {'form': form})

# python manage.py changepassword admin@test1
