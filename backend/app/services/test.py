from vector_store import VectorStore
store = VectorStore()
print(store.count())        # 0
print(store.is_empty())     # True

store.add_bug("1", "Crash", "App crashes", metadata={"severity": "critical"})
print(store.count())        # 1

store.add_bug("2", "Login", "Cannot login", metadata={"severity": "high"})
results = store.retrieve_similar_with_metadata("login problem", n_results=2)
for r in results:
    print(r["bug_id"], r["similarity"], r["metadata"]["severity"])
# returned 2 highest bug

store.clear_collection()
print(store.count())        # → 0

store = VectorStore()
store.add_bug("keep", "Persist", "This should survive", metadata={"severity": "low"})
print(store.count())        # 1
store = VectorStore()
print(store.count())        # 1 
store.find_similar_bug(title="Crash", description="App crashes")
store.find_similar_bug(query="Crash") # 1