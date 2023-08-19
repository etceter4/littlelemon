from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerOrdersView, FoodItemViewSet, OrderViewSet, CategoryViewSet, PlaceOrderView, registration_view, UserRegistrationView, assign_user_to_manager, assign_to_delivery_crew
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'food-items', FoodItemViewSet)
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'categories', CategoryViewSet)
router.register(r'fooditems', FoodItemViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('register/', registration_view, name='register'),
    path('user-register/', UserRegistrationView.as_view(), name='user-register'), # Changed the path to avoid conflict
    path('assign_manager/', assign_user_to_manager, name='assign-manager'),
    path('assign-to-delivery-crew/', assign_to_delivery_crew, name='assign-to-delivery-crew'),
    path('cart/add/', views.add_item_to_cart, name='add-item-to-cart'),
    path('cart/', views.get_cart_items, name='get-cart-items'),
    path('place_order/', PlaceOrderView.as_view(), name='place_order'),
    path('my_orders/', CustomerOrdersView.as_view(), name='my_orders'),


]
