from sqlalchemy.orm import Session
from .database import engine, Base, SessionLocal
from .models import Commission

# Create tables
Base.metadata.create_all(bind=engine)

def seed_db():
    db = SessionLocal()
    
    # Check if data already exists
    existing = db.query(Commission).first()
    if existing:
        print("Database already seeded")
        return

    # Create the 'New Commission (Web Developer)'
    commission = Commission(
        title="New Commission (Web Developer)",
        category="Web Developer",
        description="Seeking a JavaScript developer for Wix Velo and Blocks projects. While prior Wix expertise isn't required, strong JavaScript fundamentals, API experience, and the ability to apply platform documentation are essential. The work involves custom frontend logic, backend functions, database interactions, and developing reusable components. Candidates familiar with modern JS, Node.js, or frontend frameworks should be a good fit."
    )
    
    db.add(commission)
    db.commit()
    print("Seeded database with initial commission.")
    db.close()

if __name__ == "__main__":
    seed_db()
