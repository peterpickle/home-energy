from django.urls import path

from . import views

app_name = 'home-heating'
urlpatterns = [
    # ex: /home-heating/
    path('', views.debug_ebus, name='debug_ebus'),

    # ex: /home-heating/debug/ebus
    # ex: /home-heating/debug/ebus/
    path('debug/ebus', views.debug_ebus, name='debug_ebus'),
    path('debug/ebus/', views.debug_ebus, name='debug_ebus'),
]
