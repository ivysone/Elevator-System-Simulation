import tkinter as tk
from tkinter import ttk, messagebox
import time
from collections import defaultdict
import os

# ------------------ DATA STRUCTURES ------------------
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

    # Compare first by priority, then by timestamp
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
        left = 2*index + 1
        right = 2*index + 2
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
        return node.data if node else None

    def is_empty(self):
        return self.heap.is_empty()

    def contains(self, data):
        for node in self.heap.heap:
            if node.data == data:
                return True
        return False

    def remove(self, data):
        # Remove node with matching data, rebuild heap
        for i, node in enumerate(self.heap.heap):
            if node.data == data:
                self.heap.heap.pop(i)
                new_heap = Heap()
                for n in self.heap.heap:
                    new_heap.insert(n)
                self.heap = new_heap
                return

# ------------------ ELEVATOR & BUILDING ------------------
class Elevator:
    def __init__(self, num_of_floors):
        self.total_floors = num_of_floors
        self.reg_list = []       # List of customers in elevator
        self.floor = 1           # Current floor
        self.direct = "up"       # 'up' or 'down'
        self.floors_visited = 0  # Movement count for final report
        self.internal_requests = set()

    def move(self, building):
        """Move elevator one floor at a time toward existing requests."""
        building.current_time += 1

        # Gather external floors from queues
        external_floors = set(building.up_queue.get_all()) \
                          .union(building.down_queue.get_all()) \
                          .union(node.data for node in building.priority_floors.heap.heap)

        # Combine with elevator's internal requests
        request_floors = external_floors.union(self.internal_requests)

        # If no requests, do nothing
        if not request_floors:
            return

        # Move logic (one floor at a time)
        if self.direct == "up":
            above = [f for f in request_floors if f > self.floor]
            if above:
                self.floor += 1  # move up exactly one floor
            else:
                # No floors above, switch direction
                self.direct = "down"
                below = [f for f in request_floors if f < self.floor]
                if below:
                    self.floor -= 1
        else:  # "down"
            below = [f for f in request_floors if f < self.floor]
            if below:
                self.floor -= 1  # move down exactly one floor
            else:
                # No floors below, switch direction
                self.direct = "up"
                above = [f for f in request_floors if f > self.floor]
                if above:
                    self.floor += 1

        self.floors_visited += 1

    def register_customer(self, customer, building, gui_log=None):
        """ Customer boards elevator; register internal request """
        self.reg_list.append(customer)
        customer.indicator = 1
        self.internal_requests.add(customer.going_floor)
        if gui_log:
            gui_log(f"  C{customer.ident} pressed INTERNAL button for {customer.going_floor}")

    def cancel_customer(self, customer):
        """ Customer reached destination; remove from elevator """
        self.reg_list.remove(customer)
        customer.indicator = 0
        customer.fin = 1
        if customer.going_floor in self.internal_requests:
            self.internal_requests.remove(customer.going_floor)

class Customer:
    """
    This version of Customer does NOT pick random floors.
    Instead, you specify them directly (on_floor, going_floor).
    """
    def __init__(self, ID, on_floor, going_floor, building, gui_log=None):
        self.ident = ID
        self.indicator = 0  # 1 if inside elevator
        self.fin = 0        # 1 if delivered
        self.on_floor = on_floor
        self.going_floor = going_floor
        # Determine direction
        self.direction = 'up' if self.going_floor > self.on_floor else 'down'

        # Log creation
        if gui_log:
            gui_log(f"\n🆕 CUSTOMER {self.ident}:")
            gui_log(f"  From floor {self.on_floor} to {self.going_floor}")

        # Priority floors if on 1 or top floor (10 in this case)
        if self.on_floor == 1 or self.on_floor == building.total_floors:
            if gui_log:
                gui_log(f"  Priority floor detected! (Floor {self.on_floor})")
            if not building.priority_floors.contains(self.on_floor):
                building.priority_floors.enqueue(self.on_floor, priority=0)
        else:
            # Normal up/down queues
            if self.direction == 'up':
                if not building.up_queue.contains(self.on_floor):
                    building.up_queue.enqueue(self.on_floor)
                    building.up_queue_times[self.on_floor] = building.current_time
            else:
                if not building.down_queue.contains(self.on_floor):
                    building.down_queue.enqueue(self.on_floor)
                    building.down_queue_times[self.on_floor] = building.current_time

