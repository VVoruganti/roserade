import sqlite3
from sqlite_vec import serialize_float32
import sqlite_vec
import ollama

db = sqlite3.connect("./test.db")
db.enable_load_extension(True)
sqlite_vec.load(db)
db.enable_load_extension(False)


def get_embedding(text, model="nomic-embed-text"):
    embed = ollama.embed(model=model, input=text)
    return embed["embeddings"][0]


query = get_embedding("Interview strategy")

rows = db.execute(
    """
        SELECT embeddings.rowid, metadata.file_path, vec_distance_cosine(embeddings.embedding, ?) as distance
        FROM embeddings
        JOIN metadata ON embeddings.rowid = metadata.id
        ORDER BY distance ASC
        LIMIT ?
    """,
    [serialize_float32(query), 3],
).fetchall()

print(rows)
