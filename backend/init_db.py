from backend.migrations import upgrade_database

if __name__ == "__main__":
    upgrade_database()
    print("Database migrations are applied.")