# The Building is always 10 floors in this example.
class Building:
    def __init__(self, num_of_floors=10):
        self.total_floors = num_of_floors
        self.current_time = 0
        self.WAIT_THRESHOLD = 5

        # Queues
        self.up_queue = Queue()
        self.down_queue = Queue()
        self.priority_floors = PriorityQueue()

        # Track wait times
        self.up_queue_times = {}
        self.down_queue_times = {}

    def promote_long_waits(self, gui_log=None):
        """
        Promote floors that waited too long from up/down to priority.
        """
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

# ------------------ ELEVATOR SYSTEM ------------------
class ElevatorSystem:
    def __init__(self, floors, customer_data_list, gui):
        """
        :param floors: Fixed at 10 in this example.
        :param customer_data_list: A list of (on_floor, going_floor) tuples from the text file.
        :param gui: Reference to the GUI for logging and visualization.
        """
        self.gui = gui
        self.building = Building(floors)
        self.elevator = Elevator(floors)
        self.customers = []
        self.finished = False

        # Create customers based on file data
        for i, (on_f, go_f) in enumerate(customer_data_list, start=1):
            cust = Customer(i, on_f, go_f, self.building, gui_log=self.gui.log_message)
            self.customers.append(cust)

    def step(self):
        """
        One iteration of elevator logic:
          1) Serve external calls at current floor
          2) Serve internal calls (arrivals)
          3) Move elevator
          4) Promote long waits
        """
        if all(c.fin for c in self.customers):
            self.finished = True
            return

        b = self.building
        e = self.elevator
        curr_floor = e.floor
        direction_symbol = "↑" if e.direct == "up" else "↓"

        self.gui.log_message(f"\n=== Floor {curr_floor} {direction_symbol} [Time: {b.current_time}] ===")
        self.gui.log_message(f"Active internal requests: {list(e.internal_requests)}")

        handled_external = False
        handled_internal = False

        # ---- External Calls ----
        if b.priority_floors.contains(curr_floor):
            self.gui.log_message(f"\n🔥 EXTERNAL CALL: Priority Floor {curr_floor}")
            served = []
            for c in self.customers:
                if c.on_floor == curr_floor and not c.indicator and not c.fin:
                    served.append(f"C{c.ident}")
                    e.register_customer(c, b, gui_log=self.gui.log_message)
            if served:
                self.gui.log_message(f"  Boarded: {', '.join(served)}")
            else:
                self.gui.log_message("  No waiting customers")
            b.priority_floors.remove(curr_floor)
            handled_external = True

        else:
            if e.direct == "up" and b.up_queue.contains(curr_floor):
                self.gui.log_message(f"\n⬆️ EXTERNAL CALL: Up Request at {curr_floor}")
                served = []
                for c in self.customers:
                    if c.on_floor == curr_floor and not c.indicator and not c.fin and c.direction == "up":
                        served.append(f"C{c.ident}")
                        e.register_customer(c, b, gui_log=self.gui.log_message)
                if served:
                    self.gui.log_message(f"  Boarded: {', '.join(served)}")
                else:
                    self.gui.log_message("  No matching customers")
                b.up_queue.remove(curr_floor)
                handled_external = True

            elif e.direct == "down" and b.down_queue.contains(curr_floor):
                self.gui.log_message(f"\n⬇️ EXTERNAL CALL: Down Request at {curr_floor}")
                served = []
                for c in self.customers:
                    if c.on_floor == curr_floor and not c.indicator and not c.fin and c.direction == "down":
                        served.append(f"C{c.ident}")
                        e.register_customer(c, b, gui_log=self.gui.log_message)
                if served:
                    self.gui.log_message(f"  Boarded: {', '.join(served)}")
                else:
                    self.gui.log_message("  No matching customers")
                b.down_queue.remove(curr_floor)
                handled_external = True

        # ---- Internal Calls (arrivals) ----
        exits = []
        for cust in e.reg_list[:]:
            if cust.going_floor == curr_floor:
                self.gui.log_message(f"\n🎯 INTERNAL DESTINATION REACHED: Floor {curr_floor}")
                exits.append(f"C{cust.ident}")
                e.cancel_customer(cust)
        if exits:
            self.gui.log_message(f"  Exited: {', '.join(exits)}")
            handled_internal = True

        # ---- Logging reason for stop ----
        if handled_external and handled_internal:
            self.gui.log_message("\nℹ️ Stopping for both EXTERNAL and INTERNAL calls")
        elif handled_external:
            self.gui.log_message("\nℹ️ Stopping primarily for EXTERNAL call")
        elif handled_internal:
            self.gui.log_message("\nℹ️ Stopping primarily for INTERNAL call")

        # ---- Move elevator ----
        e.move(b)

        # ---- Promote long waits ----
        b.promote_long_waits(gui_log=self.gui.log_message)

    def generate_final_report(self):
        self.gui.log_message("\n===== FINAL REPORT =====")
        self.gui.log_message(f"Total elevator movements: {self.elevator.floors_visited}")
        self.gui.log_message("\nCustomer Details:")
        for c in sorted(self.customers, key=lambda x: x.ident):
            status = "DELIVERED" if c.fin else "WAITING"
            self.gui.log_message(f"  [C{c.ident}] {c.on_floor} → {c.going_floor} ({status})")
            self.gui.log_message("-" * 40)

