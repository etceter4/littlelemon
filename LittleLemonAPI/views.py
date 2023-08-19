from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import FoodItem, Order, Category, Cart, CartItem
from .serializers import FoodItemSerializer, OrderSerializer, CategorySerializer, UserRegistrationSerializer, CartItemSerializer
from .permissions import IsManager, IsDeliveryCrew
from rest_framework.exceptions import PermissionDenied
from rest_framework import filters
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.contrib.auth import authenticate


class FoodItemViewSet(viewsets.ModelViewSet):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['category__name']

    def get_queryset(self):
        return FoodItem.objects.all()

    def perform_update(self, serializer):
        if 'is_item_of_the_day' in self.request.data:
            if not IsManager().has_permission(self.request, self):
                raise PermissionDenied("Only managers can update the item of the day.")
        serializer.save()


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='DeliveryCrew').exists():
            return Order.objects.filter(delivery_crew_member=user)
        elif user.groups.filter(name='Customer').exists():
            return Order.objects.filter(customer_name=user.username)
        return Order.objects.none()

    def perform_update(self, serializer):
        # Only allow managers to assign orders to delivery crew members
        if 'delivery_crew_member' in self.request.data:
            if not IsManager().has_permission(self.request, self):
                raise PermissionDenied("Only managers can assign orders to the delivery crew.")
        
        # Only allow delivery crew to mark orders as delivered
        if 'delivered' in self.request.data:
            if not IsDeliveryCrew().has_permission(self.request, self):
                raise PermissionDenied("Only delivery crew can mark orders as delivered.")
        
        serializer.save()

    @action(detail=True, methods=['POST'], permission_classes=[IsDeliveryCrew], url_path='mark-delivered')
    def mark_as_delivered(self, request, pk=None):
        order = self.get_object()

        # Check if the order is assigned to the current user (delivery crew member)
        if order.delivery_crew_member != request.user:
            return Response({"detail": "Order not assigned to you."}, status=status.HTTP_403_FORBIDDEN)

        order.delivery_status = 'Delivered'
        order.save()
        return Response({"message": f"Order {order.id} marked as delivered."}, status=status.HTTP_200_OK)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if not request.user.is_staff or not request.user.is_superuser:
            return Response({"detail": "Only admin users can create categories."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

@api_view(['POST',])
def registration_view(request):
    if request.method == 'POST':
        serializer = UserRegistrationSerializer(data=request.data)
        data = {}
        if serializer.is_valid():
            user = serializer.save()
            data['response'] = 'successfully registered a new user.'
            data['username'] = user.username
        else:
            data = serializer.errors
        return Response(data)

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    def create(self, request, *args, **kwargs):
        response = super(UserRegistrationView, self).create(request, *args, **kwargs)
        return Response({
            "message": "User registered successfully",
            "data": response.data
        }, status=status.HTTP_201_CREATED)
    
class UserManagerViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [IsAuthenticated, IsManager]

    @action(detail=True, methods=['post'], url_path='assign-to-delivery-crew')
    def assign_to_delivery_crew(self, request, pk=None):
        user = self.get_object()
        delivery_crew_group, _ = Group.objects.get_or_create(name='DeliveryCrew')
        user.groups.add(delivery_crew_group)
        user.save()
        return Response({"message": f"{user.username} has been added to the delivery crew."}, status=status.HTTP_200_OK)

    
@api_view(['POST'])
def assign_user_to_manager(request):
    if request.user.is_staff:
        username = request.data.get('username')
        user = User.objects.get(username=username)
        manager_group, created = Group.objects.get_or_create(name='Manager')
        user.groups.add(manager_group)
        user.save()
        return Response({"message": f"User {username} added to Manager group."}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Only admins can assign users to the Manager group."}, status=status.HTTP_403_FORBIDDEN)

@api_view(['POST'])
@permission_classes([IsManager])
def assign_to_delivery_crew(request):
    user_id = request.data.get("user_id")
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=400)

    delivery_crew_group, created = Group.objects.get_or_create(name="DeliveryCrew")
    user.groups.add(delivery_crew_group)
    return Response({"message": f"{user.username} has been assigned to the delivery crew."})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_item_to_cart(request):
    # Check if user has a cart, if not create one
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Get the food item
    food_item_id = request.data.get('food_item_id')
    try:
        food_item = FoodItem.objects.get(id=food_item_id)
    except FoodItem.DoesNotExist:
        return Response({"error": "Food item not found."}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if item already exists in cart, if yes update quantity, else create new cart item
    cart_item, created = CartItem.objects.get_or_create(cart=cart, food_item=food_item)
    if not created:
        cart_item.quantity += 1
    cart_item.save()

    return Response({"message": f"Added {food_item.name} to cart."}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart_items(request):
    try:
        cart = request.user.cart
        cart_items = cart.cart_items.all()
        serializer = CartItemSerializer(cart_items, many=True)
        return Response(serializer.data)
    except Cart.DoesNotExist:
        return Response({"detail": "Cart not found."}, status=404)
    
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({"error": "Invalid credentials"}, status=400)

class PlaceOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        cart_items = cart.cart_items.all()
        if not cart_items:
            return Response({"error": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)
        for cart_item in cart_items:
            Order.objects.create(
                customer_name=request.user.username,
                food_item=cart_item.food_item,
                delivery_status='Pending'
            )
        cart.cart_items.clear()
        return Response({"message": "Order placed successfully."}, status=status.HTTP_200_OK)

class CustomerOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(customer_name=request.user.username)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

