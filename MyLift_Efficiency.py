from LookLiftScheduler import Customer, Building, Elevator 
from ScanLiftScheduler import Customer, Building, Elevator 
import os
import matplotlib.pyplot as plt
from Data_Structure import Queue,PriorityQueue

# ----------------- EFFICIENCY ALGORITHM -----------------
eff_request_queue = Queue()
eff_priority_floors = PriorityQueue()
eff_current_time = 0
eff_WAIT_THRESHOLD = 5
eff_request_times = {}

class EffElevator:
    def __init__(self, num_floors):
        self.total_floors = num_floors
        self.reg_list = []
        self.floor = 1
        self.direct = "up"
        self.floors_visited = 0
        self.internal_requests = set()
        self.path = [self.floor]

    def move(self, customers):
        global eff_current_time
        eff_current_time += 1
        all_requests = set(self.internal_requests)
        for f in eff_request_queue.get_all(): all_requests.add(f)
        for node in eff_priority_floors.heap.heap: all_requests.add(node.data)
        if not all_requests:
            return
        distances = {f: abs(self.floor - f) for f in all_requests}
        if self.direct == "up":
            ahead = [f for f in all_requests if f > self.floor]
            if not ahead and all_requests:
                self.direct = "down"
        else:
            ahead = [f for f in all_requests if f < self.floor]
            if not ahead and all_requests:
                self.direct = "up"
        clusters = []
        sorted_floors = sorted(all_requests)
        current_cluster = []
        for i, f in enumerate(sorted_floors):
            if not current_cluster or f == current_cluster[-1] + 1:
                current_cluster.append(f)
            else:
                clusters.append(current_cluster)
                current_cluster = [f]
            if i == len(sorted_floors) - 1:
                clusters.append(current_cluster)
        min_distance = float('inf')
        next_floor = self.floor
        for f in all_requests:
            distance = distances[f]
            cluster_bonus = 0
            for cluster in clusters:
                if f in cluster and len(cluster) > 1:
                    cluster_bonus = len(cluster) * 0.5
                    break
            effective_distance = distance - cluster_bonus
            if (self.direct == "up" and f > self.floor) or (self.direct == "down" and f < self.floor) or eff_priority_floors.contains(f):
                if effective_distance < min_distance:
                    min_distance = effective_distance
                    next_floor = f
            elif effective_distance < min_distance and not any(f2 > self.floor if self.direct == "up" else f2 < self.floor for f2 in all_requests):
                min_distance = effective_distance
                next_floor = f
        if next_floor != self.floor:
            self.floor = next_floor
            self.floors_visited += 1
            self.path.append(self.floor)
            if next_floor < self.floor:
                self.direct = "down"
            elif next_floor > self.floor:
                self.direct = "up"

    def register_customer(self, customer):
        self.reg_list.append(customer)
        customer.indicator = 1
        customer.start_time = eff_current_time
        self.internal_requests.add(customer.going_floor)

    def cancel_customer(self, customer):
        self.reg_list.remove(customer)
        customer.indicator = 0
        customer.fin = 1
        customer.end_time = eff_current_time
        self.internal_requests.discard(customer.going_floor)

def eff_promote_long_waits(customers):
    global eff_current_time
    for floor in eff_request_queue.get_all()[:]:
        if floor in eff_request_times and eff_current_time - eff_request_times[floor] >= eff_WAIT_THRESHOLD:
            eff_request_queue.remove(floor)
            del eff_request_times[floor]
            eff_priority_floors.enqueue(floor, priority=-eff_current_time)

