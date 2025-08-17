# Stock Management API Documentation

## Overview
A comprehensive REST API for inventory management with role-based access control, built with Django and Django REST Framework.

## Authentication
The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

Response:
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## User Roles
- **Admin**: Full access to all endpoints
- **Staff**: Can manage products, categories, suppliers, and stock
- **Viewer**: Read-only access

## API Endpoints

### Users
- `GET /api/users/` - List all users (Admin only)
- `POST /api/users/` - Create new user (Admin only)
- `GET /api/users/{id}/` - Get user details (Admin only)
- `PUT /api/users/{id}/` - Update user (Admin only)
- `DELETE /api/users/{id}/` - Delete user (Admin only)

### Categories
- `GET /api/categories/` - List categories
- `POST /api/categories/` - Create category (Staff+)
- `GET /api/categories/{id}/` - Get category details
- `PUT /api/categories/{id}/` - Update category (Staff+)
- `DELETE /api/categories/{id}/` - Delete category (Staff+)

### Suppliers
- `GET /api/suppliers/` - List suppliers
- `POST /api/suppliers/` - Create supplier (Staff+)
- `GET /api/suppliers/{id}/` - Get supplier details
- `PUT /api/suppliers/{id}/` - Update supplier (Staff+)
- `DELETE /api/suppliers/{id}/` - Delete supplier (Staff+)

### Products
- `GET /api/products/` - List products with filtering and search
- `POST /api/products/` - Create product (Staff+)
- `GET /api/products/{id}/` - Get product details
- `PUT /api/products/{id}/` - Update product (Staff+)
- `DELETE /api/products/{id}/` - Delete product (Staff+)

#### Product Filtering
```http
GET /api/products/?category=electronics&supplier=acme&low_stock=true
```

Available filters:
- `name` - Filter by name (contains)
- `sku` - Filter by SKU (exact match)
- `category` - Filter by category name
- `supplier` - Filter by supplier name
- `price_min` / `price_max` - Price range
- `quantity_min` / `quantity_max` - Quantity range
- `low_stock` - Products below minimum stock level
- `out_of_stock` - Products with zero quantity
- `is_active` - Active/inactive products

### Stock Management
- `GET /api/stock-logs/` - List all stock movements
- `GET /api/products/{id}/stock-logs/` - Get stock logs for specific product
- `POST /api/products/{id}/update-stock/` - Update product stock (Staff+)

#### Stock Update Example
```http
POST /api/products/1/update-stock/
Content-Type: application/json

{
    "action": "restock",
    "quantity_change": 50,
    "reason": "Weekly restock from supplier",
    "reference_number": "PO-2024-001",
    "unit_cost": 15.50
}
```

### Reports
- `GET /api/reports/inventory/` - Comprehensive inventory report
- `GET /api/reports/low-stock/` - Products with low stock
- `GET /api/dashboard/stats/` - Dashboard statistics

#### Inventory Report Example
```http
GET /api/reports/inventory/?category=electronics&supplier=acme
```

Response includes:
- Total products count
- Low stock and out of stock counts
- Total inventory value
- Category and supplier statistics
- Recent stock movement activity

## Error Responses
The API returns appropriate HTTP status codes with detailed error messages:

```json
{
    "error": "Product not found or inactive"
}
```

Common status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

## Pagination
List endpoints support pagination:
```json
{
    "count": 150,
    "next": "http://api.example.com/api/products/?page=2",
    "previous": null,
    "results": [...]
}
```

## Example Usage

### Create a Product
```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Headphones",
    "description": "High-quality bluetooth headphones",
    "sku": "WH-001",
    "quantity": 100,
    "price": 79.99,
    "category": 1,
    "supplier": 1,
    "min_stock_level": 10
  }'
```

### Update Stock
```bash
curl -X POST http://localhost:8000/api/products/1/update-stock/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "sale",
    "quantity_change": -5,
    "reason": "Sold 5 units to customer"
  }'
```

### Get Low Stock Report
```bash
curl -X GET http://localhost:8000/api/reports/low-stock/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```