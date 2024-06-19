from mitigation import get_detection_probabilities
import time

run_start = time.time()

for i in [0]:#range(365):
    print(f"\nStarting night {i}")
    start = time.time()
    get_detection_probabilities(night_start=i, pool_size=30, schedule_type='predicted')
    print(f"Time for this run: {time.time() - start:1.1f}s")

print(f"\n\nOverall, it took {time.time() - run_start:1.1f}s")
