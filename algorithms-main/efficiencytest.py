import random

# ----------------- DATA STRUCTURES (Shared Across All Algorithms) -----------------

class QueueNode:
    def __init__(self, data):
        self.data = data
        self.next = None

class Queue:
    def __init__(self):
        self.head = None
        self.tail = None

    def enqueue(self, data):
        new_node = QueueNode(data)
        if self.tail is None:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node

    def dequeue(self):
        if self.head is None:
            return None
        data = self.head.data
        self.head = self.head.next
        if self.head is None:
            self.tail = None
        return data

    def is_empty(self):
        return self.head is None

    def contains(self, data):
        current = self.head
        while current:
            if current.data == data:
                return True
            current = current.next
        return False

    def remove(self, data):
        if self.head is None:
            return
        if self.head.data == data:
            self.dequeue()
            return
        current = self.head
        while current.next:
            if current.next.data == data:
                current.next = current.next.next
                if current.next is None:
                    self.tail = current
                return
            current = current.next

    def get_all(self):
        floors = []
        current = self.head
        while current:
            floors.append(current.data)
            current = current.next
        return floors

class HeapNode:
    def __init__(self, priority, timestamp, data):
        self.priority = priority
        self.timestamp = timestamp
        self.data = data

    def __lt__(self, other):
        if self.priority == other.priority:
            return self.timestamp < other.timestamp
        return self.priority < other.priority

class Heap:
    def __init__(self):
        self.heap = []

    def insert(self, node):
        self.heap.append(node)
        self._percolate_up(len(self.heap) - 1)

    def _percolate_up(self, index):
        parent = (index - 1) // 2
        while parent >= 0 and self.heap[index] < self.heap[parent]:
            self.heap[index], self.heap[parent] = self.heap[parent], self.heap[index]
            index = parent
            parent = (index - 1) // 2

    def extract_min(self):
        if not self.heap:
            return None
        min_node = self.heap[0]
        last_node = self.heap.pop()
        if self.heap:
            self.heap[0] = last_node
            self._percolate_down(0)
        return min_node

    def _percolate_down(self, index):
        left = 2 * index + 1
        right = 2 * index + 2
        smallest = index
        if left < len(self.heap) and self.heap[left] < self.heap[smallest]:
            smallest = left
        if right < len(self.heap) and self.heap[right] < self.heap[smallest]:
            smallest = right
        if smallest != index:
            self.heap[index], self.heap[smallest] = self.heap[smallest], self.heap[index]
            self._percolate_down(smallest)

    def is_empty(self):
        return len(self.heap) == 0

class PriorityQueue:
    def __init__(self):
        self.heap = Heap()
        self.timestamp = 0

    def enqueue(self, data, priority):
        self.timestamp += 1
        node = HeapNode(priority, self.timestamp, data)
        self.heap.insert(node)

    def dequeue(self):
        node = self.heap.extract_min()
        if node:
            return node.data
        return None

    def is_empty(self):
        return self.heap.is_empty()

    def contains(self, data):
        for node in self.heap.heap:
            if node.data == data:
                return True
        return False

    def remove(self, data):
        for i, node in enumerate(self.heap.heap):
            if node.data == data:
                self.heap.heap.pop(i)
                new_heap = Heap()
                for n in self.heap.heap:
                    new_heap.insert(n)
                self.heap = new_heap
                return

# ----------------- LOOK ALGORITHM -----------------

look_up_queue = Queue()
look_down_queue = Queue()
look_priority_floors = PriorityQueue()
look_current_time = 0
look_WAIT_THRESHOLD = 5
look_up_queue_times = {}
look_down_queue_times = {}

