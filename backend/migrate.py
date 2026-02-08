from sqlalchemy import text
from .database import engine

def migrate_db():
    try:
        with engine.connect() as conn:
            # Check if column exists, if not, create it
            # This is a bit hacky but works for development without full Alembic setup
            try:
                conn.execute(text("ALTER TABLE applications ADD COLUMN status VARCHAR DEFAULT 'Pending'"))
                conn.commit()
                print("Added status column to applications table.")
            except Exception as e:
                print(f"Migration error (probably column exists): {e}")
                
    except Exception as e:
        print(f"Database connection error: {e}")

if __name__ == "__main__":
    migrate_db()
