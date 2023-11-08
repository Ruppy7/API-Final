from django.urls import path
from . import views

urlpatterns = [
    path('menu-items', views.MenuItemsView.as_view()),
    path('menu-items/category', views.CategoriesView.as_view()),
    path('menu-items/<int:pk>', views.SingleMenuItemView.as_view()),
    path('groups/managers/users', views.ManagersView.as_view()),
    path('groups/managers/users/<int:pk>', views.ManagersRemoveView.as_view()),
    path('groups/delivery-crew/users', views.DeliveryCrewView.as_view()),
    path('groups/delivery-crew/users/<int:pk>', views.DeliveryCrewRemoveView.as_view()),
    path('cart/menu-items', views.CartView.as_view()),
    path('order', views.OrderView.as_view()),
    path('orders/<int:pk>', views.SingleOrderView.as_view()),
]