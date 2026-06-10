import os
import matplotlib.pyplot as plt

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
up_queue = Queue()
down_queue = Queue()
priority_floors = PriorityQueue()
current_time = 0
WAIT_THRESHOLD = 5
up_queue_times = {}
down_queue_times = {}

# ----------------- ELEVATOR SYSTEM -----------------
class Elevator:
    def __init__(self, num_of_floors):
        self.total_floors = num_of_floors
        self.reg_list = []
        self.floor = 1
        self.direct = "up"
        self.floors_visited = 0
        self.internal_requests = set()

    def move(self, customers):
        global current_time
        current_time += 1
        
        self.external_floors = set()
        self.internal_floors = self.internal_requests.copy()
        
        for f in up_queue.get_all():
            self.external_floors.add(f)
        for f in down_queue.get_all():
            self.external_floors.add(f)
        for node in priority_floors.heap.heap:
            self.external_floors.add(node.data)

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

    def register_customer(self, customer):
        self.reg_list.append(customer)
        customer.indicator = 1
        customer.boarding_time = current_time
        self.internal_requests.add(customer.going_floor)
        print(f"  C{customer.ident} pressed INTERNAL button for {customer.going_floor}")

    def cancel_customer(self, customer):
        self.reg_list.remove(customer)
        customer.indicator = 0
        customer.fin = 1
        customer.exit_time = current_time
        self.internal_requests.discard(customer.going_floor)

def promote_long_waits():
    global current_time, WAIT_THRESHOLD
    
    for floor in up_queue.get_all()[:]:
        if floor in up_queue_times:
            wait_time = current_time - up_queue_times[floor]
            if wait_time >= WAIT_THRESHOLD:
                customers_waiting = [
                    f"C{c.ident}" for c in customers
                    if c.on_floor == floor and not c.indicator and c.direction == "up"
                ]
                up_queue.remove(floor)
                del up_queue_times[floor]
                priority_floors.enqueue(floor, priority=-wait_time)
                print(f"\n⚠️ PROMOTION: Floor {floor} (waiting {wait_time} units)")
                print(f"   Moved from UP queue to priority")

    for floor in down_queue.get_all()[:]:
        if floor in down_queue_times:
            wait_time = current_time - down_queue_times[floor]
            if wait_time >= WAIT_THRESHOLD:
                customers_waiting = [
                    f"C{c.ident}" for c in customers
                    if c.on_floor == floor and not c.indicator and c.direction == "down"
                ]
                down_queue.remove(floor)
                del down_queue_times[floor]
                priority_floors.enqueue(floor, priority=-wait_time)
                print(f"\n⚠️ PROMOTION: Floor {floor} (waiting {wait_time} units)")
                print(f"   Moved from DOWN queue to priority")

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

            if priority_floors.contains(current_floor):
                print(f"\n🔥 EXTERNAL CALL: Priority Floor {current_floor}")
                served = []
                for c in self.customers:
                    if c.on_floor == current_floor and not c.indicator:
                        served.append(f"C{c.ident}")
                        self.elevator.register_customer(c)
                if served:
                    print(f"  Boarded: {', '.join(served)}")
                else:
                    print("  No waiting customers")
                priority_floors.remove(current_floor)
                handled_external = True
            else:
                if self.elevator.direct == "up" and up_queue.contains(current_floor):
                    print(f"\n⬆️ EXTERNAL CALL: Up Request at {current_floor}")
                    served = []
                    for c in self.customers:
                        if c.on_floor == current_floor and not c.indicator and c.direction == "up":
                            served.append(f"C{c.ident}")
                            self.elevator.register_customer(c)
                    if served:
                        print(f"  Boarded: {', '.join(served)}")
                    else:
                        print("  No matching customers")
                    up_queue.remove(current_floor)
                    handled_external = True
                elif self.elevator.direct == "down" and down_queue.contains(current_floor):
                    print(f"\n⬇️ EXTERNAL CALL: Down Request at {current_floor}")
                    served = []
                    for c in self.customers:
                        if c.on_floor == current_floor and not c.indicator and c.direction == "down":
                            served.append(f"C{c.ident}")
                            self.elevator.register_customer(c)
                    if served:
                        print(f"  Boarded: {', '.join(served)}")
                    else:
                        print("  No matching customers")
                    down_queue.remove(current_floor)
                    handled_external = True

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
    def __init__(self, ID, on_floor, going_floor, num_of_floors):
        global current_time
        
        self.ident = ID
        self.indicator = 0
        self.fin = 0
        self.on_floor = on_floor
        self.going_floor = going_floor
        self.enqueue_time = current_time
        self.boarding_time = None
        self.exit_time = None
        
        self.direction = 'up' if self.going_floor > self.on_floor else 'down'
        
        if self.on_floor == 1 or self.on_floor == num_of_floors:
            print(f"\n🆕 CUSTOMER {self.ident}:")
            print(f"  Priority floor detected!")
            print(f"  Waiting at floor {self.on_floor}")
            print(f"  Will request INTERNAL call to {self.going_floor}")
            if not priority_floors.contains(self.on_floor):
                priority_floors.enqueue(self.on_floor, priority=0)
        else:
            print(f"\n🆕 CUSTOMER {self.ident}:")
            print(f"  From floor {self.on_floor} to {self.going_floor}")
            print(f"  Pressed {'UP' if self.direction == 'up' else 'DOWN'} button")
            print(f"  Will request INTERNAL call to {self.going_floor}")
            if self.direction == 'up':
                if not up_queue.contains(self.on_floor):
                    up_queue.enqueue(self.on_floor)
                    up_queue_times[self.on_floor] = current_time
            else:
                if not down_queue.contains(self.on_floor):
                    down_queue.enqueue(self.on_floor)
                    down_queue_times[self.on_floor] = current_time

