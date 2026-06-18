MAX_HISTORY = 5

history = []
for i in range(1, 8):  # simulate 7 exchanges, one more than the window allows
    history = history + [{"question": f"Q{i}", "answer": f"A{i}"}]
    history = history[-MAX_HISTORY:]
    print(f"After exchange {i}: {[h['question'] for h in history]}")