# create_admin.py
from backend import add_user, init_db

# Initialize database
init_db()

# Define your admin credentials
email = "admin@example.com"
password = "adminpass"
first_name = "Admin"
last_name = "User"

# Create admin user
success = add_user(email, password, first_name, last_name, is_admin=1)

if success:
    print("✅ Admin account created successfully!")
    print(f"Email: {email}")
    print(f"Password: {password}")
else:
    print("⚠️ Admin already exists!")