class LookElevator:
    def __init__(self, num_floors):
        self.total_floors = num_floors
        self.reg_list = []
        self.floor = 1
        self.direct = "up"
        self.floors_visited = 0
        self.internal_requests = set()
        self.path = [self.floor]  # Initialize path with starting floor

    def move(self, customers):
        global look_current_time
        look_current_time += 1
        self.external_floors = set()
        self.internal_floors = self.internal_requests.copy()
        for f in look_up_queue.get_all(): self.external_floors.add(f)
        for f in look_down_queue.get_all(): self.external_floors.add(f)
        for node in look_priority_floors.heap.heap: self.external_floors.add(node.data)
        request_floors = self.external_floors.union(self.internal_floors)
        if not request_floors:
            return
        if self.direct == "up":
            above = [f for f in request_floors if f > self.floor]
            if above:
                self.floor = min(above)
            else:
                self.direct = "down"
                self.floor = max(request_floors) if request_floors else self.floor
        else:
            below = [f for f in request_floors if f < self.floor]
            if below:
                self.floor = max(below)
            else:
                self.direct = "up"
                self.floor = min(request_floors) if request_floors else self.floor
        self.floors_visited += 1
        self.path.append(self.floor)  # Append new floor to path

    def register_customer(self, customer):
        self.reg_list.append(customer)
        customer.indicator = 1
        customer.start_time = look_current_time
        self.internal_requests.add(customer.going_floor)

    def cancel_customer(self, customer):
        self.reg_list.remove(customer)
        customer.indicator = 0
        customer.fin = 1
        customer.end_time = look_current_time
        self.internal_requests.discard(customer.going_floor)

def look_promote_long_waits(customers):
    global look_current_time
    for floor in look_up_queue.get_all()[:]:
        if floor in look_up_queue_times and look_current_time - look_up_queue_times[floor] >= look_WAIT_THRESHOLD:
            look_up_queue.remove(floor)
            del look_up_queue_times[floor]
            look_priority_floors.enqueue(floor, priority=-look_current_time)
    for floor in look_down_queue.get_all()[:]:
        if floor in look_down_queue_times and look_current_time - look_down_queue_times[floor] >= look_WAIT_THRESHOLD:
            look_down_queue.remove(floor)
            del look_down_queue_times[floor]
            look_priority_floors.enqueue(floor, priority=-look_current_time)

class LookBuilding:
    def __init__(self, customers, elevator):
        self.total_floors = elevator.total_floors
        self.customers = customers
        self.elevator = elevator

    def run(self):
        while any(not c.fin for c in self.customers):
            current_floor = self.elevator.floor
            if look_priority_floors.contains(current_floor):
                for c in self.customers:
                    if c.on_floor == current_floor and not c.indicator:
                        self.elevator.register_customer(c)
                look_priority_floors.remove(current_floor)
            elif self.elevator.direct == "up" and look_up_queue.contains(current_floor):
                for c in self.customers:
                    if c.on_floor == current_floor and not c.indicator and c.direction == "up":
                        self.elevator.register_customer(c)
                look_up_queue.remove(current_floor)
            elif self.elevator.direct == "down" and look_down_queue.contains(current_floor):
                for c in self.customers:
                    if c.on_floor == current_floor and not c.indicator and c.direction == "down":
                        self.elevator.register_customer(c)
                look_down_queue.remove(current_floor)
            for c in self.elevator.reg_list[:]:
                if c.going_floor == current_floor:
                    self.elevator.cancel_customer(c)
            self.elevator.move(self.customers)
            look_promote_long_waits(self.customers)

class LookCustomer:
    def __init__(self, ident, on_floor, going_floor, num_floors):
        self.ident = ident
        self.indicator = 0
        self.fin = 0
        self.on_floor = on_floor
        self.going_floor = going_floor
        self.direction = 'up' if going_floor > on_floor else 'down'
        self.start_time = None
        self.end_time = None
        self.request_time = look_current_time
        if self.on_floor == 1 or self.on_floor == num_floors:
            if not look_priority_floors.contains(self.on_floor):
                look_priority_floors.enqueue(self.on_floor, priority=0)
        elif self.direction == 'up':
            if not look_up_queue.contains(self.on_floor):
                look_up_queue.enqueue(self.on_floor)
                look_up_queue_times[self.on_floor] = look_current_time
        else:
            if not look_down_queue.contains(self.on_floor):
                look_down_queue.enqueue(self.on_floor)
                look_down_queue_times[self.on_floor] = look_current_time

# ----------------- SCAN ALGORITHM -----------------

scan_up_queue = Queue()
scan_down_queue = Queue()
scan_priority_floors = PriorityQueue()
scan_current_time = 0
scan_WAIT_THRESHOLD = 5
scan_up_queue_times = {}
scan_down_queue_times = {}

