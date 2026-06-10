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
        self.reg_list = []  # List of registered customers inside the elevator
        self.floor = 1  # Current floor
        self.direct = "up"  # Current direction
        self.floors_visited = 0  # Number of moves made
        self.internal_requests = set()  # Floors requested inside the elevator

    def move(self, customers):
        global current_time
        current_time += 1
        
        # Collect external and internal requests
        self.external_floors = set()
        self.internal_floors = self.internal_requests.copy()
        
        # Gather external requests from queues
        for f in up_queue.get_all():
            self.external_floors.add(f)
        for f in down_queue.get_all():
            self.external_floors.add(f)
        for node in priority_floors.heap.heap:
            self.external_floors.add(node.data)

        # All floors with requests
        request_floors = self.external_floors.union(self.internal_floors)
        
        if not request_floors:
            return  # No movement if no requests

        # Implement LOOK algorithm
        if self.direct == "up":
            above = [f for f in request_floors if f > self.floor]
            if above:
                self.floor = min(above)  # Next floor with a request above
            else:
                self.direct = "down"  # Reverse direction
                self.floor = max(request_floors) if request_floors else self.floor
        else:
            below = [f for f in request_floors if f < self.floor]
            if below:
                self.floor = max(below)  # Next floor with a request below
            else:
                self.direct = "up"  # Reverse direction
                self.floor = min(request_floors) if request_floors else self.floor
        
        self.floors_visited += 1

    def register_customer(self, customer):
        self.reg_list.append(customer)
        customer.indicator = 1  # Customer is now inside
        self.internal_requests.add(customer.going_floor)
        print(f"  C{customer.ident} pressed INTERNAL button for {customer.going_floor}")

    def cancel_customer(self, customer):
        self.reg_list.remove(customer)
        customer.indicator = 0  # Customer exits
        customer.fin = 1  # Customer journey complete
        self.internal_requests.discard(customer.going_floor)

def promote_long_waits():
    global current_time, WAIT_THRESHOLD
    
    # Promote long-waiting up requests
    for floor in up_queue.get_all()[:]:
        if floor in up_queue_times:
            wait_time = current_time - up_queue_times[floor]
            if wait_time >= WAIT_THRESHOLD:
                up_queue.remove(floor)
                del up_queue_times[floor]
                priority_floors.enqueue(floor, priority=-wait_time)
                print(f"\n⚠️ PROMOTION: Floor {floor} (waiting {wait_time} units)")
                print(f"   Moved from UP queue to priority")

    # Promote long-waiting down requests
    for floor in down_queue.get_all()[:]:
        if floor in down_queue_times:
            wait_time = current_time - down_queue_times[floor]
            if wait_time >= WAIT_THRESHOLD:
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
        while any(not c.fin for c in self.customers):  # Continue until all customers are served
            direction = "↑" if self.elevator.direct == "up" else "↓"
            print(f"\n=== Floor {self.elevator.floor} {direction} [Time: {current_time}] ===")
            print(f"Active internal requests: {self.elevator.internal_requests}")
            
            current_floor = self.elevator.floor
            handled_external = False
            handled_internal = False

            # Handle priority external calls first
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
                # Handle regular external calls based on direction
                if self.elevator.direct == "up" and up_queue.contains(current_floor):
                    print(f"\n⬆️ EXTERNAL CALL: Up Request at {current_floor}")
                    served = []
                    for c in self.customers:
                        if c.on_floor == current_floor and not c.indicator and c.direction == "up":
                            served.append(f"C{c.ident}")
                            self.elevator.register_customer(c)
                    if served:
                        print(f"  Boarded: {', '.join(served)}")
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
                    down_queue.remove(current_floor)
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

            # Log the reason for stopping
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
        self.indicator = 0  # 0: outside, 1: inside
        self.fin = 0  # 0: not finished, 1: finished
        self.on_floor = random.randint(1, num_of_floors)
        
        # Ensure destination differs from current floor
        while True:
            self.going_floor = random.randint(1, num_of_floors)
            if self.going_floor != self.on_floor:
                break
        
        self.direction = 'up' if self.going_floor > self.on_floor else 'down'
        
        # Assign request to appropriate queue
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

# ----------------- MAIN PROGRAM -----------------
num_customers = int(input("Enter number of customers: "))
num_floors = int(input("Enter number of floors: "))

customers = [Customer(i+1, num_floors) for i in range(num_customers)]
elevator = Elevator(num_floors)
building = Building(num_floors, customers, elevator)

print("\n======== SIMULATION START ========")
building.run()
building.output()
