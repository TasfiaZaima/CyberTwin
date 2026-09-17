from database.setup import initialize_from_config
from simulation.service import simulate_all
from twin.baseline import train_baseline
from tests.test_database import output_path

def test_normal_traffic_creates_baseline():
    database=initialize_from_config(database_path=output_path("baseline.db"))
    simulate_all(database,3)
    baseline=train_baseline(database,"camera-01")
    assert baseline["connections_per_minute"]["mean"] > 0
    assert len(database.baselines("camera-01")) == 10

