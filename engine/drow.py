import matplotlib.pyplot as plt
import numpy as np
from analyzer_fit import MODELS


def plot_complexity_graph(report, label_to_plot=None):
   
    if "raw_data" not in report or "error" in report:
        print("Error Data Nit Found")
        return

    sizes = report["raw_data"]["sizes"]
    times = report["raw_data"]["times"]
    
    
    target_label = label_to_plot if label_to_plot else report["detected"]
    
    
    try:
        model_data = next(item for item in report["ranking"] if item["label"] == target_label)
    except StopIteration:
        print(f"{target_label} Not Found")
        return

    a_factor = model_data["scale"]

   
    ns_smooth = np.linspace(min(sizes), max(sizes), 100)
    theoretical_values = MODELS[target_label](ns_smooth, a_factor)

   
    plt.figure(figsize=(10, 6))
    plt.scatter(sizes, times, color='red', label='Measured Data (Actual)')
    plt.plot(ns_smooth, theoretical_values,  linestyle='--', color='blue')
    
    plt.title(f"Complexity Curve")
    plt.xlabel("Input Size (n)")
    plt.ylabel("Time (seconds)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()