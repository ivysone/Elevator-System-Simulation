from Data_Structure import Queue, PriorityQueue
from collections import defaultdict

class Elevator:
    def __init__(self, num_of_floors):
        self.total_floors = num_of_floors
        self.reg_list = []       # Passengers in elevator
        self.floor = 1           # Current floor
        self.direct = "up"       # Direction: 'up' or 'down'
        self.floors_visited = 0  # Movement counter
        self.internal_requests = set()  # Destinations from passengers

    def move(self, building):
        
        building.current_time += 1
        
        # Get queues from building
        external_floors = set(building.up_queue.get_all()) | \
                         set(building.down_queue.get_all()) | \
                         {node.data for node in building.priority_floors.heap.heap}
        
        request_floors = external_floors.union(self.internal_requests)
        
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


    def register_customer(self, customer, building, gui_log=None):
        self.reg_list.append(customer)
        customer.indicator = 1
        self.internal_requests.add(customer.going_floor)
        if gui_log:
            gui_log(f"  C{customer.ident} pressed INTERNAL button for {customer.going_floor}")

    def cancel_customer(self, customer):
        self.reg_list.remove(customer)
        customer.indicator = 0
        customer.fin = 1
        if customer.going_floor in self.internal_requests:
            self.internal_requests.remove(customer.going_floor)

class Customer:
    def __init__(self, ID, on_floor, going_floor, building, gui_log=None):
        self.ident = ID
        self.indicator = 0  
        self.fin = 0        
        self.on_floor = on_floor
        self.building = building
        self.going_floor = going_floor
        self.direction = 'up' if self.going_floor > self.on_floor else 'down'

        # Time tracking attributes
        self.enqueue_time = building.current_time  # Time when customer appears
        self.boarding_time = None  # Time when customer enters elevator
        self.exit_time = None      # Time when customer exits elevator

        if gui_log:
            gui_log(f"\n🆕 CUSTOMER {self.ident}:")
            gui_log(f"  From floor {self.on_floor} to {self.going_floor}")

        if self.on_floor == 1 or self.on_floor == building.total_floors:
            if gui_log:
                gui_log(f"  Priority floor detected! (Floor {self.on_floor})")
            if not building.priority_floors.contains(self.on_floor):
                building.priority_floors.enqueue(self.on_floor, priority=0)
        else:
            if self.direction == 'up':
                if not building.up_queue.contains(self.on_floor):
                    building.up_queue.enqueue(self.on_floor)
                    building.up_queue_times[self.on_floor] = building.current_time
            else:
                if not building.down_queue.contains(self.on_floor):
                    building.down_queue.enqueue(self.on_floor)
                    building.down_queue_times[self.on_floor] = building.current_time

class Building:
    def __init__(self, num_of_floors=10):
        self.total_floors = num_of_floors
        self.current_time = 0
        self.WAIT_THRESHOLD = 5

        self.up_queue = Queue()
        self.down_queue = Queue()
        self.priority_floors = PriorityQueue()

        self.up_queue_times = {}
        self.down_queue_times = {}

    def promote_long_waits(self, gui_log=None):
        for f in self.up_queue.get_all():
            wait_time = self.current_time - self.up_queue_times.get(f, 0)
            if wait_time >= self.WAIT_THRESHOLD:
                self.up_queue.remove(f)
                del self.up_queue_times[f]
                self.priority_floors.enqueue(f, priority=-wait_time)
                if gui_log:
                    gui_log(f"\n⚠️ PROMOTION: Floor {f} (waiting {wait_time} units)")
                    gui_log("   Moved from UP queue to priority")
        for f in self.down_queue.get_all():
            wait_time = self.current_time - self.down_queue_times.get(f, 0)
            if wait_time >= self.WAIT_THRESHOLD:
                self.down_queue.remove(f)
                del self.down_queue_times[f]
                self.priority_floors.enqueue(f, priority=-wait_time)
                if gui_log:
                    gui_log(f"\n⚠️ PROMOTION: Floor {f} (waiting {wait_time} units)")
                    gui_log("   Moved from DOWN queue to priority")
