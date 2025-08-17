from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import Product, Category, Supplier, StockLog

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'password', 'is_active', 'created_at')
        extra_kwargs = {
            'password': {'write_only': True},
            'created_at': {'read_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'products_count', 'created_at')
        read_only_fields = ('created_at',)

    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()


class SupplierSerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Supplier
        fields = (
            'id', 'name', 'contact_person', 'email', 'phone', 
            'address', 'products_count', 'created_at'
        )
        read_only_fields = ('created_at',)

    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    last_modified_by_username = serializers.CharField(source='last_modified_by.username', read_only=True)
    stock_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'sku', 'quantity', 'price',
            'category', 'category_name', 'supplier', 'supplier_name',
            'min_stock_level', 'is_active', 'stock_value', 'is_low_stock',
            'created_by', 'created_by_username', 'last_modified_by', 
            'last_modified_by_username', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'created_by', 'last_modified_by', 'created_at', 'updated_at',
            'stock_value', 'is_low_stock'
        )

    def validate_sku(self, value):
        """Ensure SKU is unique and properly formatted"""
        value = value.upper().strip()
        if not value:
            raise serializers.ValidationError("SKU cannot be empty")
        return value

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value


class StockLogSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = StockLog
        fields = (
            'id', 'product', 'product_name', 'product_sku', 'action', 'action_display',
            'quantity_change', 'previous_quantity', 'new_quantity', 'reason',
            'user', 'user_username', 'timestamp', 'reference_number', 
            'unit_cost', 'total_value'
        )
        read_only_fields = ('timestamp', 'total_value')


class StockUpdateSerializer(serializers.Serializer):
    """
    Serializer for stock updates with automatic logging
    """
    ACTION_CHOICES = [
        ('restock', 'Restock'),
        ('sale', 'Sale'),
        ('adjustment', 'Stock Adjustment'),
        ('return', 'Return'),
        ('damage', 'Damage/Loss'),
        ('transfer', 'Transfer'),
    ]

    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    quantity_change = serializers.IntegerField()
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    reference_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    def validate_quantity_change(self, value):
        if value == 0:
            raise serializers.ValidationError("Quantity change cannot be zero")
        return value

    def update_stock(self, product, validated_data, user):
        """
        Update product stock and create log entry
        """
        with transaction.atomic():
            previous_quantity = product.quantity
            quantity_change = validated_data['quantity_change']
            new_quantity = previous_quantity + quantity_change

            if new_quantity < 0:
                raise serializers.ValidationError(
                    f"Cannot reduce stock below 0. Current stock: {previous_quantity}, "
                    f"Requested change: {quantity_change}"
                )

            # Update product quantity
            product.quantity = new_quantity
            product.last_modified_by = user
            product.save(update_fields=['quantity', 'last_modified_by', 'updated_at'])

            # Create stock log entry
            stock_log = StockLog.objects.create(
                product=product,
                action=validated_data['action'],
                quantity_change=quantity_change,
                previous_quantity=previous_quantity,
                new_quantity=new_quantity,
                reason=validated_data.get('reason', ''),
                reference_number=validated_data.get('reference_number', ''),
                unit_cost=validated_data.get('unit_cost'),
                user=user
            )

            return product, stock_log


class InventoryReportSerializer(serializers.Serializer):
    """
    Serializer for inventory summary reports
    """
    total_products = serializers.IntegerField()
    active_products = serializers.IntegerField()
    inactive_products = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()
    out_of_stock_products = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_quantity = serializers.IntegerField()
    categories_count = serializers.IntegerField()
    suppliers_count = serializers.IntegerField()
    recent_stock_changes = serializers.IntegerField()