from django.urls import path

from . import views

app_name = 'home-vent'
urlpatterns = [
    # ex: /home-vent/
    # ex: /home-vent/main.html
    path('', views.main, name='main'),
    path('main.html', views.main, name='main'),

    # ex: /home-vent/get/<field>
    path('get/<str:field>', views.get, name='get'),

    # ex: /home-vent/getAll
    # ex: /home-vent/getAll/
    path('getAll', views.getAll, name='getAll'),
    path('getAll/', views.getAll, name='getAll'),

    # ex: /home-vent/action/<action>
    path('action/<str:action>', views.action, name='action')
]
