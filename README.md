# Elevator Scheduling Simulation

A Python simulation that compares two classic elevator scheduling algorithms — **SCAN** and **LOOK** — with a real-time animated GUI and an efficiency analysis module. Built with custom data structures from scratch (no `heapq`, no `collections.deque`).

## What it does

- Simulates a 10-floor building with multiple customers, each waiting on a floor and heading to a destination
- Runs either SCAN or LOOK scheduling to move the elevator and pick up/drop off passengers
- Promotes passengers who have been waiting too long to a priority queue, so no one gets stuck
- Visualises everything live in a Tkinter GUI — floor positions, waiting passengers, active requests, and a colour-coded event log
- Compares both algorithms on the same customer data and plots wait time, service time, and total movements side by side

## Algorithms

**SCAN** moves floor by floor in one direction, reversing only when it hits the top or bottom — like a lift that sweeps the whole building before coming back.

**LOOK** is smarter: it only goes as far as the furthest request in the current direction, then reverses — skipping empty floors at the ends.

Both use the same priority queue system: if a floor has been waiting longer than a threshold (5 time units), it gets promoted to priority so the elevator stops there regardless of direction.

## Project structure

```
├── Data_Structure.py       # Queue, Heap, PriorityQueue — all built from scratch
│
├── ScanLiftScheduler.py    # SCAN: Elevator, Customer, Building classes
├── Scan_System.py          # SCAN simulation logic (used by GUI)
├── ScanGui_Design.py       # SCAN GUI
├── Scan_main.py            # Entry point for SCAN GUI
├── Scan_Efficiency.py      # SCAN efficiency metrics + chart
│
├── LookLiftScheduler.py    # LOOK: Elevator, Customer, Building classes
├── Look_System.py          # LOOK simulation logic (used by GUI)
├── LookGui_Design.py       # LOOK GUI
├── Look_main.py            # Entry point for LOOK GUI
├── Look_Efficiency.py      # LOOK efficiency metrics + chart
│
├── MyLift_Efficiency.py    # Head-to-head comparison: SCAN vs LOOK vs custom algorithm
└── customers.txt           # Input file (on_floor going_floor per line)
```

## Running it

**Requirements:** Python 3, Tkinter (usually bundled with Python), Matplotlib

```bash
pip install matplotlib
```

**SCAN simulation:**
```bash
python Scan_main.py
```

**LOOK simulation:**
```bash
python Look_main.py
```

**Side-by-side algorithm comparison:**
```bash
python MyLift_Efficiency.py
```

When the GUI opens, it will default to `customers.txt` in the same directory. You can change the path or edit the file directly.

## Customer input format

Each line in `customers.txt` is one customer request:

```
on_floor  going_floor
```

Example:
```
1 5
2 8
3 10
```

Floors 1 and 10 are treated as **priority floors** — customers there are picked up first.

## GUI controls

- **Start / Pause** — runs the simulation automatically at the chosen speed
- **Step** — advances one time unit at a time, useful for stepping through the logic
- **Speed slider** — controls how fast the auto-run goes (50ms to 2000ms per step)
- **Event log** — colour-coded: priority calls in yellow, external calls in teal, internal destinations in orange

## Data structures

Everything is implemented manually in `Data_Structure.py`:

- **Queue** — linked list with enqueue, dequeue, contains, remove, get\_all
- **Heap** — min-heap with percolate up/down
- **PriorityQueue** — wraps the heap, uses a timestamp to break ties between equal-priority items

## Efficiency metrics

Each efficiency script calculates:
- **Average wait time** — time from a customer appearing to boarding the elevator
- **Average service time** — time from boarding to reaching their destination
- **Total floors visited** — how many floor movements the elevator made

`MyLift_Efficiency.py` runs all three algorithms and plots bar charts comparing them.
