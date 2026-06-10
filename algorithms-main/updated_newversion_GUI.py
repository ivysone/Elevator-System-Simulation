import tkinter as tk
from tkinter import ttk, messagebox
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
        return node.data if node else None

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
        building.current_time += 1

        external_floors = set(building.up_queue.get_all()) \
                          .union(building.down_queue.get_all()) \
                          .union(node.data for node in building.priority_floors.heap.heap)

        request_floors = external_floors.union(self.internal_requests)
        if not request_floors:
            return

        if self.direct == "up":
            above = [f for f in request_floors if f > self.floor]
            if above:
                self.floor += 1
            else:
                self.direct = "down"
                below = [f for f in request_floors if f < self.floor]
                if below:
                    self.floor -= 1
        else:
            below = [f for f in request_floors if f < self.floor]
            if below:
                self.floor -= 1
            else:
                self.direct = "up"
                above = [f for f in request_floors if f > self.floor]
                if above:
                    self.floor += 1

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
        self.going_floor = going_floor
        self.direction = 'up' if self.going_floor > self.on_floor else 'down'

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

# ------------------ ELEVATOR SYSTEM ------------------
class ElevatorSystem:
    def __init__(self, floors, customer_data_list, gui):
        self.gui = gui
        self.building = Building(floors)
        self.elevator = Elevator(floors)
        self.customers = []
        self.finished = False

        for i, (on_f, go_f) in enumerate(customer_data_list, start=1):
            cust = Customer(i, on_f, go_f, self.building, gui_log=self.gui.log_message)
            self.customers.append(cust)

    def step(self):
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

        exits = []
        for cust in e.reg_list[:]:
            if cust.going_floor == curr_floor:
                self.gui.log_message(f"\n🎯 INTERNAL DESTINATION REACHED: Floor {curr_floor}")
                exits.append(f"C{cust.ident}")
                e.cancel_customer(cust)
        if exits:
            self.gui.log_message(f"  Exited: {', '.join(exits)}")
            handled_internal = True

        if handled_external and handled_internal:
            self.gui.log_message("\nℹ️ Stopping for both EXTERNAL and INTERNAL calls")
        elif handled_external:
            self.gui.log_message("\nℹ️ Stopping primarily for EXTERNAL call")
        elif handled_internal:
            self.gui.log_message("\nℹ️ Stopping primarily for INTERNAL call")

        e.move(b)
        b.promote_long_waits(gui_log=self.gui.log_message)

    def generate_final_report(self):
        self.gui.log_message("\n===== FINAL REPORT =====")
        self.gui.log_message(f"Total elevator movements: {self.elevator.floors_visited}")
        self.gui.log_message("\nCustomer Details:")
        for c in sorted(self.customers, key=lambda x: x.ident):
            status = "DELIVERED" if c.fin else "WAITING"
            self.gui.log_message(f"  [C{c.ident}] {c.on_floor} → {c.going_floor} ({status})")
            self.gui.log_message("-" * 40)

