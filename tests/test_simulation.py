from simulation.generator import generate_window

def test_anomaly_changes_telemetry_characteristics():
    normal=generate_window("camera-01",1,False)
    anomaly=generate_window("camera-01",1,True)
    assert len(anomaly) > len(normal)*5
    assert len({e.destination for e in anomaly}) > len({e.destination for e in normal})
    assert sum(e.bytes for e in anomaly) > sum(e.bytes for e in normal)*10

