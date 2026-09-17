"""Long-running containerized device telemetry producer."""
import json, os, time
from urllib.request import Request, urlopen
from simulation.generator import generate_window

device_id=os.environ["DEVICE_ID"]; api=os.getenv("CYBERTWIN_API","http://api:8000")
sequence=0
while True:
    for event in generate_window(device_id,sequence):
        request=Request(api+"/telemetry",data=event.model_dump_json().encode(),method="POST",headers={"Content-Type":"application/json"})
        try: urlopen(request,timeout=10).close()
        except Exception as error: print(f"telemetry delivery failed: {error}",flush=True)
    sequence+=1; time.sleep(int(os.getenv("DEVICE_INTERVAL","15")))
