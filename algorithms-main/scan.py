#!/usr/bin/env python3

import threading
import time
import heapq
from collections import deque

# How long (in seconds) a request can wait in the normal queue before getting "promoted"
WAIT_THRESHOLD = 10


class Request:
    """
    Represents a request for an elevator.
    'floor': The floor where passenger is waiting (or needs to go).
    'priority': Smaller number means higher priority (handled first).
    """
    def __init__(self, floor, priority=0):
        self.floor = floor
        self.priority = priority
        # Track creation time so we can measure how long this request waits
        self.creation_time = time.time()

    def __lt__(self, other):
        """For priority comparison in a min-heap."""
        return self.priority < other.priority

    def __repr__(self):
        return f"(floor={self.floor}, priority={self.priority})"


class Elevator:
    """
    A simple elevator that moves one floor at a time in a separate thread.
    Uses a SCAN-like approach for normal requests, and a min-heap for priority requests.
    """
    def __init__(self, elevator_id, start_floor=0, top_floor=20, direction='up'):
        self.elevator_id = elevator_id
        self.current_floor = start_floor
        self.top_floor = top_floor
        self.bottom_floor = 0
        self.direction = direction  # 'up' or 'down'

        # Normal requests (FIFO)
        self.request_queue = deque()
        # Priority requests (min-heap)
        self.priority_requests = []

        # Stats
        self.seek_distance = 0
        self.seek_sequence = []

        self._stop_event = threading.Event()
        self._lock = threading.Lock()  # Protects request structures

    def add_request(self, request):
        """
        Thread-safe addition of a new request to the elevator.
        Priority != 0 => put in min-heap; else => normal queue.
        """
        with self._lock:
            if request.priority != 0:
                heapq.heappush(self.priority_requests, request)
            else:
                self.request_queue.append(request)

    def _promote_requests_if_needed(self):
        """
        Check all normal (FIFO) requests to see how long they've waited.
        If any have waited >= WAIT_THRESHOLD, promote them to the priority queue
        (by giving them a negative priority).
        """
        with self._lock:
            now = time.time()
            new_normal_queue = deque()

            while self.request_queue:
                req = self.request_queue.popleft()
                waited = now - req.creation_time

                if waited >= WAIT_THRESHOLD:
                    # Promote request by setting a negative priority
                    req.priority = -1
                    heapq.heappush(self.priority_requests, req)
                    print(f"[Elevator {self.elevator_id}] Promoting request {req} (waited {waited:.1f}s)")
                else:
                    new_normal_queue.append(req)

            self.request_queue = new_normal_queue

    def get_next_target_floor(self):
        """
        Returns the floor the elevator should move toward next, based on:
          - If priority requests exist, serve the top priority request first.
          - Else use a minimal SCAN approach for normal requests.
        If no requests, returns None.
        """
        with self._lock:
            # 1) If we have priority requests, pick the highest priority (smallest .priority)
            if self.priority_requests:
                return self.priority_requests[0].floor

            # 2) If no priority requests, check normal queue
            if not self.request_queue:
                return None

            floors = [r.floor for r in self.request_queue]
            below = [f for f in floors if f < self.current_floor]
            above = [f for f in floors if f > self.current_floor]
            below.sort()
            above.sort()

            if self.direction == 'up':
                if above:
                    return above[0]  # smallest above
                else:
                    # No above floors, reverse direction
                    self.direction = 'down'
                    if below:
                        return below[-1]  # largest below
                    else:
                        return None
            else:
                # direction == 'down'
                if below:
                    return below[-1]  # largest below
                else:
                    self.direction = 'up'
                    if above:
                        return above[0]
                    else:
                        return None

    def move_one_floor_toward(self, target):
        """
        Move exactly one floor toward 'target' (if it's not None).
        Return True if arrived at target, else False.
        """
        if target is None:
            return True  # No move needed

        if target == self.current_floor:
            return True  # Already there

        step = 1 if target > self.current_floor else -1
        self.current_floor += step
        self.seek_distance += abs(step)
        self.seek_sequence.append(self.current_floor)
        return (self.current_floor == target)

    def serve_floor_if_arrived(self, floor):
        """
        If we've arrived at 'floor', remove all requests for that floor.
        """
        with self._lock:
            # Remove matching requests from priority queue
            self.priority_requests = [req for req in self.priority_requests if req.floor != floor]
            heapq.heapify(self.priority_requests)

            # Remove matching requests from normal queue
            new_q = deque()
            while self.request_queue:
                req = self.request_queue.popleft()
                if req.floor != floor:
                    new_q.append(req)
            self.request_queue = new_q

    def run_elevator(self):
        """
        Main method for the elevator's thread:
          - Continuously pick a target floor
          - Move one floor at a time
          - Sleep between steps for "parallel" effect
          - Stop if _stop_event is set
        """
        print(f"[Elevator {self.elevator_id}] Starting at floor {self.current_floor}, direction={self.direction}")

        while not self._stop_event.is_set():
            # 1) First, check if any requests waited too long -> promote them
            self._promote_requests_if_needed()

            # 2) Get the next target floor
            target_floor = self.get_next_target_floor()

            # Determine if this is a priority request (for printing info).
            # We do this under the same lock we used to get the next target.
            is_priority = False
            with self._lock:
                if self.priority_requests and target_floor == self.priority_requests[0].floor:
                    is_priority = True

            if target_floor is None:
                # No requests, just sleep
                time.sleep(1)
                continue

            # 3) Move one step toward target
            arrived = self.move_one_floor_toward(target_floor)

            # Print out a message, including whether this is a priority request or not
            if is_priority:
                print(f"[Elevator {self.elevator_id}] (PRIORITY) Floor={self.current_floor}, "
                      f"Target={target_floor}, Distance={self.seek_distance}")
            else:
                print(f"[Elevator {self.elevator_id}] Floor={self.current_floor}, "
                      f"Target={target_floor}, Distance={self.seek_distance}")

            # 4) If arrived, serve it
            if arrived:
                self.serve_floor_if_arrived(target_floor)
                print(f"[Elevator {self.elevator_id}] Served floor {target_floor}.")

            time.sleep(1)  # Let other elevator move in the meantime

        print(f"[Elevator {self.elevator_id}] Stopped. Final floor={self.current_floor}, Distance={self.seek_distance}.")

    def stop(self):
        """Signal the elevator's thread to stop."""
        self._stop_event.set()

    def __repr__(self):
        return (f"Elevator {self.elevator_id}: floor={self.current_floor}, "
                f"direction={self.direction}, distance={self.seek_distance}, "
                f"normalQ={list(self.request_queue)}, priorityQ={list(self.priority_requests)}")


