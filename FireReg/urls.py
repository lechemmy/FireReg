"""
URL configuration for FireReg project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponseRedirect

class CustomLogoutView(LogoutView):
    """
    Custom LogoutView that handles both GET and POST requests.
    This ensures users are properly logged out regardless of request method.
    """
    http_method_names = ['get', 'post', 'options']
    def get(self, request, *args, **kwargs):
        """Handle GET requests by logging out the user and redirecting."""
        auth_logout(request)
        redirect_to = self.get_success_url()
        if redirect_to != request.get_full_path():
            # Redirect to target page once the session has been cleared.
            return HttpResponseRedirect(redirect_to)
        return super().get(request, *args, **kwargs)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Custom logout view that properly handles GET requests
    path('accounts/logout/', CustomLogoutView.as_view(), name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('register.urls')),
]
