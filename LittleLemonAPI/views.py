from django.contrib.auth.models import User, Group
from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import FoodItem, Order, Category, Cart, CartItem
from .serializers import FoodItemSerializer, OrderSerializer, CategorySerializer, UserRegistrationSerializer, CartItemSerializer
from .permissions import IsManager, IsDeliveryCrew
from rest_framework.exceptions import PermissionDenied


class FoodItemViewSet(viewsets.ModelViewSet):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthenticated]

    def perform_update(self, serializer):
        # Check if the `is_item_of_the_day` field is being updated
        if 'is_item_of_the_day' in self.request.data:
            # Ensure the user has manager permissions
            if not IsManager().has_permission(self.request, self):
                raise PermissionDenied("Only managers can update the item of the day.")
        serializer.save()

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='DeliveryCrew').exists():
            return Order.objects.filter(delivery_crew_member=user)
        elif user.groups.filter(name='Customer').exists():
            return Order.objects.filter(customer_name=user.username)
        return Order.objects.none()

    def perform_update(self, serializer):
        # Only allow managers or admins to assign orders to delivery crew members
        if 'delivery_crew_member' in self.request.data:
            if not (IsManager().has_permission(self.request, self) or self.request.user.is_staff):
                raise PermissionDenied("Only managers or admins can assign orders to delivery crew members.")
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
        # Only allow managers or admins to assign orders to delivery crew members
        if 'delivery_crew_member' in self.request.data:
            if not (IsManager().has_permission(self.request, self) or self.request.user.is_staff):
                raise PermissionDenied("Only managers or admins can assign orders to delivery crew members.")
        serializer.save()


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
