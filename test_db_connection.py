from app import create_app, db
import sys
import traceback

def test_connection():
    app = create_app()
    with app.app_context():
        try:
            # Try to connect to the database
            db.engine.connect()
            print("✅ Successfully connected to the database!")
            
            # Try to execute a simple query
            result = db.session.execute("SELECT 1")
            print("✅ Successfully executed a test query!")
            
            # Get database information
            version = db.session.execute("SELECT VERSION()").scalar()
            print(f"📊 Database version: {version}")
            
            return True
            
        except Exception as e:
            print("❌ Failed to connect to the database!")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print("\nDetailed error traceback:")
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1) 