import sqlite3

def maybe_create_table(sqlite_file: str) -> bool:
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()

    try :
        create_table_query = """
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY, 
            url TEXT NOT NULL, 
            alias TEXT NOT NULL, 
            created_at DATETIME NOT NULL,
            used INTEGER DEFAULT 1);
        """

        create_index_query = """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_urls_alias
        ON urls (alias);
        """

        cursor.execute(create_table_query)
        cursor.execute(create_index_query)
        db.commit()
        return True
    except Exception:
        return False

maybe_create_table( "/tmp/urldatabase.db")