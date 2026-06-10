import tkinter as tk
from tkinter import ttk, messagebox
from Scan_System import ElevatorSystem  
from collections import defaultdict

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