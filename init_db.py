import sqlite3

def init_db():
    with open("schema.sql") as f:
        schema = f.read()

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()
    cursor.executescript(schema)
    connection.commit()
    connection.close()
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    init_db()
