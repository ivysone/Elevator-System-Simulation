import threading
import time
import random
from datastructures import MinHeap, Queue, bubble_sort

# Global Variables
up_queue = Queue()
down_queue = Queue()
priority_floors = MinHeap()
current_time = 0
WAIT_THRESHOLD = 10
up_queue_times = {}
down_queue_times = {}

class Request:
    def __init__(self, floor, priority=0):
        self.floor = floor
        self.priority = priority
        self.creation_time = time.time()

    def __lt__(self, other):
        return self.priority < other.priority

    def __repr__(self):
        return f"(floor={self.floor}, priority={self.priority})"

class Elevator:
    def __init__(self, elevator_id, start_floor=0, top_floor=10, direction='up'):
        self.elevator_id = elevator_id
        self.current_floor = start_floor
        self.top_floor = top_floor
        self.bottom_floor = 0
        self.direction = direction
        
        self.internal_requests = set()
        self.external_floors = set()
        
        self.seek_distance = 0
        self.seek_sequence = []
        
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def add_request(self, floor, direction):
        with self._lock:
            if direction == 'up':
                up_queue.enqueue(floor)
                up_queue_times[floor] = current_time
            else:
                down_queue.enqueue(floor)
                down_queue_times[floor] = current_time
            print(f"[Elevator {self.elevator_id}] Added request for floor {floor} ({direction}).")

    def promote_priority_requests(self):
        global current_time
        with self._lock:
            for floor, request_time in list(up_queue_times.items()):
                if current_time - request_time > WAIT_THRESHOLD:
                    priority_floors.push(Request(floor, priority=1))
                    del up_queue_times[floor]
                    print(f"[Elevator {self.elevator_id}] Promoted floor {floor} to priority queue.")
            
            for floor, request_time in list(down_queue_times.items()):
                if current_time - request_time > WAIT_THRESHOLD:
                    priority_floors.push(Request(floor, priority=1))
                    del down_queue_times[floor]
                    print(f"[Elevator {self.elevator_id}] Promoted floor {floor} to priority queue.")
    
    def get_next_target_floor(self):
        with self._lock:
            if not priority_floors.is_empty():
                floor = priority_floors.pop().floor
                print(f"[Elevator {self.elevator_id}] Next target from priority queue: {floor}.")
                return floor
            
            if self.direction == 'up':
                if not up_queue.is_empty():
                    return up_queue.dequeue()
                elif not down_queue.is_empty():
                    self.direction = 'down'
                    return down_queue.dequeue()
            else:
                if not down_queue.is_empty():
                    return down_queue.dequeue()
                elif not up_queue.is_empty():
                    self.direction = 'up'
                    return up_queue.dequeue()
            
            return None

    def move_one_floor_toward(self, target):
        if target is None or target == self.current_floor:
            return True
        
        step = 1 if target > self.current_floor else -1
        self.current_floor += step
        self.seek_distance += abs(step)
        self.seek_sequence.append(self.current_floor)
        print(f"[Elevator {self.elevator_id}] Moving to floor {self.current_floor}.")
        return self.current_floor == target

    def serve_floor_if_arrived(self, floor):
        with self._lock:
            if floor in up_queue_times:
                del up_queue_times[floor]
            if floor in down_queue_times:
                del down_queue_times[floor]
            print(f"[Elevator {self.elevator_id}] Served floor {floor}.")

    def run_elevator(self):
        global current_time
        print(f"[Elevator {self.elevator_id}] Starting at floor {self.current_floor}, direction={self.direction}")
        
        while not self._stop_event.is_set():
            self.promote_priority_requests()
            target_floor = self.get_next_target_floor()
            
            if target_floor is None:
                print(f"[Elevator {self.elevator_id}] No pending requests. Waiting...")
                time.sleep(1)
                continue
            
            while self.current_floor != target_floor:
                self.move_one_floor_toward(target_floor)
                time.sleep(1)
            
            self.serve_floor_if_arrived(target_floor)
            current_time += 1
        
        print(f"[Elevator {self.elevator_id}] Stopped. Final floor={self.current_floor}, Distance={self.seek_distance}.")
    
    def stop(self):
        self._stop_event.set()

ran1 = random.randint(0, 10)
ran2 = random.randint(0, 10)
ran3 = random.randint(0, 10)

def main():
    elevator1 = Elevator(elevator_id=1, start_floor=1)
    elevator1_thread = threading.Thread(target=elevator1.run_elevator)
    elevator1_thread.start()

    elevator1.add_request(7, 'up')
    elevator1.add_request(6, 'down')

    time.sleep(20)

    elevator1.stop()
    elevator1_thread.join()

    print(elevator1)

if __name__ == "__main__":
    main()