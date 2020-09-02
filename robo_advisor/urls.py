"""robo_advisor URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.conf.urls import url
from django.contrib import admin
from django.urls import path,include
from fastback  import views as fastback_views
from account import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('account/login/', views.login, name='login'),
    path('account/register/', views.register, name='register'),
    path('account/check/', views.check, name='check'),
    path('account/logout/', views.logout, name='logout'),

    path('form/', fastback_views.index),
    path('opt/', fastback_views.portfo_opt),

    path('automation/create/', fastback_views.copy_strat),
    path('automation/list/', fastback_views.user_portfolio_list),
    path('automation/index/', fastback_views.portfo_index),
    path('automation/save/', fastback_views.portfo_save),
    path('automation/delete/', fastback_views.portfo_delete),
    path('pay/', fastback_views.pay_money),
]
