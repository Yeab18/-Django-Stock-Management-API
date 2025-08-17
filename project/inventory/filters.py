import django_filters
from django.db.models import Q
from .models import Product, StockLog


class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    sku = django_filters.CharFilter(lookup_expr='iexact')
    category = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    supplier = django_filters.CharFilter(field_name='supplier__name', lookup_expr='icontains')
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    quantity_min = django_filters.NumberFilter(field_name='quantity', lookup_expr='gte')
    quantity_max = django_filters.NumberFilter(field_name='quantity', lookup_expr='lte')
    low_stock = django_filters.BooleanFilter(method='filter_low_stock')
    out_of_stock = django_filters.BooleanFilter(method='filter_out_of_stock')
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'category', 'supplier', 'price_min', 'price_max',
            'quantity_min', 'quantity_max', 'low_stock', 'out_of_stock', 'is_active'
        ]

    def filter_low_stock(self, queryset, name, value):
        if value:
            return queryset.filter(quantity__lte=models.F('min_stock_level'))
        return queryset

    def filter_out_of_stock(self, queryset, name, value):
        if value:
            return queryset.filter(quantity=0)
        return queryset


class StockLogFilter(django_filters.FilterSet):
    product = django_filters.CharFilter(field_name='product__name', lookup_expr='icontains')
    product_sku = django_filters.CharFilter(field_name='product__sku', lookup_expr='iexact')
    action = django_filters.ChoiceFilter(choices=StockLog.ACTION_CHOICES)
    user = django_filters.CharFilter(field_name='user__username', lookup_expr='icontains')
    date_from = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    quantity_change_positive = django_filters.BooleanFilter(method='filter_quantity_change_positive')

    class Meta:
        model = StockLog
        fields = ['product', 'product_sku', 'action', 'user', 'date_from', 'date_to', 'quantity_change_positive']

    def filter_quantity_change_positive(self, queryset, name, value):
        if value is True:
            return queryset.filter(quantity_change__gt=0)
        elif value is False:
            return queryset.filter(quantity_change__lt=0)
        return queryset