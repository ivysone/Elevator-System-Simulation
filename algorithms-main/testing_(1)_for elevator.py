import threading
import time

class Elevator:
    def __init__(self, current_floor=0):
        self.current_floor = current_floor
        self.direction = 'up'  # Starts by moving up
        self.requests = []  # List of floor requests
        self.running = True
        self.lock = threading.Lock()  # Lock to prevent race conditions

    def request_elevator(self, floor):
        """Adds a floor request."""
        with self.lock:  # Ensures thread-safe access to requests list
            if floor not in self.requests:
                self.requests.append(floor)
                self.requests.sort()

    def move(self):
        """Moves the elevator continuously while checking requests."""
        while self.running:
            if not self.requests:
                print("No requests. Elevator is idle.")
                time.sleep(2)
                continue

            with self.lock:  # Lock the request list while moving
                if self.direction == 'up':
                    self.requests.sort()
                else:
                    self.requests.sort(reverse=True)

                while self.requests:
                    next_floor = self.requests.pop(0)
                    distance = abs(self.current_floor - next_floor)  # Calculate the distance
                    self._move_elevator(distance)  # Move the elevator realistically
                    self.current_floor = next_floor
                    print(f"Elevator stopped at floor {self.current_floor}")
                    time.sleep(1)

                self.direction = 'down' if self.direction == 'up' else 'up'

    def _move_elevator(self, distance):
        """Simulates the elevator's travel time between floors."""
        # Simulate moving between floors by adding a time delay based on distance
        print(f"Moving {distance} floors...")
        for _ in range(distance):
            time.sleep(1)  # 1 second per floor to simulate real-time movement

    def collect_requests(self):
        """Continuously collects user floor requests."""
        while self.running:
            user_input = input("Enter a floor request (or 'exit' to stop): ")
            if user_input.lower() == 'exit':
                self.running = False
                break
            try:
                floor = int(user_input)
                self.request_elevator(floor)
            except ValueError:
                print("Invalid input. Please enter a floor number.")

# Initialize elevator
elevator = Elevator()

# Start elevator movement in a separate thread
movement_thread = threading.Thread(target=elevator.move)
request_thread = threading.Thread(target=elevator.collect_requests)

movement_thread.start()
request_thread.start()

movement_thread.join()
request_thread.join()

print("Elevator system shutting down.")
