from django.urls import path

from . import views

app_name = 'home-energy'
urlpatterns = [
    # ex: /home-energy/
    path('', views.usage, name='usage'),
    # ex: /home-energy/usage.html
    path('usage.html', views.usage, name='usage'),
    # ex: /home-energy/latest
    path('latest', views.latest, name='latest'),
    # ex: /home-energy/details
    path('details', views.details, name='details'),

    # ex: /home-energy/debug/p1-reader.html
    path('debug/p1-reader.html', views.debug_p1_reader, name='debug_p1_reader'),
]
    
