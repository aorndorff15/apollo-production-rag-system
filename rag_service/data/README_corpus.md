# Put your corpus here

Drop the `.md` / `.txt` files your Milestone 1 system answers from into this folder (subfolders are fine). The reference
`rag.py` chunks them at startup, embeds them through the UNC AI Gateway, and caches the result in `index.npz`.

If your Milestone 1 index lives in Chroma, Pinecone, or Weaviate instead, you don't need this folder at all — replace
`RAGPipeline.load()` and `RAGPipeline.retrieve()` in `rag.py` with your own code and delete this file.

This README is itself a tiny corpus, so the service works before you add anything. Ask it: "Where does the corpus go?"
