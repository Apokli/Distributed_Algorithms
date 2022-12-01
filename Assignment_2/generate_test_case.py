import sys
from random import randint, sample

if __name__ == "__main__":
    num_of_nodes = int(sys.argv[1])
    trans = 10
    greets = 5
    
    generator = sample([1 for _ in range(trans)] + [0 for _ in range(greets)] + [2], trans + greets + 1)
    clocks = [0 for _ in range(num_of_nodes)]
    events = [dict() for _ in range(num_of_nodes)]

    for i in generator:
        src = randint(0, num_of_nodes - 1)
        clocks[src] += randint(1, 4)
        dst = src
        while dst == src:
            dst = randint(0, num_of_nodes - 1)
        if i == 0:
            events[src][clocks[src]] = f"How are you doing! {dst}"
        elif i == 1:
            events[src][clocks[src]] = f"Give {randint(0, 1000)} to {dst}"
        else:
            events[src][clocks[src]] = "Initiate Record"

    with open("./src/test_cases.py", 'w') as test_cases:
        test_cases.write("test_events = [\n")
        for event in events:
            test_cases.write("{\n")
            for clock, text in event.items():
                test_cases.write(f"    {clock}: " + "\"" + text + "\"" + ",\n")
            test_cases.write("},\n")
        test_cases.write("]\n")

