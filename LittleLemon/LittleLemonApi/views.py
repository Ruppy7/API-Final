from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest
from django.contrib.auth.models import Group, User
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import ManagerListSerializer, CategorySerializer, MenuItemSerializer, CartSerializer, CartAddSerializer, CartRemoveSerializer,SingleOrderSerializer, OrderSerializer, OrderInsertSerializer
from .permissions import IsManager, IsDeliveryCrew
from datetime import date
import math

class CategoriesView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

class MenuItemsView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    search_fields = ['title','category__title']
    ordering_fields = ['price', 'category']
    
    def get_permissions(self):
        permission_classes = []
        if self.request.method != "GET":
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]
    
class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    
    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        if self.request.method == "PATCH":
            permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
        if self.request.method == "DELETE":
            permission_classes = [IsAuthenticated, IsAdminUser]
        return[permission() for permission in permission_classes]

    def patch(self, request, *args, **kwargs):
        menuitem = MenuItem.objects.get(pk=self.kwargs['pk'])
        menuitem.featured = not menuitem.featured
        menuitem.save()
        return Response({'message': f'Status of {str(menuitem.title)} changed to {str(menuitem.featured)}'}, status.HTTP_200_OK)

class ManagersView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = User.objects.filter(groups__name='Managers')
    serializer_class = ManagerListSerializer
    permission_classes = [IsAuthenticated, IsManager | IsAdminUser]

    def post(self, request, *args, **kwargs):
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            managers = Group.objects.get(name='Managers')
            managers.user_set.add(user)
            return Response({'message':'User added to Managers'}, status.HTTP_201_CREATED) 

class ManagersRemoveView(generics.DestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = ManagerListSerializer
    permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
    queryset = User.objects.filter(groups__name='Managers')

    def delete(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        user = get_object_or_404(User, pk=pk)
        managers = Group.objects.get(name='Managers')
        managers.user_set.remove(user)
        return Response({'message':'User removed Managers'}, status.HTTP_200_OK)

class DeliveryCrewView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = User.objects.filter(groups__name='Delivery crew')
    serializer_class = ManagerListSerializer
    permission_classes = [IsAuthenticated, IsManager | IsAdminUser]

    def post(self, request, *args, **kwargs):
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            crew = Group.objects.get(name='Delivery crew')
            crew.user_set.add(user)
            return Response({'message':'User added to Delivery Crew'}, status.HTTP_201_CREATED)

class DeliveryCrewRemoveView(generics.DestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = ManagerListSerializer
    permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
    queryset = User.objects.filter(groups__name='Delivery crew')

    def delete(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        user = get_object_or_404(User, pk=pk)
        managers = Group.objects.get(name='Delivery crew')
        managers.user_set.remove(user)
        return Response({'message':'User removed from the Delivery crew'}, status.HTTP_200_OK)

class CartView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        serialized_item = CartAddSerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        id = request.data['menuitem']
        quantity = request.data['quantity']
        item = get_object_or_404(MenuItem, id=id)
        price = int(quantity) * item.price
        try:
            Cart.objects.create(user=request.user, quantity=quantity, unit_price=item.price, price=price, menuitem_id=id)
        except:
            return Response({'message':'Item already in cart'}, status.HTTP_409_CONFLICT)
        return Response({'message':'Item added to cart!'}, status.HTTP_201_CREATED)
    
    def delete(self, request, *args, **kwargs):
        if request.data['menuitem']:
           serialized_item = CartRemoveSerializer(data=request.data)
           serialized_item.is_valid(raise_exception=True)
           menuitem = request.data['menuitem']
           cart = get_object_or_404(Cart, user=request.user, menuitem=menuitem )
           cart.delete()
           return Response({'message':'Item removed from cart'}, status.HTTP_200_OK)
        else:
            Cart.objects.filter(user=request.user).delete()
            return Response({'message':'All Items removed from cart'}, status.HTTP_200_OK)

class OrderView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.groups.filter(name="Managers").exists():
            return Order.objects.all()
        elif user.groups.filter(name='Delivery Crew').exists():  # delivery crew
            return Order.objects.filter(delivery_crew = user)  # only show orders assigned to him
        else:
            return Order.objects.filter(user=user)

    def get_permissions(self):
        if self.request.method == "GET" or "POST":
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def post(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user=request.user)
        value_list=cart.values_list()
        if len(value_list) == 0:
            return HttpResponseBadRequest()
        total = math.fsum([float(value[-1]) for value in value_list])
        order = Order.objects.create(user=request.user, status=False, total=total, date=date.today())
        for i in cart.values():
            menuitem = get_object_or_404(MenuItem, id=i['menuitem_id'])
            orderitem = OrderItem.objects.create(order=order, menuitem=menuitem, quantity=i['quantity'])
            orderitem.save()
        cart.delete()
        return Response({'message':f'Your order has been placed. Your id is {str(order.id)}'}, status.HTTP_201_CREATED)

class SingleOrderView(generics.RetrieveUpdateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = SingleOrderSerializer
    
    def get_permissions(self):
        user = self.request.user
        method = self.request.method
        order = Order.objects.get(pk=self.kwargs['pk'])
        if user == order.user and method == 'GET':
            permission_classes = [IsAuthenticated]
        elif method == 'PUT' or method == 'DELETE':
            permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
        else:
            permission_classes = [IsAuthenticated, IsDeliveryCrew | IsManager | IsAdminUser]
        return[permission() for permission in permission_classes] 

    def get_queryset(self, *args, **kwargs):
            query = OrderItem.objects.filter(order_id=self.kwargs['pk'])
            return query


    def patch(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs['pk'])
        order.status = not order.status
        order.save()
        return Response({'message':'Status of order #'+ str(order.id)+' changed to '+str(order.status)}, status.HTTP_201_CREATED)

    def put(self, request, *args, **kwargs):
        serialized_item = OrderInsertSerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        order_pk = self.kwargs['pk']
        crew_pk = request.data['delivery_crew'] 
        order = get_object_or_404(Order, pk=order_pk)
        crew = get_object_or_404(User, pk=crew_pk)
        order.delivery_crew = crew
        order.save()
        return Response({'message':str(crew.username)+' was assigned to order #'+str(order.id)}, status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs['pk'])
        order_number = str(order.id)
        order.delete()
        return Response({'message':f'Order #{order_number} was deleted'}, status.HTTP_200_OK)
