
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
]



    # path('login/', views.login, name='login'),  
    # path('logout/', views.logout, name='logout'), 

# {% extends 'base.html' %}

# {% block content %}
# <h2>User Login</h2>
#     <form method="post">
#         {% csrf_token %}
#         {{ form.email.label }} {{ form.email }}<br>
#         {{ form.password.label }} {{ form.password }}<br>
#         <button type="submit">Login</button>
#     </form>
#     <p>Don't have an account? <a href="{% url 'register' %}">Register here</a>.</p>
# {% endblock content%}






