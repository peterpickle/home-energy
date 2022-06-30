from django.urls import path

from . import views

app_name = 'home-heating'
urlpatterns = [
    # ex: /home-heating/
    path('', views.ebus, name='ebus'),

    # ex: /home-heating/ebus
    # ex: /home-heating/ebus/
    path('ebus', views.ebus, name='ebus'),
    path('ebus/', views.ebus, name='ebus'),
]
