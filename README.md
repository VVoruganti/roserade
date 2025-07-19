# Roserade

A Project for making a local set of embeddings based on my notes that I can run
RAG queries against.

The project uses `ollama`, and the `nomic-embed-text` model for the embedding
model. I'm using the `sqlite-vec` package to create a local database for the
embeddings

## To Do

- [ ] Make a bash script for running rag searches from anywhere
- [ ] I'm feeling lucky style open the top search in neovim or less
- [ ] cron job for re-syncing embeddings whenever they are out of re-sync
- [ ] Experiment with making it more fine grained (sections of markdown files)
- [ ] Add the text content to the database (and/or line number of section)

## Inspiration

https://github.com/ggozad/haiku.rag
