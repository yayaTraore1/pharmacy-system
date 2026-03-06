from app.database import SessionLocal, engine, Base
from app.models.user import User

# Create tables if not exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Find the first user and make them admin
first_user = db.query(User).first()
if first_user:
    first_user.role = "admin"
    db.commit()
    print(f"User {first_user.username} set as admin")
else:
    print("No users found")

db.close()