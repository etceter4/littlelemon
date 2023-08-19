from django.contrib import admin
from django.contrib.auth.models import User, Group
from .models import FoodItem, Order, Category
from django import forms

# Unregister the default User and Group admin classes
admin.site.unregister(User)
admin.site.unregister(Group)

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'is_item_of_the_day', 'category')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff',)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(OrderAdminForm, self).__init__(*args, **kwargs)
        delivery_crew_group, created = Group.objects.get_or_create(name='Delivery Crew')
        self.fields['delivery_crew_member'].queryset = User.objects.filter(groups=delivery_crew_group)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'food_item', 'delivery_status')
    form = OrderAdminForm
