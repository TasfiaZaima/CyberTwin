from database.setup import initialize_from_config
from simulation.service import simulate_all, simulate_window
from twin.baseline import train_baseline
from tests.test_database import output_path

def test_anomaly_scores_higher_than_normal():
    database=initialize_from_config(database_path=output_path("detection.db"))
    simulate_all(database,12)
    for device in database.list_devices(): train_baseline(database,device["device_id"])
    normal=simulate_window(database,"camera-01",100,False)
    abnormal=simulate_window(database,"camera-01",101,True)
    assert abnormal["anomaly_score"] > normal["anomaly_score"]
    assert abnormal["anomaly_score"] >= 0.6
    assert database.alerts("camera-01")