# ------------------ ENHANCED ELEVATOR GUI ------------------
class ElevatorGUI:
    def __init__(self, root, floors, customer_data_list):
        self.root = root
        self.root.title("Elevator Simulation Suite")
        self.root.geometry("1300x850")
        self.num_floors = floors

        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0')
        self.style.configure('TButton', font=('Helvetica', 10))
        self.style.configure('Status.TLabel', font=('Helvetica', 10, 'bold'), background='#f0f0f0')

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.viz_frame = ttk.Frame(self.main_frame)
        self.viz_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        self.create_controls()
        self.create_status_panel()
        self.create_elevator_canvas()
        self.create_log_panel()

        self.system = ElevatorSystem(floors, customer_data_list, self)
        self.sim_running = False
        self.update_status()

    def create_controls(self):
        control_container = ttk.LabelFrame(self.control_frame, text="Simulation Controls")
        control_container.pack(pady=10, fill=tk.X)

        self.start_btn = ttk.Button(control_container, text="▶ Start", command=self.toggle_simulation)
        self.start_btn.pack(pady=5, fill=tk.X)

        self.step_btn = ttk.Button(control_container, text="Step ▶▶", command=self.step_simulation)
        self.step_btn.pack(pady=5, fill=tk.X)

        ttk.Label(control_container, text="Simulation Speed (ms):").pack(pady=5)
        self.speed_slider = ttk.Scale(control_container, from_=50, to=2000, orient=tk.HORIZONTAL, value=1000)
        self.speed_slider.pack(pady=5, fill=tk.X)

    def create_status_panel(self):
        status_container = ttk.LabelFrame(self.control_frame, text="Current Status")
        status_container.pack(pady=10, fill=tk.X)

        label_width = 15
        value_width = 6

        self.status_vars = {
            'floor': tk.StringVar(value="1"),
            'direction': tk.StringVar(value="↑"),
            'passengers': tk.StringVar(value="0"),
            'movements': tk.StringVar(value="0"),
            'requests': tk.StringVar(value="None")
        }

        ttk.Label(status_container, text="Current Floor:", style='Status.TLabel', width=label_width)\
            .grid(row=0, column=0, sticky=tk.W, padx=5, pady=4)
        ttk.Label(status_container, textvariable=self.status_vars['floor'], width=value_width)\
            .grid(row=0, column=1, sticky=tk.E, padx=5, pady=4)

        ttk.Label(status_container, text="Direction:", style='Status.TLabel', width=label_width)\
            .grid(row=1, column=0, sticky=tk.W, padx=5, pady=4)
        ttk.Label(status_container, textvariable=self.status_vars['direction'], width=value_width)\
            .grid(row=1, column=1, sticky=tk.E, padx=5, pady=4)

        ttk.Label(status_container, text="Passengers:", style='Status.TLabel', width=label_width)\
            .grid(row=2, column=0, sticky=tk.W, padx=5, pady=4)
        ttk.Label(status_container, textvariable=self.status_vars['passengers'], width=value_width)\
            .grid(row=2, column=1, sticky=tk.E, padx=5, pady=4)

        ttk.Label(status_container, text="Movements:", style='Status.TLabel', width=label_width)\
            .grid(row=3, column=0, sticky=tk.W, padx=5, pady=4)
        ttk.Label(status_container, textvariable=self.status_vars['movements'], width=value_width)\
            .grid(row=3, column=1, sticky=tk.E, padx=5, pady=4)

        ttk.Label(status_container, text="Active Requests:", style='Status.TLabel', width=label_width)\
            .grid(row=4, column=0, sticky=tk.W, padx=5, pady=4)
        ttk.Label(status_container, textvariable=self.status_vars['requests'], width=value_width)\
            .grid(row=4, column=1, sticky=tk.E, padx=5, pady=4)

    def create_elevator_canvas(self):
        screen_height = self.root.winfo_screenheight()
        margin = 250
        available_height = screen_height - margin
        self.floor_height = available_height // self.num_floors
        self.canvas_width = 800
        self.canvas_height = self.floor_height * self.num_floors

        self.canvas = tk.Canvas(self.viz_frame, bg='#ffffff', width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack(pady=5, padx=5)
        self.draw_modern_building()

    def draw_modern_building(self):
        for floor in range(1, self.num_floors + 1):
            y_pos = self.canvas_height - (floor * self.floor_height)
            self.canvas.create_rectangle(0, y_pos, self.canvas_width, y_pos + self.floor_height,
                                         fill='#f8f9fa', outline='#dee2e6')
            self.canvas.create_text(30, y_pos + self.floor_height / 2,
                                    text=f"FLOOR {floor}", anchor=tk.W,
                                    font=('Helvetica', 11, 'bold'), fill='#6c757d')
            self.canvas.create_rectangle(550, y_pos + 10, 720, y_pos + self.floor_height - 10,
                                         fill='#e9ecef', outline='#ced4da', width=2)
            self.canvas.create_rectangle(70, y_pos + 20, 220, y_pos + self.floor_height - 20,
                                         fill='#e9ecef', outline='#ced4da')
            self.canvas.create_text(80, y_pos + 30, text="▲", anchor=tk.W,
                                    fill='#2a9d8f', font=('Helvetica', 14))
            self.canvas.create_text(120, y_pos + 30, text="▼", anchor=tk.W,
                                    fill='#e76f51', font=('Helvetica', 14))

    def create_log_panel(self):
        log_container = ttk.LabelFrame(self.control_frame, text="Event Log")
        log_container.pack(pady=10, fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_container, height=15, width=40,
                                bg='#1a1a1a', fg='#ffffff', insertbackground='white')
        vsb = ttk.Scrollbar(log_container, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.log_text.tag_config('priority', foreground='#e9c46a')
        self.log_text.tag_config('external', foreground='#2a9d8f')
        self.log_text.tag_config('internal', foreground='#e76f51')
        self.log_text.tag_config('movement', foreground='#a2d2ff')
        self.log_text.tag_config('status', foreground='#8ac926')

    def update_visualization(self):
        self.canvas.delete("dynamic")
        e = self.system.elevator
        self.draw_elevator(e.floor, e.direct)
        self.draw_passengers()
        self.highlight_active_floors()

    def draw_elevator(self, current_floor, direction):
        y_base = self.canvas_height - (current_floor * self.floor_height)
        self.canvas.create_rectangle(560, y_base + 20, 710, y_base + self.floor_height - 20,
                                     fill='#bde0fe', outline='#219ebc', width=2, tags="dynamic")
        indicator_color = '#023e8a' if direction == 'up' else '#e63946'
        self.canvas.create_oval(660, y_base + 30, 680, y_base + 50,
                                fill=indicator_color, tags="dynamic")
        arrow = "↑" if direction == 'up' else "↓"
        self.canvas.create_text(670, y_base + 40, text=arrow,
                                fill='white', font=('Helvetica', 12), tags="dynamic")

    def draw_passengers(self):
        e = self.system.elevator
        for i, p in enumerate(e.reg_list):
            x = 570 + (i % 3) * 45
            y = self.canvas_height - (e.floor * self.floor_height) + 30 + (i // 3) * 45
            self.canvas.create_oval(x, y, x + 30, y + 30, fill='#8ecae6',
                                    tags=("dynamic", f"pass_{p.ident}"))
            self.canvas.create_text(x + 15, y + 15, text=str(p.ident),
                                    tags=("dynamic", f"pass_{p.ident}"))
        waiting = defaultdict(lambda: {'up': [], 'down': []})
        for c in self.system.customers:
            if not c.indicator and not c.fin:
                waiting[c.on_floor][c.direction].append(c)
        for floor, directions in waiting.items():
            y_base = self.canvas_height - (floor * self.floor_height)
            for dir_idx, direction in enumerate(['up', 'down']):
                x_start = 80 if direction == 'up' else 130
                for i, p in enumerate(directions[direction]):
                    x = x_start + i * 40
                    y = y_base + 40 + dir_idx * 30
                    self.canvas.create_rectangle(x, y, x + 25, y + 25,
                                                 fill='#ffb4a2', tags=("dynamic", f"pass_{p.ident}"))
                    self.canvas.create_text(x + 12.5, y + 12.5, text=str(p.ident),
                                            tags=("dynamic", f"pass_{p.ident}"))

    def highlight_active_floors(self):
        active_floors = set()
        active_floors.update(self.system.building.up_queue.get_all())
        active_floors.update(self.system.building.down_queue.get_all())
        active_floors.update(n.data for n in self.system.building.priority_floors.heap.heap)
        for floor in active_floors:
            y_base = self.canvas_height - (floor * self.floor_height)
            self.canvas.create_rectangle(0, y_base, self.canvas_width, y_base + self.floor_height,
                                         outline='#ffd700', width=3, tags="dynamic")

    def update_status(self):
        e = self.system.elevator
        self.status_vars['floor'].set(e.floor)
        self.status_vars['direction'].set("↑" if e.direct == 'up' else "↓")
        self.status_vars['passengers'].set(len(e.reg_list))
        self.status_vars['movements'].set(e.floors_visited)
        active_reqs = []
        if not self.system.building.priority_floors.is_empty():
            active_reqs.append("Priority")
        if not self.system.building.up_queue.is_empty():
            active_reqs.append("Up")
        if not self.system.building.down_queue.is_empty():
            active_reqs.append("Down")
        self.status_vars['requests'].set(", ".join(active_reqs) or "None")

    def log_message(self, message):
        tag = 'status'
        if 'PROMOTION' in message:
            tag = 'priority'
        elif 'EXTERNAL' in message:
            tag = 'external'
        elif 'INTERNAL' in message:
            tag = 'internal'
        elif 'MOVING' in message:
            tag = 'movement'
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def toggle_simulation(self):
        if not self.sim_running:
            self.sim_running = True
            self.start_btn.config(text="Pause")
            self.run_simulation_step()
        else:
            self.sim_running = False
            self.start_btn.config(text="Resume")

    def step_simulation(self):
        self.system.step()
        self.update_visualization()
        self.update_status()
        if self.system.finished:
            self.system.generate_final_report()
            messagebox.showinfo("Simulation Complete", "All customers delivered!")

    def run_simulation_step(self):
        if not self.sim_running:
            return
        self.system.step()
        self.update_visualization()
        self.update_status()
        if self.system.finished:
            self.sim_running = False
            self.start_btn.config(text="Start")
            self.system.generate_final_report()
            messagebox.showinfo("Simulation Complete", "All customers delivered!")
            return
        speed = int(self.speed_slider.get())
        self.root.after(speed, self.run_simulation_step)

# ------------------ MAIN / FILE LOADING ------------------
def read_customer_data(file_path):
    customer_list = []
    with open(file_path, 'r') as f:
        for line in f:
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