class Dispatcher:
    """
    A simple dispatcher that assigns new requests (floor)
    to whichever elevator is closer.
    If there's a tie, pick Elevator A for simplicity.
    """
    def __init__(self, elevatorA, elevatorB):
        self.elevatorA = elevatorA
        self.elevatorB = elevatorB

    def assign_request(self, floor):
        distA = abs(self.elevatorA.current_floor - floor)
        distB = abs(self.elevatorB.current_floor - floor)
        if distA <= distB:
            self.elevatorA.add_request(Request(floor, priority=0))
            print(f"[Dispatcher] Assigned floor={floor} to Elevator A.")
        else:
            self.elevatorB.add_request(Request(floor, priority=0))
            print(f"[Dispatcher] Assigned floor={floor} to Elevator B.")


def user_input_thread(dispatcher, elevatorA, elevatorB):
    """
    Continuously reads user input in the format:
      floor
    Example: "10" => floor=10
    'exit' => stop all.
    """
    print("[Input Thread] Enter floor requests (example: '10')")
    print("[Input Thread] Type 'exit' to stop.\n")

    while True:
        line = input("Request> ").strip().lower()
        if not line:
            continue
        if line == "exit":
            print("[Input Thread] Exiting. Stopping all elevators...")
            elevatorA.stop()
            elevatorB.stop()
            break
        try:
            floor = int(line)
        except ValueError:
            print("[Input Thread] Floor must be an integer. Try again.")
            continue

        dispatcher.assign_request(floor)


def main():
    # Create two elevators
    elevatorA = Elevator(elevator_id='A', start_floor=0, top_floor=15, direction='up')
    elevatorB = Elevator(elevator_id='B', start_floor=15, top_floor=15, direction='down')

    # Create a dispatcher to assign requests to whichever elevator is closer
    dispatcher = Dispatcher(elevatorA, elevatorB)

    # Launch threads for each elevator
    elevA_thread = threading.Thread(target=elevatorA.run_elevator, daemon=True)
    elevB_thread = threading.Thread(target=elevatorB.run_elevator, daemon=True)

    # Launch user input thread
    input_thread = threading.Thread(target=user_input_thread, args=(dispatcher, elevatorA, elevatorB), daemon=True)

    elevA_thread.start()
    elevB_thread.start()
    input_thread.start()

    # Wait for user input thread to end (user types "exit")
    input_thread.join()

    # Then wait for elevator threads to stop
    elevA_thread.join()
    elevB_thread.join()

    print("\n=== FINAL ELEVATOR STATES ===")
    print(elevatorA)
    print(elevatorB)
    print("\nDone.")


if __name__ == "__main__":
    main()
