import argparse
from database.setup import initialize_from_config
from simulation.service import simulate_window
if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--device",default="camera-01"); args=parser.parse_args()
    print(simulate_window(initialize_from_config(), args.device, 999, True))
