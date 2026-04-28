from dotenv import load_dotenv
import os
import sys
import eel


@eel.expose
def run_algorithm(algorithm, code, input_data):
    return f"Ran {algorithm}\nInput: {input_data}\n\nDetected: O(n)"


def main():
    load_dotenv()
    eel.init("web")
    eel.start("index.html", size=(1400, 850), port=8000)


if __name__ == "__main__":
    main()
