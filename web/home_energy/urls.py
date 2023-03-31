from django.urls import path

from . import views

app_name = 'home-energy'
urlpatterns = [
    # ex: /home-energy/
    path('', views.usage, name='usage'),
    # ex: /home-energy/usage.html
    path('usage.html', views.usage, name='usage'),

    # ex: /home-energy/latest_usage
    # ex: /home-energy/latest_usage/
    path('latest_usage', views.latest_usage, name='latest_usage'),
    path('latest_usage/', views.latest_usage, name='latest_usage'),

    # ex: /home-energy/detailed_usage
    # ex: /home-energy/detailed_usage/
    path('detailed_usage', views.detailed_usage, name='detailed_usage'),
    path('detailed_usage/', views.detailed_usage, name='detailed_usage'),

    # ex: /home-energy/total_usage
    # ex: /home-energy/total_usage
    path('total_usage', views.total_usage, name='total_usage'),
    path('total_usage/', views.total_usage, name='total_usage'),

    # ex: /home-energy/total_cost
    # ex: /home-energy/total_cost
    path('total_cost', views.total_cost, name='total_cost'),
    path('total_cost/', views.total_cost, name='total_cost'),

    # ex: /home-energy/prices.html
    path('prices.html', views.prices, name='prices'),

    # ex: /home-energy/get_all_prices
    # ex: /home-energy/get_all_prices/
    path('get_all_prices', views.get_all_prices, name='get_all_prices'),

    path('add_price', views.add_price, name='add_price'),
    path('modify_price', views.modify_price, name='modify_price'),
    path('remove_price', views.remove_price, name='remove_price'),

    # ex: /home-energy/debug/p1-reader.html
    path('debug/p1-reader.html', views.debug_p1_reader, name='debug_p1_reader'),
]
