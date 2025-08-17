from django.urls import path
from . import views

urlpatterns = [
    # User Management
    path('users/', views.UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    
    # Category Management
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    
    # Supplier Management
    path('suppliers/', views.SupplierListCreateView.as_view(), name='supplier-list-create'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier-detail'),
    
    # Product Management
    path('products/', views.ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    
    # Stock Management
    path('stock-logs/', views.StockLogListView.as_view(), name='stock-log-list'),
    path('products/<int:product_id>/stock-logs/', views.ProductStockLogView.as_view(), name='product-stock-logs'),
    path('products/<int:product_id>/update-stock/', views.update_product_stock, name='update-product-stock'),
    
    # Reports & Analytics
    path('reports/inventory/', views.inventory_report, name='inventory-report'),
    path('reports/low-stock/', views.low_stock_products, name='low-stock-products'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
]