class EffBuilding:
    def __init__(self, customers, elevator):
        self.total_floors = elevator.total_floors
        self.customers = customers
        self.elevator = elevator

    def run(self):
        while any(not c.fin for c in self.customers):
            current_floor = self.elevator.floor
            if eff_priority_floors.contains(current_floor):
                for c in self.customers:
                    if c.on_floor == current_floor and not c.indicator:
                        self.elevator.register_customer(c)
                eff_priority_floors.remove(current_floor)
            elif eff_request_queue.contains(current_floor):
                for c in self.customers:
                    if c.on_floor == current_floor and not c.indicator:
                        self.elevator.register_customer(c)
                eff_request_queue.remove(current_floor)
            for c in self.elevator.reg_list[:]:
                if c.going_floor == current_floor:
                    self.elevator.cancel_customer(c)
            self.elevator.move(self.customers)
            eff_promote_long_waits(self.customers)

class EffCustomer:
    def __init__(self, ident, on_floor, going_floor, num_floors):
        self.ident = ident
        self.indicator = 0
        self.fin = 0
        self.on_floor = on_floor
        self.going_floor = going_floor
        self.start_time = None
        self.end_time = None
        self.request_time = eff_current_time
        if self.on_floor == 1 or self.on_floor == num_floors:
            if not eff_priority_floors.contains(self.on_floor):
                eff_priority_floors.enqueue(self.on_floor, priority=0)
        else:
            if not eff_request_queue.contains(self.on_floor):
                eff_request_queue.enqueue(self.on_floor)
                eff_request_times[self.on_floor] = eff_current_time

# ----------------- TEST FUNCTION -----------------

def read_customer_requests(filename):
    """
    Read customer requests from the specified file.
    Each line contains two integers: on_floor and going_floor.
    Skip invalid requests where on_floor == going_floor.
    """
    requests = []
    with open(filename, "r") as file:
        for line in file:
            on_floor, going_floor = map(int, line.strip().split())
            if on_floor == going_floor:
                print(f"Warning: on_floor == going_floor for request: {on_floor} -> {going_floor}. Skipping.")
                continue
            requests.append((on_floor, going_floor))
    return requests

