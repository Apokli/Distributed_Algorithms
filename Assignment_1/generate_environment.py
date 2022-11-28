import sys

if __name__ == "__main__":
    num_of_nodes = int(sys.argv[1])

    # generate addresses.txt
    with open("./resources/addresses.txt", 'w') as addresses:
        for i in range(num_of_nodes):
            addresses.write(f"{i} localhost {9090 + i}\n")
    
    # generate addresses_docker.txt
    with open("./resources/addresses_docker.txt", 'w') as addresses_docker:
        for i in range(num_of_nodes):
            addresses_docker.write(f"{i} node{i} {9090 + i}\n")

    # generate docker-compose.yml
    with open("docker-compose.yml", 'w') as docker_compose:
        docker_compose.writelines(["version: '3.3'\n", "services:\n"])
        for i in range(num_of_nodes):
            docker_compose.writelines([f"  node{i}:\n", "    build: .\n", "    ports:\n", f"      - '{9090 + i}:{9090 + i}'\n", "    environment:\n", f"      PID: {i}\n"])

