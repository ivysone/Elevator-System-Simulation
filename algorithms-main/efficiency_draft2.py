import random

# ----------------- DATA STRUCTURES -----------------
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

# ----------------- GLOBAL VARIABLES -----------------
request_queue = Queue()  # Unified queue for all external requests
priority_floors = PriorityQueue()
current_time = 0
WAIT_THRESHOLD = 5
request_times = {}  # Tracks wait times for all requests

# ----------------- ELEVATOR SYSTEM -----------------
class Elevator:
    def __init__(self, num_of_floors):
        self.total_floors = num_of_floors
        self.reg_list = []
        self.floor = 1
        self.direct = "up"  # Initial direction, adjusted dynamically
        self.floors_visited = 0
        self.internal_requests = set()

    def move(self, customers):
        global current_time
        current_time += 1
        
        # Collect all requests
        all_requests = set(self.internal_requests)
        for f in request_queue.get_all():
            all_requests.add(f)
        for node in priority_floors.heap.heap:
            all_requests.add(node.data)

        if not all_requests:
            return  # No movement if no requests

        # ESSTF-C Logic
        # 1. Calculate distances to all request floors
        distances = {f: abs(self.floor - f) for f in all_requests}
        
        # 2. Prefer current direction unless no requests ahead or priority overrides
        if self.direct == "up":
            ahead = [f for f in all_requests if f > self.floor]
            if not ahead and all_requests:
                self.direct = "down"
        else:
            ahead = [f for f in all_requests if f < self.floor]
            if not ahead and all_requests:
                self.direct = "up"

        # 3. Find clustered requests (consecutive floors)
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

        # 4. Choose next floor: prioritize nearest with clustering bonus
        min_distance = float('inf')
        next_floor = self.floor
        for f in all_requests:
            distance = distances[f]
            # Bonus for clusters: reduce effective distance if part of a larger cluster
            cluster_bonus = 0
            for cluster in clusters:
                if f in cluster and len(cluster) > 1:
                    cluster_bonus = len(cluster) * 0.5  # Encourage servicing clusters
                    break
            effective_distance = distance - cluster_bonus
            
            # Prefer direction unless priority overrides
            if (self.direct == "up" and f > self.floor) or (self.direct == "down" and f < self.floor) or priority_floors.contains(f):
                if effective_distance < min_distance:
                    min_distance = effective_distance
                    next_floor = f
            elif effective_distance < min_distance and not any(f2 > self.floor if self.direct == "up" else f2 < self.floor for f2 in all_requests):
                min_distance = effective_distance
                next_floor = f

        if next_floor != self.floor:
            self.floor = next_floor
            self.floors_visited += 1
            if next_floor < self.floor:
                self.direct = "down"
            elif next_floor > self.floor:
                self.direct = "up"

    def register_customer(self, customer):
        self.reg_list.append(customer)
        customer.indicator = 1
        self.internal_requests.add(customer.going_floor)
        print(f"  C{customer.ident} pressed INTERNAL button for {customer.going_floor}")

    def cancel_customer(self, customer):
        self.reg_list.remove(customer)
        customer.indicator = 0
        customer.fin = 1
        self.internal_requests.discard(customer.going_floor)

def promote_long_waits():
    global current_time, WAIT_THRESHOLD
    
    for floor in request_queue.get_all()[:]:
        if floor in request_times:
            wait_time = current_time - request_times[floor]
            if wait_time >= WAIT_THRESHOLD:
                request_queue.remove(floor)
                del request_times[floor]
                priority_floors.enqueue(floor, priority=-wait_time)
                print(f"\n⚠️ PROMOTION: Floor {floor} (waiting {wait_time} units)")
                print(f"   Moved to priority queue")

