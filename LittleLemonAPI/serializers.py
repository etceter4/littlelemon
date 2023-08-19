from rest_framework import serializers
from .models import FoodItem, Order, Cart, CartItem
from .models import Category
from django.contrib.auth.models import User

class FoodItemSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    class Meta:
        model = FoodItem
        fields = ('id', 'name', 'description', 'price', 'is_item_of_the_day', 'category')

class OrderSerializer(serializers.ModelSerializer): 
    class Meta:
        model = Order
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True},
        }
    
    def save(self):
        user = User(
            username=self.validated_data['username'],
        )
        password = self.validated_data['password']
        password2 = self.validated_data['password2']
        if password != password2:
            raise serializers.ValidationError({'password': 'Passwords must match.'})
        user.set_password(password)
        user.save()
        return user

class CartItemSerializer(serializers.ModelSerializer):
    food_item = FoodItemSerializer(read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['food_item', 'quantity']

class CartSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['user', 'created_at', 'cart_items']

class CartItemSerializer(serializers.ModelSerializer):
    food_item_name = serializers.ReadOnlyField(source='food_item.name')

    class Meta:
        model = CartItem
        fields = ('id', 'food_item_name', 'quantity')
