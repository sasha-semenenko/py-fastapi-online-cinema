user_schema = {
    "id": 1,
    "email": "example@email.com",
    "password": "<PASSWORD>",
}


order_create_schema = {
    "user_id": user_schema,
    "status": "PAID"
}