class Building:
    def __init__(self, num_of_floors, customers, elevator):
        self.total_floors = num_of_floors
        self.customers = customers
        self.elevator = elevator

    def run(self):
        while any(not c.fin for c in self.customers):
            direction = "↑" if self.elevator.direct == "up" else "↓"
            print(f"\n=== Floor {self.elevator.floor} {direction} [Time: {current_time}] ===")
            print(f"Active internal requests: {self.elevator.internal_requests}")
            
            current_floor = self.elevator.floor
            handled_external = False
            handled_internal = False

            # Handle priority floors first
            if priority_floors.contains(current_floor):
                print(f"\n🔥 EXTERNAL CALL: Priority Floor {current_floor}")
                served = []
                for c in self.customers:
                    if c.on_floor == current_floor and not c.indicator:
                        served.append(f"C{c.ident}")
                        self.elevator.register_customer(c)
                if served:
                    print(f"  Boarded: {', '.join(served)}")
                priority_floors.remove(current_floor)
                handled_external = True
            # Handle regular requests
            elif request_queue.contains(current_floor):
                print(f"\n⬆️⬇️ EXTERNAL CALL: Request at {current_floor}")
                served = []
                for c in self.customers:
                    if c.on_floor == current_floor and not c.indicator:
                        served.append(f"C{c.ident}")
                        self.elevator.register_customer(c)
                if served:
                    print(f"  Boarded: {', '.join(served)}")
                request_queue.remove(current_floor)
                handled_external = True

            # Handle internal requests
            exits = []
            for c in self.elevator.reg_list[:]:
                if c.going_floor == current_floor:
                    print(f"\n🎯 INTERNAL DESTINATION REACHED: Floor {current_floor}")
                    exits.append(f"C{c.ident}")
                    self.elevator.cancel_customer(c)
                    handled_internal = True
            if exits:
                print(f"  Exited: {', '.join(exits)}")

            if handled_external and handled_internal:
                print(f"\nℹ️ Stopping for both EXTERNAL and INTERNAL calls")
            elif handled_external:
                print(f"\nℹ️ Stopping primarily for EXTERNAL call")
            elif handled_internal:
                print(f"\nℹ️ Stopping primarily for INTERNAL call")

            self.elevator.move(self.customers)
            promote_long_waits()

    def output(self):
        print("\n===== FINAL REPORT =====")
        print(f"Total elevator movements: {self.elevator.floors_visited}")
        print("\nCustomer Details:")
        for c in sorted(self.customers, key=lambda x: x.ident):
            status = "DELIVERED" if c.fin else "WAITING"
            print(f"  [C{c.ident}] {c.on_floor} → {c.going_floor} ({status})")
            print(f"  {'-'*40}")

class Customer:
    def __init__(self, ID, num_of_floors):
        global current_time
        
        self.ident = ID
        self.indicator = 0
        self.fin = 0
        self.on_floor = random.randint(1, num_of_floors)
        
        while True:
            self.going_floor = random.randint(1, num_of_floors)
            if self.going_floor != self.on_floor:
                break
        
        # Unified request queue with priority for edge floors
        if self.on_floor == 1 or self.on_floor == num_of_floors:
            print(f"\n🆕 CUSTOMER {self.ident}:")
            print(f"  Priority floor detected!")
            print(f"  Waiting at floor {self.on_floor}")
            print(f"  Destination: {self.going_floor}")
            if not priority_floors.contains(self.on_floor):
                priority_floors.enqueue(self.on_floor, priority=0)
        else:
            print(f"\n🆕 CUSTOMER {self.ident}:")
            print(f"  From floor {self.on_floor} to {self.going_floor}")
            if not request_queue.contains(self.on_floor):
                request_queue.enqueue(self.on_floor)
                request_times[self.on_floor] = current_time

# ----------------- MAIN PROGRAM -----------------
num_customers = int(input("Enter number of customers: "))
num_floors = int(input("Enter number of floors: "))

customers = [Customer(i+1, num_floors) for i in range(num_customers)]
elevator = Elevator(num_floors)
building = Building(num_floors, customers, elevator)

print("\n======== SIMULATION START ========")
building.run()
building.output()