class ScanElevator:
    def __init__(self, num_floors):
        self.total_floors = num_floors
        self.reg_list = []
        self.floor = 1
        self.direct = "up"
        self.floors_visited = 0
        self.internal_requests = set()
        self.path = [self.floor]  # Initialize path with starting floor

    def move(self, customers):
        global scan_current_time
        scan_current_time += 1
        self.external_floors = set()
        self.internal_floors = self.internal_requests.copy()
        for f in scan_up_queue.get_all(): self.external_floors.add(f)
        for f in scan_down_queue.get_all(): self.external_floors.add(f)
        for node in scan_priority_floors.heap.heap: self.external_floors.add(node.data)
        if self.direct == "up":
            if self.floor < self.total_floors:
                self.floor += 1
            else:
                self.direct = "down"
                self.floor -= 1
        else:
            if self.floor > 1:
                self.floor -= 1
            else:
                self.direct = "up"
                self.floor += 1
        self.floors_visited += 1
        self.path.append(self.floor)  # Append new floor to path

    def register_customer(self, customer):
        self.reg_list.append(customer)
        customer.indicator = 1
        customer.start_time = scan_current_time
        self.internal_requests.add(customer.going_floor)

    def cancel_customer(self, customer):
        self.reg_list.remove(customer)
        customer.indicator = 0
        customer.fin = 1
        customer.end_time = scan_current_time
        self.internal_requests.discard(customer.going_floor)

def scan_promote_long_waits(customers):
    global scan_current_time
    for floor in scan_up_queue.get_all()[:]:
        if floor in scan_up_queue_times and scan_current_time - scan_up_queue_times[floor] >= scan_WAIT_THRESHOLD:
            scan_up_queue.remove(floor)
            del scan_up_queue_times[floor]
            scan_priority_floors.enqueue(floor, priority=-scan_current_time)
    for floor in scan_down_queue.get_all()[:]:
        if floor in scan_down_queue_times and scan_current_time - scan_down_queue_times[floor] >= scan_WAIT_THRESHOLD:
            scan_down_queue.remove(floor)
            del scan_down_queue_times[floor]
            scan_priority_floors.enqueue(floor, priority=-scan_current_time)

class ScanBuilding:
    def __init__(self, customers, elevator):
        self.total_floors = elevator.total_floors
        self.customers = customers
        self.elevator = elevator

    def run(self):
        while any(not c.fin for c in self.customers):
            current_floor = self.elevator.floor
            if scan_priority_floors.contains(current_floor):
                for c in self.customers:
                    if c.on_floor == current_floor and not c.indicator:
                        self.elevator.register_customer(c)
                scan_priority_floors.remove(current_floor)
            elif self.elevator.direct == "up" and scan_up_queue.contains(current_floor):
                for c in self.customers:
                    if c.on_floor == current_floor and not c.indicator and c.direction == "up":
                        self.elevator.register_customer(c)
                scan_up_queue.remove(current_floor)
            elif self.elevator.direct == "down" and scan_down_queue.contains(current_floor):
                for c in self.customers:
                    if c.on_floor == current_floor and not c.indicator and c.direction == "down":
                        self.elevator.register_customer(c)
                scan_down_queue.remove(current_floor)
            for c in self.elevator.reg_list[:]:
                if c.going_floor == current_floor:
                    self.elevator.cancel_customer(c)
            self.elevator.move(self.customers)
            scan_promote_long_waits(self.customers)

class ScanCustomer:
    def __init__(self, ident, on_floor, going_floor, num_floors):
        self.ident = ident
        self.indicator = 0
        self.fin = 0
        self.on_floor = on_floor
        self.going_floor = going_floor
        self.direction = 'up' if going_floor > on_floor else 'down'
        self.start_time = None
        self.end_time = None
        self.request_time = scan_current_time
        if self.on_floor == 1 or self.on_floor == num_floors:
            if not scan_priority_floors.contains(self.on_floor):
                scan_priority_floors.enqueue(self.on_floor, priority=0)
        elif self.direction == 'up':
            if not scan_up_queue.contains(self.on_floor):
                scan_up_queue.enqueue(self.on_floor)
                scan_up_queue_times[self.on_floor] = scan_current_time
        else:
            if not scan_down_queue.contains(self.on_floor):
                scan_down_queue.enqueue(self.on_floor)
                scan_down_queue_times[self.on_floor] = scan_current_time

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
        self.path = [self.floor]  # Initialize path with starting floor

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
            self.path.append(self.floor)  # Append new floor to path
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

