import sys
import random
import numpy as np

if __name__ == "__main__":
    num_of_nodes = int(sys.argv[1])
    candidate_chance = 0.25
    has_candidate = False
    beta = 10   # The lower the more likely it happens at the start
    
    clocks = [0 for _ in range(num_of_nodes)]
    events = [dict() for _ in range(num_of_nodes)]

    for i in range(num_of_nodes):
        is_candidate = candidate_chance - random.random()
        if is_candidate > 0 or (i == num_of_nodes - 1 and not has_candidate):
            has_candidate = True
            clocks[i] = int(np.random.exponential(scale=beta)) + 1
            events[i][clocks[i]] = "start"

    with open("./src/test_cases.py", 'w') as test_cases:
        test_cases.write("test_events = [\n")
        for event in events:
            test_cases.write("{\n")
            for clock, text in event.items():
                test_cases.write(f"    {clock}: " + "\"" + text + "\"" + ",\n")
            test_cases.write("},\n")
        test_cases.write("]\n")

