#!/usr/bin/env python
"""
Script to populate the database with sample data
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_management.settings')
django.setup()

from inventory.models import User, Category, Supplier, Product, StockLog
from decimal import Decimal

def create_sample_data():
    # Create users
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin'
        )
        print("Admin user created")

    if not User.objects.filter(username='staff').exists():
        staff = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='staff123',
            role='staff'
        )
        print("Staff user created")

    if not User.objects.filter(username='viewer').exists():
        viewer = User.objects.create_user(
            username='viewer',
            email='viewer@example.com',
            password='viewer123',
            role='viewer'
        )
        print("Viewer user created")

    # Create categories
    categories_data = [
        {'name': 'Electronics', 'description': 'Electronic devices and components'},
        {'name': 'Office Supplies', 'description': 'General office supplies'},
        {'name': 'Furniture', 'description': 'Office and home furniture'},
        {'name': 'Books', 'description': 'Books and educational materials'},
        {'name': 'Clothing', 'description': 'Apparel and accessories'},
    ]

    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        if created:
            print(f"Category '{category.name}' created")

    # Create suppliers
    suppliers_data = [
        {
            'name': 'TechCorp Solutions',
            'contact_person': 'John Smith',
            'email': 'john@techcorp.com',
            'phone': '+1-555-0101',
            'address': '123 Tech Street, Silicon Valley, CA 94105'
        },
        {
            'name': 'Office Depot Inc.',
            'contact_person': 'Jane Doe',
            'email': 'jane@officedepot.com',
            'phone': '+1-555-0102',
            'address': '456 Supply Ave, New York, NY 10001'
        },
        {
            'name': 'Furniture World',
            'contact_person': 'Bob Wilson',
            'email': 'bob@furnitureworld.com',
            'phone': '+1-555-0103',
            'address': '789 Furniture Blvd, Chicago, IL 60601'
        },
    ]

    for sup_data in suppliers_data:
        supplier, created = Supplier.objects.get_or_create(
            name=sup_data['name'],
            defaults=sup_data
        )
        if created:
            print(f"Supplier '{supplier.name}' created")

    # Get references
    admin_user = User.objects.get(username='admin')
    electronics = Category.objects.get(name='Electronics')
    office_supplies = Category.objects.get(name='Office Supplies')
    furniture = Category.objects.get(name='Furniture')
    techcorp = Supplier.objects.get(name='TechCorp Solutions')
    office_depot = Supplier.objects.get(name='Office Depot Inc.')
    furniture_world = Supplier.objects.get(name='Furniture World')

    # Create products
    products_data = [
        {
            'name': 'Wireless Mouse',
            'description': 'Ergonomic wireless mouse with USB receiver',
            'sku': 'WM-001',
            'quantity': 50,
            'price': Decimal('29.99'),
            'category': electronics,
            'supplier': techcorp,
            'min_stock_level': 10
        },
        {
            'name': 'Mechanical Keyboard',
            'description': 'RGB backlit mechanical gaming keyboard',
            'sku': 'KB-002',
            'quantity': 25,
            'price': Decimal('89.99'),
            'category': electronics,
            'supplier': techcorp,
            'min_stock_level': 5
        },
        {
            'name': 'A4 Copy Paper',
            'description': 'White A4 copy paper, 500 sheets per pack',
            'sku': 'CP-003',
            'quantity': 200,
            'price': Decimal('8.99'),
            'category': office_supplies,
            'supplier': office_depot,
            'min_stock_level': 20
        },
        {
            'name': 'Office Chair',
            'description': 'Ergonomic office chair with lumbar support',
            'sku': 'OC-004',
            'quantity': 8,
            'price': Decimal('199.99'),
            'category': furniture,
            'supplier': furniture_world,
            'min_stock_level': 3
        },
        {
            'name': 'Standing Desk',
            'description': 'Height-adjustable standing desk',
            'sku': 'SD-005',
            'quantity': 12,
            'price': Decimal('299.99'),
            'category': furniture,
            'supplier': furniture_world,
            'min_stock_level': 5
        },
        {
            'name': 'Ballpoint Pens',
            'description': 'Blue ballpoint pens, pack of 10',
            'sku': 'BP-006',
            'quantity': 5,  # Low stock to demonstrate alerts
            'price': Decimal('4.99'),
            'category': office_supplies,
            'supplier': office_depot,
            'min_stock_level': 15
        },
    ]

    for prod_data in products_data:
        product, created = Product.objects.get_or_create(
            sku=prod_data['sku'],
            defaults={
                **prod_data,
                'created_by': admin_user,
                'last_modified_by': admin_user
            }
        )
        if created:
            print(f"Product '{product.name}' created")

    print("Sample data populated successfully!")
    print("\nSample login credentials:")
    print("Admin - Username: admin, Password: admin123")
    print("Staff - Username: staff, Password: staff123")  
    print("Viewer - Username: viewer, Password: viewer123")

if __name__ == '__main__':
    create_sample_data()