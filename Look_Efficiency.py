import os
import matplotlib.pyplot as plt
from LookLiftScheduler import Customer, Building, Elevator  

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

#======================Main=====================
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

# Initialize system components
building = Building(num_floors)
elevator = Elevator(num_floors)
customers = []

# Create customers properly
for i, (on_floor, going_floor) in enumerate(customer_data, 1):
    customers.append(Customer(
        ID=i,
        on_floor=on_floor,
        going_floor=going_floor,
        building=building,
        gui_log=None
    ))

# After creating customers and elevator:
print("\n======== SIMULATION START ========")

# Initialize building time
building.current_time = 0

# Run simulation until all customers are delivered
while not all(c.fin for c in customers):
    current_floor = elevator.floor
    
    # --- Handle EXTERNAL calls (boarding) ---
    handled_external = False
    
    # Priority floor handling
    if building.priority_floors.contains(current_floor):
        for customer in customers:
            if (customer.on_floor == current_floor 
                and not customer.indicator 
                and not customer.fin):
                elevator.register_customer(customer, building)
                customer.boarding_time = building.current_time
        building.priority_floors.remove(current_floor)
        handled_external = True
    else:
        # Regular queue handling
        if elevator.direct == "up" and building.up_queue.contains(current_floor):
            for customer in customers:
                if (customer.on_floor == current_floor 
                    and not customer.indicator 
                    and not customer.fin 
                    and customer.direction == "up"):
                    elevator.register_customer(customer, building)
                    customer.boarding_time = building.current_time
            building.up_queue.remove(current_floor)
            handled_external = True
        elif elevator.direct == "down" and building.down_queue.contains(current_floor):
            for customer in customers:
                if (customer.on_floor == current_floor 
                    and not customer.indicator 
                    and not customer.fin 
                    and customer.direction == "down"):
                    elevator.register_customer(customer, building)
                    customer.boarding_time = building.current_time
            building.down_queue.remove(current_floor)
            handled_external = True

    # --- Handle INTERNAL exits ---
    exited_customers = []
    for customer in elevator.reg_list[:]:  # Iterate over a copy
        if customer.going_floor == current_floor:
            elevator.cancel_customer(customer)
            customer.exit_time = building.current_time
            customer.fin = 1  # Mark as delivered
            exited_customers.append(customer)
    
    # Remove exited customers from elevator
    for customer in exited_customers:
        if customer in elevator.reg_list:
            elevator.reg_list.remove(customer)

    # --- Move elevator and increment time ---
    elevator.move(building)
    building.promote_long_waits()

    # Optional: Print progress
    print(f"Time: {building.current_time}, Floor: {elevator.floor}, Direction: {elevator.direct}")

# Now calculate metrics
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