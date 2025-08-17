from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta

from .models import Product, Category, Supplier, StockLog
from .serializers import (
    UserSerializer, ProductSerializer, CategorySerializer, 
    SupplierSerializer, StockLogSerializer, StockUpdateSerializer,
    InventoryReportSerializer
)
from .permissions import RoleBasedPermission, IsAdminOrReadOnly, StockLogPermission
from .filters import ProductFilter, StockLogFilter

User = get_user_model()


# User Management Views
class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['role', 'is_active']
    search_fields = ['username', 'email']
    ordering_fields = ['username', 'email', 'created_at']
    ordering = ['username']


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]


# Category Management Views
class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [RoleBasedPermission]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [RoleBasedPermission]


# Supplier Management Views
class SupplierListCreateView(generics.ListCreateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [RoleBasedPermission]
    search_fields = ['name', 'contact_person', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [RoleBasedPermission]


# Product Management Views
class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.select_related('category', 'supplier', 'created_by', 'last_modified_by')
    serializer_class = ProductSerializer
    permission_classes = [RoleBasedPermission]
    filterset_class = ProductFilter
    search_fields = ['name', 'sku', 'description']
    ordering_fields = ['name', 'sku', 'quantity', 'price', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            last_modified_by=self.request.user
        )


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related('category', 'supplier', 'created_by', 'last_modified_by')
    serializer_class = ProductSerializer
    permission_classes = [RoleBasedPermission]

    def perform_update(self, serializer):
        serializer.save(last_modified_by=self.request.user)


# Stock Management Views
class StockLogListView(generics.ListAPIView):
    queryset = StockLog.objects.select_related('product', 'user')
    serializer_class = StockLogSerializer
    permission_classes = [StockLogPermission]
    filterset_class = StockLogFilter
    search_fields = ['product__name', 'product__sku', 'reason', 'reference_number']
    ordering_fields = ['timestamp', 'product__name', 'quantity_change']
    ordering = ['-timestamp']


class ProductStockLogView(generics.ListAPIView):
    serializer_class = StockLogSerializer
    permission_classes = [StockLogPermission]
    filterset_class = StockLogFilter
    ordering = ['-timestamp']

    def get_queryset(self):
        product_id = self.kwargs['product_id']
        return StockLog.objects.filter(product_id=product_id).select_related('product', 'user')


@api_view(['POST'])
@permission_classes([RoleBasedPermission])
def update_product_stock(request, product_id):
    """
    Update product stock with automatic logging
    """
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found or inactive'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = StockUpdateSerializer(data=request.data)
    if serializer.is_valid():
        try:
            updated_product, stock_log = serializer.update_stock(
                product, serializer.validated_data, request.user
            )
            
            return Response({
                'message': 'Stock updated successfully',
                'product': ProductSerializer(updated_product).data,
                'stock_log': StockLogSerializer(stock_log).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([RoleBasedPermission])
def low_stock_products(request):
    """
    Get products with low stock levels
    """
    low_stock_products = Product.objects.filter(
        is_active=True,
        quantity__lte=F('min_stock_level')
    ).select_related('category', 'supplier').order_by('quantity')
    
    serializer = ProductSerializer(low_stock_products, many=True)
    return Response({
        'count': low_stock_products.count(),
        'products': serializer.data
    })


@api_view(['GET'])
@permission_classes([RoleBasedPermission])
def inventory_report(request):
    """
    Generate comprehensive inventory report
    """
    # Filter parameters
    category = request.GET.get('category')
    supplier = request.GET.get('supplier')
    
    # Base queryset
    products_queryset = Product.objects.all()
    if category:
        products_queryset = products_queryset.filter(category__name__icontains=category)
    if supplier:
        products_queryset = products_queryset.filter(supplier__name__icontains=supplier)

    # Calculate metrics
    total_products = products_queryset.count()
    active_products = products_queryset.filter(is_active=True).count()
    inactive_products = total_products - active_products
    
    # Stock analysis
    active_products_qs = products_queryset.filter(is_active=True)
    low_stock_products = active_products_qs.filter(quantity__lte=F('min_stock_level')).count()
    out_of_stock_products = active_products_qs.filter(quantity=0).count()
    
    # Financial metrics
    stock_value_data = active_products_qs.aggregate(
        total_value=Sum(F('quantity') * F('price'), default=0),
        total_quantity=Sum('quantity', default=0)
    )
    
    # Category and supplier counts
    categories_count = Category.objects.count()
    suppliers_count = Supplier.objects.count()
    
    # Recent stock changes (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_changes = StockLog.objects.filter(timestamp__gte=week_ago).count()

    report_data = {
        'total_products': total_products,
        'active_products': active_products,
        'inactive_products': inactive_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'total_stock_value': stock_value_data['total_value'] or 0,
        'total_quantity': stock_value_data['total_quantity'] or 0,
        'categories_count': categories_count,
        'suppliers_count': suppliers_count,
        'recent_stock_changes': recent_changes,
    }
    
    serializer = InventoryReportSerializer(data=report_data)
    serializer.is_valid()
    
    return Response({
        'report': serializer.data,
        'generated_at': timezone.now(),
        'filters': {
            'category': category,
            'supplier': supplier
        }
    })


@api_view(['GET'])
@permission_classes([RoleBasedPermission])
def dashboard_stats(request):
    """
    Get key dashboard statistics
    """
    # Quick stats
    total_products = Product.objects.filter(is_active=True).count()
    low_stock_count = Product.objects.filter(
        is_active=True, 
        quantity__lte=F('min_stock_level')
    ).count()
    out_of_stock_count = Product.objects.filter(is_active=True, quantity=0).count()
    
    # Total inventory value
    inventory_value = Product.objects.filter(is_active=True).aggregate(
        total=Sum(F('quantity') * F('price'), default=0)
    )['total']
    
    # Recent activity (last 24 hours)
    yesterday = timezone.now() - timedelta(days=1)
    recent_stock_movements = StockLog.objects.filter(timestamp__gte=yesterday).count()
    
    # Top categories by product count
    top_categories = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).order_by('-product_count')[:5]
    
    return Response({
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'inventory_value': inventory_value,
        'recent_stock_movements': recent_stock_movements,
        'top_categories': [
            {'name': cat.name, 'product_count': cat.product_count} 
            for cat in top_categories
        ],
        'timestamp': timezone.now()
    })