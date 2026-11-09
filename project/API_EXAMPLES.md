# API Examples

The browser app uses a session cookie. Log in first, then send that cookie with authenticated requests. Examples below use the supplied Sales account and representative response values.

## Log in

Request:

```http
POST /api/login
Content-Type: application/json

{"email":"sales@example.com","password":"ChangeMe123!"}
```

Successful response:

```json
{"message":"Logged in","role":"sales"}
```

## List products

Sales users only see active products. Search and pagination parameters are optional.

Request:

```http
GET /api/products?search=lamp&limit=20&offset=0
```

Successful response:

```json
{
  "items": [
    {
      "id": 1,
      "product_code": "LAMP-001",
      "name": "Desk Lamp",
      "category": "Lighting",
      "price": 39.99,
      "stock_quantity": 25,
      "is_active": true
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

## Create a Draft order

The server looks up the product price. Clients send product IDs and quantities, not trusted prices or totals.

Request:

```http
POST /api/orders
Content-Type: application/json

{"customer_id":1,"items":[{"product_id":1,"quantity":2}],"discount_percent":10}
```

Successful response with HTTP 201:

```json
{"id":42,"order_number":"SO-0123456789AB","status":"draft"}
```

## View an order

Request:

```http
GET /api/orders/42
```

Successful response:

```json
{
  "id": 42,
  "order_number": "SO-0123456789AB",
  "customer_id": 1,
  "created_by": 2,
  "status": "draft",
  "discount_percent": 10.0,
  "subtotal": 79.98,
  "discount_amount": 8.0,
  "total": 71.98,
  "created_at": "2026-11-09T12:00:00",
  "updated_at": "2026-11-09T12:00:00",
  "items": [
    {
      "product_id": 1,
      "quantity": 2,
      "unit_price": 39.99,
      "line_total": 79.98
    }
  ]
}
```

Sales users can view only their own orders. They receive a not-found response for another user's order.

## Confirm and cancel

Confirm a Draft order:

```http
POST /api/orders/42/confirm
```

```json
{"message":"Order confirmed"}
```

Cancel an order:

```http
POST /api/orders/42/cancel
```

```json
{"message":"Order cancelled"}
```

Confirmation checks stock before changing it. If an item is short, the request returns HTTP 409 and no order or stock changes are committed. Unauthenticated requests return HTTP 401; invalid request fields are reported with HTTP 422.
