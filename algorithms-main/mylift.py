import random
from datastructures import *

# ----------------- GLOBAL VARIABLES -----------------
request_queue = Queue()
priority_floors = PriorityQueue()
current_time = 0
WAIT_THRESHOLD = 5
request_times = {}
unserved_floors = set()

max_capacity = 5
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
        
        #collecting the customers' requests
        all_requests = set(self.internal_requests)
        for f in request_queue.get_all():
            all_requests.add(f)
        for node in priority_floors.heap.heap:
            all_requests.add(node.data)

        if not all_requests:
            return  #does not move if there are no requests

        '''Special Part of the MyLift: Clustering
        Below are the steps of what clustering is'''
        #step 1: calculate distances of all the requested floors
        distances = {f: abs(self.floor - f) for f in all_requests}
        
        #step 2: it prefers current direction unless overwritten by priority queue
        if self.direct == "up":
            ahead = [f for f in all_requests if f > self.floor]
            if not ahead and all_requests:
                self.direct = "down"
        else:
            ahead = [f for f in all_requests if f < self.floor]
            if not ahead and all_requests:
                self.direct = "up"

        #step 3: find "clusters" or floors that are in consecutive orders
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
        '''If the request floors are [2,3,4,7], the clusters are [2,3,4] and [7]'''

        #step 4: chooses next floor while prioritising nearest using cluster bonus
        min_distance = float('inf')
        next_floor = self.floor
        for f in all_requests:
            distance = distances[f]
            #cluster bonus is floors in cluster * 0.5
            cluster_bonus = 0
            for cluster in clusters:
                if f in cluster and len(cluster) > 1:
                    cluster_bonus = len(cluster) * 0.5
                    break
            effective_distance = distance - cluster_bonus #calculates "effective distance" using cluster bonus
            
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
      # checks if there are more requests than the max capacity
        if len(self.reg_list) < max_capacity:
            self.reg_list.append(customer)
            customer.indicator = 1
            self.internal_requests.add(customer.going_floor)
            print(f"  C{customer.ident} pressed INTERNAL button for {customer.going_floor}")
        else:
            unserved_floors.add(customer.on_floor)
            customer.indicator = 0
            self.internal_requests.discard(customer.going_floor)
            print(f"  🚫 C{customer.ident} could not board (Elevator Full)")
            # Re-enqueue the floor request for unserved passengers
            request_queue.enqueue(customer.on_floor)
            request_times[customer.on_floor] = current_time

    def cancel_customer(self, customer):
        self.reg_list.remove(customer)
        customer.indicator = 0
        customer.fin = 1
        self.internal_requests.discard(customer.going_floor)

        if customer.on_floor in unserved_floors:
            unserved_floors.remove(customer.on_floor)
            request_queue.enqueue(customer.on_floor)

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

            #handling internal requests
            exits = []
            for c in self.elevator.reg_list[:]:
                if c.going_floor == current_floor:
                    print(f"\n🎯 INTERNAL DESTINATION REACHED: Floor {current_floor}")
                    exits.append(f"C{c.ident}")
                    self.elevator.cancel_customer(c)
                    handled_internal = True
            if exits:
                print(f"  Exited: {', '.join(exits)}")

            #handling priority floors
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

            #handling regular requests
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
