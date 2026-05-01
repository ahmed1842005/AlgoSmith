from bridge_fit import get_performance_report
from drow import plot_complexity_graph

if __name__ == "__main__":
    code_input = """
def my_algorithm(arr):
    pass
        
"""


    
   
    report = get_performance_report(code_input)
    
    if "error" in report:
        print(f"❌ {report['error']}")
    else:
        print(f" {report['detected']} ({report['confidence']}%)")
        
        
        print("The Graph")
        plot_complexity_graph(report)