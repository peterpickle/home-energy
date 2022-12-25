from django.urls import path

from . import views

app_name = 'home-vent'
urlpatterns = [
    # ex: /home-vent/
    # ex: /home-vent/main.html
    path('', views.main, name='main'),
    path('main.html', views.main, name='main')
]