# ------------------ MODIFIED GUI CLASS ------------------
class ElevatorGUI:
    def __init__(self, root, floors, customer_data_list):
        self.root = root
        self.root.title("Elevator Simulation GUI")
        self.num_floors = floors
        
        # We'll create a left frame for building and controls,
        # and a right frame for the log.
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Controls frame at the top (left side)
        self.controls_frame = ttk.Frame(self.left_frame)
        self.controls_frame.pack(pady=5)

        # Start button
        self.start_button = ttk.Button(self.controls_frame, text="Start Simulation", 
                                       command=self.start_simulation)
        self.start_button.pack(side=tk.LEFT, padx=5)

        # Canvas below controls (left side)
        self.floor_height = 80
        self.canvas_width = 600
        self.canvas_height = self.floor_height * floors
        self.elevator_width = 60
        self.passenger_size = 20
        
        self.canvas = tk.Canvas(self.left_frame, width=self.canvas_width, 
                                height=self.canvas_height, bg='white')
        self.canvas.pack(pady=5)

        # Log text on the right side with scrollbar
        self.log_frame = ttk.Frame(self.right_frame)
        self.log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_scrollbar = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL)
        self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(self.log_frame, height=30, width=50,
                                yscrollcommand=self.log_scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.log_scrollbar.config(command=self.log_text.yview)

        # Draw initial building
        self.draw_building()
        
        # Create system AFTER GUI elements
        self.system = ElevatorSystem(floors, customer_data_list, self)
        self.sim_running = False

    def draw_building(self):
        # Draw floors from top to bottom
        for floor in range(1, self.num_floors+1):
            y = self.canvas_height - (floor * self.floor_height)
            
            # Floor label
            self.canvas.create_text(
                10, y + self.floor_height/2, 
                text=f"Floor {floor}", anchor=tk.W
            )
            
            # Waiting areas
            self.canvas.create_rectangle(100, y, 300, 
                                         y + self.floor_height, 
                                         outline='gray', fill='#f0f0f0')
            self.canvas.create_text(
                110, y + 10, text="Waiting Area ↑", anchor=tk.NW, fill='darkgreen'
            )
            self.canvas.create_text(
                210, y + 10, text="Waiting Area ↓", anchor=tk.NW, fill='darkred'
            )
            
            # Elevator shaft
            self.canvas.create_rectangle(
                400, y, 400 + self.elevator_width, 
                y + self.floor_height, 
                outline='black'
            )

    def update_visualization(self):
        """
        Redraw elevator & passengers each step.
        """
        self.canvas.delete("passengers")
        self.canvas.delete("elevator")
        
        # Draw elevator at current floor
        e = self.system.elevator
        current_floor = e.floor
        # Compute Y based on current floor
        y = self.canvas_height - (current_floor * self.floor_height) + 10
        self.canvas.create_rectangle(
            400, y, 
            400 + self.elevator_width, y + self.floor_height - 20,
            fill='lightblue', tags="elevator"
        )
        
        # -- Draw passengers inside elevator --
        elevator_x = 410
        elevator_y = y + 10
        for i, passenger in enumerate(e.reg_list):
            px = elevator_x + (i % 3) * (self.passenger_size + 5)
            py = elevator_y + (i // 3) * (self.passenger_size + 5)
            color = self.get_passenger_color(passenger.ident)
            
            self.canvas.create_oval(
                px, py, px + self.passenger_size, py + self.passenger_size,
                fill=color, tags="passengers"
            )
            self.canvas.create_text(
                px + self.passenger_size/2, py + self.passenger_size/2,
                text=str(passenger.ident), tags="passengers"
            )

        # -- Draw waiting passengers on each floor --
        from collections import defaultdict
        waiting_positions = defaultdict(lambda: {'up': 0, 'down': 0})
        for customer in self.system.customers:
            if not customer.indicator and not customer.fin:
                floor = customer.on_floor
                y_floor = self.canvas_height - (floor * self.floor_height) + 20
                direction = customer.direction
                index = waiting_positions[floor][direction]
                waiting_positions[floor][direction] += 1

                if direction == 'up':
                    x = 110 + index * 30
                else:
                    x = 210 + index * 30

                color = self.get_passenger_color(customer.ident)
                self.canvas.create_oval(
                    x, y_floor, x + self.passenger_size, y_floor + self.passenger_size,
                    fill=color, tags="passengers"
                )
                self.canvas.create_text(
                    x + self.passenger_size/2, y_floor + self.passenger_size/2,
                    text=str(customer.ident), tags="passengers"
                )

    def get_passenger_color(self, passenger_id):
        """
        Assign a color based on passenger_id, cycling through some options.
        """
        colors = [
            '#FF0000', '#00FF00', '#0000FF', '#FF00FF', 
            '#00FFFF', '#FFA500', '#800080', '#008000',
            '#800000', '#008080'
        ]
        return colors[passenger_id % len(colors)]

    def start_simulation(self):
        if not self.sim_running:
            self.sim_running = True
            self.start_button.config(text="Running...")
            self.run_simulation_step()

    def run_simulation_step(self):
        """
        One simulation step, repeated every 1 second.
        """
        if not self.sim_running:
            return

        self.system.step()
        self.update_visualization()
        
        # Check if finished
        if self.system.finished:
            self.sim_running = False
            self.start_button.config(text="Start Simulation")
            self.system.generate_final_report()
            messagebox.showinfo("Simulation Complete", "All customers delivered!")
            return

        # Schedule next step in 1000 ms (1 second)
        self.root.after(1000, self.run_simulation_step)

    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()  # Force GUI update for real-time logging

# ------------------ MAIN ------------------
#imp
def read_customer_data(file_path):
    """
    Reads lines from file_path and returns 
    a list of (on_floor, going_floor) pairs.
    """
    customer_list = []
    with open(file_path, 'r') as f:
        for line in f:
            # Ignore empty lines or commented lines
            if not line.strip() or line.startswith('#'):
                continue
            parts = line.strip().split()
            if len(parts) != 2:
                continue
            on_floor, going_floor = int(parts[0]), int(parts[1])
            customer_list.append((on_floor, going_floor))
    return customer_list

def main():
    """
    A simple parameter window that asks for 
    the path to the customers text file.
    The building floors are fixed at 10.
    """
    param_window = tk.Tk()
    param_window.title("Load Customers from File")

    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Create the default path to customers.txt in the script's directory
    default_path = os.path.join(script_dir, "customers.txt")

    tk.Label(param_window, text="Customers File Path:").pack(pady=5)
    file_entry = tk.Entry(param_window, width=30)
    file_entry.pack(pady=5)
    file_entry.insert(0, default_path)  # Set the default to the absolute path

    def start_sim():
        file_path = file_entry.get().strip()
        try:
            customer_data_list = read_customer_data(file_path)
            if not customer_data_list:
                raise ValueError("No valid customer data in file.")
        except Exception as ex:
            messagebox.showerror("Error", f"Could not read file.\n{ex}")
            return

        param_window.destroy()
        root = tk.Tk()
        # Building floors fixed to 10
        ElevatorGUI(root, 10, customer_data_list)
        root.mainloop()

    tk.Button(param_window, text="Start Simulation", command=start_sim).pack(pady=10)
    param_window.mainloop()

if __name__ == "__main__":
    main()
