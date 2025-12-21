import time
from functools import wraps

def log_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"[LOG] {func.__name__} executed in {end - start:.4f} seconds")
        return result
    return wrapper