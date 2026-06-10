import tkinter as tk
from LookGui_Design import ElevatorGUI
from tkinter import ttk, messagebox
from collections import defaultdict
import os

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