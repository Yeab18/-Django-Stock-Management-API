from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from decimal import Decimal


class User(AbstractUser):
    """
    Custom User model with role-based access control
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('viewer', 'Viewer'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='viewer')
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_staff_member(self):
        return self.role in ['admin', 'staff']

    @property
    def can_write(self):
        return self.role in ['admin', 'staff']


class Category(models.Model):
    """
    Product categories for better organization
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Supplier(models.Model):
    """
    Supplier information for products
    """
    name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Product model with comprehensive inventory tracking
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, unique=True, help_text="Stock Keeping Unit")
    quantity = models.IntegerField(
        validators=[MinValueValidator(0)], 
        default=0,
        help_text="Current stock quantity"
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price per unit"
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='products'
    )
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='products'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_products'
    )
    last_modified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='modified_products'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields for better inventory management
    min_stock_level = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        help_text="Minimum stock level before low stock alert"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['category']),
            models.Index(fields=['supplier']),
            models.Index(fields=['quantity']),
        ]

    def __str__(self):
        return f"{self.name} (SKU: {self.sku})"

    @property
    def is_low_stock(self):
        """Check if product is below minimum stock level"""
        return self.quantity <= self.min_stock_level

    @property
    def stock_value(self):
        """Calculate total value of current stock"""
        return self.quantity * self.price

    def save(self, *args, **kwargs):
        """Override save to ensure SKU is uppercase"""
        self.sku = self.sku.upper()
        super().save(*args, **kwargs)


class StockLog(models.Model):
    """
    Log all stock movements for audit trail
    """
    ACTION_CHOICES = [
        ('restock', 'Restock'),
        ('sale', 'Sale'),
        ('adjustment', 'Stock Adjustment'),
        ('return', 'Return'),
        ('damage', 'Damage/Loss'),
        ('transfer', 'Transfer'),
    ]

    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        related_name='stock_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    quantity_change = models.IntegerField(
        help_text="Positive for stock increase, negative for decrease"
    )
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    reason = models.TextField(blank=True, help_text="Reason for stock change")
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='stock_changes'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Additional metadata
    reference_number = models.CharField(max_length=100, blank=True)
    unit_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Cost per unit for this transaction"
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['product', '-timestamp']),
            models.Index(fields=['action']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.get_action_display()} ({self.quantity_change:+d})"

    @property
    def total_value(self):
        """Calculate total value of this stock movement"""
        if self.unit_cost:
            return abs(self.quantity_change) * self.unit_cost
        return abs(self.quantity_change) * self.product.price