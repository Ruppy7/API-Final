from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import Group, User
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import CategorySerializer, MenuItemSerializer, CartSerializer, OrderSerializer, UserSerilializer

class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    search_fields = ['category__title']
    ordering_fields = ['price']
    permission_classes = [IsAuthenticated]
    
class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticated]

class CartView(generics.ListCreateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        
    
    def delete(self, request, *args, **kwargs):
        self.get_queryset().delete()
        return Response("Deleted")

class OrderView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.queryset.all()
        elif user.groups.count() == 0:  # normal customer - no group
            return self.queryset.filter(user=user)
        elif user.groups.filter(name='Delivery Crew').exists():  # delivery crew
            return self.queryset.filter(delivery_crew=user)  # only show orders assigned to him
        else:  # delivery crew or manager
            return self.queryset.all()

    def create(self, request, *args, **kwargs):
        menuitem_count = Cart.objects.filter(user=request.user).count()
        if menuitem_count == 0:
            return Response({"message": "no item in cart"})

        data = request.data.copy()
        total = self.get_total_price(request.user)
        data['total'] = total
        data['user'] = request.user.id
        order_serializer = OrderSerializer(data=data)
        if order_serializer.is_valid(raise_exception=True):
            order = order_serializer.save()

            items = Cart.objects.filter(user=request.user).values()

            for item in items:
                orderitem = OrderItem(
                    order=order,
                    menuitem_id=item['menuitem_id'],
                    price=item['price'],
                    quantity=item['quantity'],
                )
                orderitem.save()

            Cart.objects.filter(user=request.user).delete()  # Delete cart items

            result = order_serializer.data.copy()
            result['total'] = total
            return Response(result)

    def get_total_price(self, user):
        items = Cart.objects.filter(user=user).values()
        return sum(item['price'] for item in items)

class SingleOrderView(generics.RetrieveUpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user = self.request.user
        if user.groups.count() == 0:  # Normal user, not belonging to any group = Customer
            return Response('Not Authorized')
        else:  # everyone else - Super Admin, Manager, and Delivery Crew
            return super().update(request, *args, **kwargs)

class GroupViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    def list(self, request):
        managers = Group.objects.filter(name='Manager')
        users = User.objects.filter(groups__in=managers)
        items = UserSerilializer(users, many=True)
        return Response(items.data)

    def create(self, request):
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)
        managers = Group.objects.get(name='Manager')
        managers.user_set.add(user)
        return Response({"message": "user added to the manager group"}, status.HTTP_200_OK)

    def destroy(self, request):
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)
        managers = Group.objects.get(name='Manager')
        managers.user_set.remove(user)
        return Response({"message": "user removed from the manager group"}, status.HTTP_200_OK)

class DeliveryCrewViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        delivery_crew = Group.objects.filter(name='Delivery Crew')
        users = User.objects.filter(groups__in=delivery_crew)
        items = UserSerilializer(users, many=True)
        return Response(items.data)

    def create(self, request):
        if not self.request.user.is_superuser and not self.request.user.groups.filter(name='Manager').exists():
            return Response({"message": "forbidden"}, status.HTTP_403_FORBIDDEN)

        username = request.data.get('username')
        user = get_object_or_404(User, username=username)
        dc = Group.objects.get(name='Delivery Crew')
        dc.user_set.add(user)
        return Response({"message": "user added to the delivery crew group"}, status.HTTP_200_OK)

    def destroy(self, request):
        if not self.request.user.is_superuser and not self.request.user.groups.filter(name='Manager').exists():
            return Response({"message": "forbidden"}, status.HTTP_403_FORBIDDEN)

        username = request.data.get('username')
        user = get_object_or_404(User, username=username)
        dc = Group.objects.get(name='Delivery Crew')
        dc.user_set.remove(user)
        return Response({"message": "user removed from the delivery crew group"}, status.HTTP_200_OK)
