import sys
import eel


@eel.expose
def run_algorithm(algorithm, code, input_data):
    return f"Ran {algorithm}\nInput: {input_data}\n\nDetected: O(n)"


def main():
    eel.init("web")
    eel.start("index.html", size=(1400, 850))


if __name__ == "__main__":
    main()