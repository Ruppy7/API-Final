from rest_framework import serializers
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils.text import slugify
from .models import Category, MenuItem, Cart, Order, OrderItem


class CategorySerializer (serializers.ModelSerializer):
    slug = serializers.SerializerMethodField(method_name='get_slug', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'title', 'slug']

    def get_slug(self, category):
        return slugify(category.title)


class MenuItemSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all()
    )
    # category = CategorySerializer(read_only=True)
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'category', 'featured']


class CartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    def validate(self, attrs):
        attrs['unit_price'] = attrs['menuitem'].price
        attrs['price'] = attrs['unit_price'] * attrs['quantity']
        return attrs

    class Meta:
        model = Cart
        fields = ['user', 'menuitem', 'unit_price', 'quantity', 'price']
        extra_kwargs = {
            'price': {'read_only': True},
            'unit_price': {'read_only': True}
        }


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['order', 'menuitem', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):

    orderitem = OrderItemSerializer(many=True, read_only=True, source='order')

    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew',
                  'status', 'date', 'total', 'orderitem']


class UserSerilializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','email']