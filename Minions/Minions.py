
import logging
import importlib

logging.basicConfig(
    level=logging.WARNING,
    format="[%(asctime)s] [%(levelname)s] [%(threadName)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

VERBOSE = True

CHOICE_MAP = {
    1: "Basic Minions",
    2: "Advanced Minions",
    3: "Speaking Minions",
}

PROCESS_MAP = {
    "Basic Minions":    ("Callers.Basic",    "processInput"),
    "Advanced Minions": ("Callers.Advanced", "processInput"),
    "Speaking Minions": ("Callers.Speaking", "processInput"),
    
}

def selectMinion():
    print("\nAutonomous Minions Demo System\n" + "-" * 30)
    print("Available Minion types:")
    for num, desc in CHOICE_MAP.items():
        print(f"  {num}: {desc}")
    print("-" * 30)
    while True:
        try:
            userChoice = input("\nSelect Minion by number (default: 1): ").strip()
            if not userChoice:
                userChoice = 1
            else:
                userChoice = int(userChoice)
            choiceStr = CHOICE_MAP[userChoice]
            modulePath, funcName = PROCESS_MAP[choiceStr]
            module = importlib.import_module(modulePath)
            if hasattr(module, "MainMinion"):
                fn = getattr(module.MainMinion(), funcName)
            elif hasattr(module, "MainMinion"):
                fn = getattr(module.MainMinion(), funcName)
            else:
                fn = getattr(module, funcName)
            print(f"\n[Selected Minion]: {choiceStr}")
            return fn, choiceStr
        except (ValueError, KeyError, ImportError) as e:
            print(f"Invalid choice or import error: {e}")

if __name__ == "__main__":
    processInput, agent = selectMinion()
    print("-" * 30)
    while True:
        userInput = input("Enter your query (or ':switch' to change Minion type, Enter to exit):\n")
        if userInput.strip() == "":
            print("Goodbye!")
            break
        if userInput.strip().lower() == ":switch":
            processInput, agent = selectMinion()
            print("-" * 30)
            continue
        print(f"\n[User Input]: {userInput}\n")
        try:
            processInput(userInput, VERBOSE)
        except Exception as e:
            logging.exception("Error during processing:")