def calculate_avg_wait_time(customers, num_customers):
    total_wait = 0
    for c in customers:
        if c.end_time is not None and c.request_time is not None:
            total_wait += c.end_time - c.request_time
    return total_wait / num_customers if num_customers > 0 else 0

def run_tests():
    # Random parameters for this run
    num_floors = random.randint(5, 20)
    num_customers = random.randint(5, 15)
    customer_requests = []
    for i in range(num_customers):
        on_floor = random.randint(1, num_floors)
        while True:
            going_floor = random.randint(1, num_floors)
            if going_floor != on_floor:
                break
        customer_requests.append((i + 1, on_floor, going_floor))

    print(f"\nTesting with {num_floors} floors and {num_customers} customers")
    print("Customer Requests:")
    for ident, on_floor, going_floor in customer_requests:
        print(f"  C{ident}: {on_floor} → {going_floor}")

    # Test LOOK Algorithm
    global look_current_time, look_up_queue, look_down_queue, look_priority_floors, look_up_queue_times, look_down_queue_times
    look_current_time = 0
    look_up_queue = Queue()
    look_down_queue = Queue()
    look_priority_floors = PriorityQueue()
    look_up_queue_times = {}
    look_down_queue_times = {}
    look_customers = [LookCustomer(ident, on_floor, going_floor, num_floors) for ident, on_floor, going_floor in customer_requests]
    look_elevator = LookElevator(num_floors)
    look_building = LookBuilding(look_customers, look_elevator)
    look_building.run()
    look_moves = look_elevator.floors_visited
    look_avg_wait = calculate_avg_wait_time(look_customers, num_customers)

    # Test SCAN Algorithm
    global scan_current_time, scan_up_queue, scan_down_queue, scan_priority_floors, scan_up_queue_times, scan_down_queue_times
    scan_current_time = 0
    scan_up_queue = Queue()
    scan_down_queue = Queue()
    scan_priority_floors = PriorityQueue()
    scan_up_queue_times = {}
    scan_down_queue_times = {}
    scan_customers = [ScanCustomer(ident, on_floor, going_floor, num_floors) for ident, on_floor, going_floor in customer_requests]
    scan_elevator = ScanElevator(num_floors)
    scan_building = ScanBuilding(scan_customers, scan_elevator)
    scan_building.run()
    scan_moves = scan_elevator.floors_visited
    scan_avg_wait = calculate_avg_wait_time(scan_customers, num_customers)

    # Test EFFICIENCY Algorithm
    global eff_current_time, eff_request_queue, eff_priority_floors, eff_request_times
    eff_current_time = 0
    eff_request_queue = Queue()
    eff_priority_floors = PriorityQueue()
    eff_request_times = {}
    eff_customers = [EffCustomer(ident, on_floor, going_floor, num_floors) for ident, on_floor, going_floor in customer_requests]
    eff_elevator = EffElevator(num_floors)
    eff_building = EffBuilding(eff_customers, eff_elevator)
    eff_building.run()
    eff_moves = eff_elevator.floors_visited
    eff_avg_wait = calculate_avg_wait_time(eff_customers, num_customers)

    # Compare Results
    print("\n===== PERFORMANCE COMPARISON =====")
    print(f"LOOK Algorithm: {look_moves} movements, Avg Wait Time: {look_avg_wait:.2f} units")
    print(f"Path: {' -> '.join(map(str, look_elevator.path))}")
    print(f"SCAN Algorithm: {scan_moves} movements, Avg Wait Time: {scan_avg_wait:.2f} units")
    print(f"Path: {' -> '.join(map(str, scan_elevator.path))}")
    print(f"Efficiency Algorithm: {eff_moves} movements, Avg Wait Time: {eff_avg_wait:.2f} units")
    print(f"Path: {' -> '.join(map(str, eff_elevator.path))}")

    # Determine most efficient (priority to lowest avg wait time, then movements)
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

    # Write winner to file
    with open("winners.txt", "a") as file:
        file.write(f"{winner}\n")

if __name__ == "__main__":
    # Run the simulation once (increase range for multiple runs)
    for i in range(1):
        run_tests()