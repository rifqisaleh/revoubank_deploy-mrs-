from app.database import engine, Base  # Import database engine and base class
from app.models import User, Transaction  # Import models

Base.metadata.create_all(bind=engine)

print(" Tables created successfully!")
