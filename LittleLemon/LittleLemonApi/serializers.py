from rest_framework import serializers
from .models import Category, MenuItem, Cart, Order, OrderItem
from django.contrib.auth.models import User


class CategorySeralizer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']
        
class MenuItemSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset = Category.objects.all()
    ) 
    #category = CategorySeralizer(read_only=True)
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price','category','featured']
        
class CartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset = User.objects.all(),
        default = serializers.CurrentUserDefault(),
    )
    def validate(self, attrs):
        menuitem = attrs.get('menuitem')
        quantity = attrs.get('quantity')
        if menuitem and quantity:
            attrs['unit_price'] = menuitem.price
            attrs['price'] = menuitem.price * quantity
        return attrs
    
    class Meta:
        model = Cart
        fields = ['user', 'menuitem','unit_price','quantity','price']
        extra_kwargs = {
            'price' : {'read_only' : True},
            'unit_price' : {'read_only' : True},
        }
    
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['order', 'menuitem', 'quantity', 'price']

    
class OrderSerializer(serializers.ModelSerializer):
    orderitem = OrderItemSerializer(many = True, read_only=True, source='order')
    class Meta:
        model = Order
        fields = ['id' ,'user','delivery_crew','status','date','total','orderitem']
    