from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")
a = model.encode("Deadlock occurs when processes wait for each other.")
b = model.encode("Processes are stuck waiting on one another forever.")
print(util.cos_sim(a, b))