from django.urls import path
from . import views

urlpatterns = [
    path('menu-items/', views.MenuItemsView),
    path('menu-items/<int:pk>/', views.SingleItemView),
    path('groups/manager/users/', views.manager),
    path('groups/manager/users/<int:pk>/', views.singlemanager),
    path('groups/delivery-crew/users/', views.deliverycrew),
    path('groups/delivery-crew/users/<int:pk>/',views.singledeliverycrew),
    path('cart/menu-items', views.cartview),
    path('orders/', views.orderview),
    path('orders/<int:pk>/', views.singleorderview),
]