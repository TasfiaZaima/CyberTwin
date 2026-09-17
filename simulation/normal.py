from database.setup import initialize_from_config
from simulation.service import simulate_all
if __name__ == "__main__":
    database = initialize_from_config(); simulate_all(database); print("Generated normal telemetry for all devices")

