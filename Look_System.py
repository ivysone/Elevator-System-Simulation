from Data_Structure import Queue, PriorityQueue
from LookLiftScheduler import Building,Elevator,Customer
from collections import defaultdict


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