# ----------------- EFFICIENCY CALCULATIONS -----------------
def calculate_efficiency(customers, elevator):
    total_wait_time = 0
    total_service_time = 0
    delivered_customers = 0

    for customer in customers:
        if customer.fin:
            if customer.boarding_time is None or customer.exit_time is None:
                continue

            wait_time = customer.boarding_time - customer.enqueue_time
            service_time = customer.exit_time - customer.boarding_time

            total_wait_time += wait_time
            total_service_time += service_time
            delivered_customers += 1

    if delivered_customers == 0:
        return 0, 0, elevator.floors_visited

    avg_wait_time = total_wait_time / delivered_customers
    avg_service_time = total_service_time / delivered_customers

    return avg_wait_time, avg_service_time, elevator.floors_visited

# ----------------- MAIN PROGRAM -----------------
try:
    script_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(script_dir, 'customers.txt')
    
    customer_data = []
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                parts = list(map(int, line.split()))
                if len(parts) != 2:
                    raise ValueError(f"Invalid format in line {line_num}: {line}")
                on_floor, going_floor = parts
                if on_floor < 1 or going_floor < 1:
                    raise ValueError(f"Non-positive floor in line {line_num}")
                customer_data.append((on_floor, going_floor))

    if not customer_data:
        raise ValueError("Data file is empty")

    all_floors = [f for pair in customer_data for f in pair]
    num_floors = max(all_floors)
    num_customers = len(customer_data)

except Exception as e:
    print(f"Error: {str(e)}")
    exit(1)

customers = []
for i, (on_floor, going_floor) in enumerate(customer_data, 1):
    customers.append(Customer(i, on_floor, going_floor, num_floors))

elevator = Elevator(num_floors)
building = Building(num_floors, customers, elevator)

print("\n======== SIMULATION START ========")
building.run()
building.output()

avg_wait_time, avg_service_time, total_floors_visited = calculate_efficiency(customers, elevator)

print("\n===== EFFICIENCY METRICS =====")
print(f"Average Wait Time: {avg_wait_time:.2f} units")
print(f"Average Service Time: {avg_service_time:.2f} units")
print(f"Total Floors Visited: {total_floors_visited}")

def plot_efficiency_chart(avg_wait_time, avg_service_time, total_floors_visited):
    labels = ["Average Wait Time", "Average Service Time", "Total Floors Visited"]
    values = [avg_wait_time, avg_service_time, total_floors_visited]

    plt.figure(figsize=(10, 6))
    plt.bar(labels, values, color=["blue", "green", "red"])
    plt.title("Elevator Efficiency Metrics")
    plt.ylabel("Time / Floors")
    plt.show()

plot_efficiency_chart(avg_wait_time, avg_service_time, total_floors_visited)
