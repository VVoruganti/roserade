import ollama
import sqlite3
import sqlite_vec
import os
import glob
from sqlite_vec import serialize_float32


def get_markdown_content(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def get_embedding(text, model="nomic-embed-text"):
    embed = ollama.embed(model=model, input=text)
    return embed["embeddings"][0]


def create_table(db):
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    # Create the vector table
    db.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS embeddings USING vec0(embedding float[768])
    """)

    # Create a separate metadata table
    db.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT
        )
    """)


def insert_embedding(conn, embedding, file_path):
    cursor = conn.cursor()

    # Insert into metadata table and get the ID
    cursor.execute("INSERT INTO metadata (file_path) VALUES (?)", (file_path,))
    metadata_id = cursor.lastrowid

    metadata_id = cursor.lastrowid

    # Insert into vec_items table
    # embedding_str = ",".join(map(str, embedding))
    cursor.execute(
        " INSERT INTO embeddings(rowid, embedding) VALUES (?, ?)",
        [metadata_id, serialize_float32(embedding)],
    )

    # conn.execute(
    #     "INSERT INTO embeddings(embedding, file_path) VALUES (?, ?)",
    #     (serialize_float32(embedding), file_path),
    # )


def process_directory(directory, conn):
    for markdown_file in glob.glob(
        os.path.join(directory, "**", "*.md"), recursive=True
    ):
        content = get_markdown_content(markdown_file)
        embedding = get_embedding(content)
        insert_embedding(conn, embedding, markdown_file)
        print(f"Processed: {markdown_file}")


def main():
    directory = input("Enter the directory path containing markdown files: ")
    db_path = input("Enter the path for the SQLite database file: ")

    db = sqlite3.connect(db_path)
    create_table(db)

    process_directory(directory, db)

    db.commit()
    db.close()

    print(f"Processing complete. Embeddings stored in the database at {db_path}")


if __name__ == "__main__":
    main()