def run_tests():
    # Read customer requests from file
    requests = read_customer_requests("customers.txt")
    num_customers = len(requests)

    # Find num_floors based on maximum floor in requests
    all_floors = [floor for request in requests for floor in request]
    num_floors = max(all_floors) if all_floors else 1

    print(f"\nTesting with {num_floors} floors and {num_customers} customers")
    print("Customer Requests:")
    for i, (on_floor, going_floor) in enumerate(requests, 1):
        print(f"  C{i}: {on_floor} → {going_floor}")

    # Test LOOK Algorithm
    global look_current_time, look_up_queue, look_down_queue, look_priority_floors, look_up_queue_times, look_down_queue_times
    look_current_time = 0
    look_up_queue = Queue()
    look_down_queue = Queue()
    look_priority_floors = PriorityQueue()
    look_up_queue_times = {}
    look_down_queue_times = {}
    look_customers = [LookCustomer(i+1, on_floor, going_floor, num_floors) for i, (on_floor, going_floor) in enumerate(requests)]
    look_elevator = LookElevator(num_floors)
    look_building = LookBuilding(look_customers, look_elevator)
    look_building.run()
    look_avg_wait, look_avg_service, look_moves = calculate_efficiency(look_customers, look_elevator)
    print(f"\nLOOK Algorithm: {look_moves} movements, Avg Waiting Time: {look_avg_wait:.2f}, Avg Service Time: {look_avg_service:.2f}")
    print(f"Path: {' -> '.join(map(str, look_elevator.path))}")

    # Test SCAN Algorithm
    global scan_current_time, scan_up_queue, scan_down_queue, scan_priority_floors, scan_up_queue_times, scan_down_queue_times
    scan_current_time = 0
    scan_up_queue = Queue()
    scan_down_queue = Queue()
    scan_priority_floors = PriorityQueue()
    scan_up_queue_times = {}
    scan_down_queue_times = {}
    scan_customers = [ScanCustomer(i+1, on_floor, going_floor, num_floors) for i, (on_floor, going_floor) in enumerate(requests)]
    scan_elevator = ScanElevator(num_floors)
    scan_building = ScanBuilding(scan_customers, scan_elevator)
    scan_building.run()
    scan_avg_wait, scan_avg_service, scan_moves = calculate_efficiency(scan_customers, scan_elevator)
    print(f"\nSCAN Algorithm: {scan_moves} movements, Avg Waiting Time: {scan_avg_wait:.2f}, Avg Service Time: {scan_avg_service:.2f}")
    print(f"Path: {' -> '.join(map(str, scan_elevator.path))}")

    # Test EFFICIENCY Algorithm
    global eff_current_time, eff_request_queue, eff_priority_floors, eff_request_times
    eff_current_time = 0
    eff_request_queue = Queue()
    eff_priority_floors = PriorityQueue()
    eff_request_times = {}
    eff_customers = [EffCustomer(i+1, on_floor, going_floor, num_floors) for i, (on_floor, going_floor) in enumerate(requests)]
    eff_elevator = EffElevator(num_floors)
    eff_building = EffBuilding(eff_customers, eff_elevator)
    eff_building.run()
    eff_avg_wait, eff_avg_service, eff_moves = calculate_efficiency(eff_customers, eff_elevator)
    print(f"\nEfficiency Algorithm: {eff_moves} movements, Avg Waiting Time: {eff_avg_wait:.2f}, Avg Service Time: {eff_avg_service:.2f}")
    print(f"Path: {' -> '.join(map(str, eff_elevator.path))}")

    # Compare Results
    print("\n===== PERFORMANCE COMPARISON =====")
    best_wait = min(look_avg_wait, scan_avg_wait, eff_avg_wait)
    winners = []
    if look_avg_wait == best_wait:
        winners.append((look_moves, "LOOK"))
    if scan_avg_wait == best_wait:
        winners.append((scan_moves, "SCAN"))
    if eff_avg_wait == best_wait:
        winners.append((eff_moves, "Efficiency"))
    if len(winners) > 1:
        best_moves = min(w[0] for w in winners)
        winner = next(w[1] for w in winners if w[0] == best_moves)
    else:
        winner = winners[0][1]
    print(f"{winner} Algorithm was the most efficient!")

    # Plotting the results
    algorithms = ["LOOK", "SCAN", "Efficiency"]
    movements = [look_moves, scan_moves, eff_moves]
    avg_wait_times = [look_avg_wait, scan_avg_wait, eff_avg_wait]
    avg_service_times = [look_avg_service, scan_avg_service, eff_avg_service]

    # Plot for movements
    plt.figure(figsize=(8, 6))
    bars = plt.bar(algorithms, movements, color=['blue', 'green', 'red'])
    plt.xlabel('Algorithm')
    plt.ylabel('Number of Movements')
    plt.title('Elevator Movements by Algorithm')
    plt.grid(True, axis='y')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, int(yval), ha='center', va='bottom')
    plt.show()
    plt.savefig('Movement.png')

    # Plot for average waiting times
    plt.figure(figsize=(8, 6))
    bars = plt.bar(algorithms, avg_wait_times, color=['blue', 'green', 'red'])
    plt.xlabel('Algorithm')
    plt.ylabel('Average Waiting Time (units)')
    plt.title('Average Waiting Time (until boarding) by Algorithm')
    plt.grid(True, axis='y')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, f"{yval:.2f}", ha='center', va='bottom')
    plt.show()
    plt.savefig('Waiting.png')

    # Optional: Plot for average service times
    plt.figure(figsize=(8, 6))
    bars = plt.bar(algorithms, avg_service_times, color=['blue', 'green', 'red'])
    plt.xlabel('Algorithm')
    plt.ylabel('Average Service Time (units)')
    plt.title('Average Service Time (inside elevator) by Algorithm')
    plt.grid(True, axis='y')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, f"{yval:.2f}", ha='center', va='bottom')
    plt.show()
    plt.savefig('Service.png')

if __name__ == "__main__":
    # Run the simulation once with fixed data
    run_tests()