import sys
from random import randint

if __name__ == "__main__":
    num_of_nodes = int(sys.argv[1])

    char = 'a'
    clocks = [0 for _ in range(num_of_nodes)]
    events = [dict() for _ in range(num_of_nodes)]

    for i in range(26):
        node = randint(0, num_of_nodes - 1)
        clocks[node] += randint(1, 4)
        events[node][clocks[node]] = char
        char = chr(ord(char) + 1)

    with open("./src/test_cases.py", 'w') as test_cases:
        test_cases.write("test_events = [\n")
        for event in events:
            test_cases.write("{\n")
            for clock, text in event.items():
                test_cases.write(f"    {clock}: " + "\'" + text + "\'" + ",\n")
            test_cases.write("},\n")
        test_cases.write("]\n")

