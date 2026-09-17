from features.extractor import extract_features

def test_feature_calculation():
    events=[{"packets":10,"bytes":1000,"destination":"a.local","destination_port":443,"protocol":"HTTPS","direction":"outbound"},
            {"packets":5,"bytes":500,"destination":"dns.local","destination_port":53,"protocol":"DNS","direction":"inbound"}]
    result=extract_features(events,60)
    assert result["packets_per_second"] == 0.25
    assert result["connections_per_minute"] == 2
    assert result["unique_destinations"] == 2
    assert result["dns_requests"] == 1
    assert result["outbound_ratio"] == 0.5

