"""Unified CyberTwin command-line interface."""
import argparse
from database.setup import initialize_from_config
from simulation.service import simulate_all, simulate_window
from twin.baseline import train_baseline

parser=argparse.ArgumentParser(prog="python -m cybertwin")
sub=parser.add_subparsers(dest="command",required=True)
sub.add_parser("start"); sub.add_parser("train"); sub.add_parser("status")
attack=sub.add_parser("attack"); attack.add_argument("device",nargs="?",default="camera-01")
args=parser.parse_args(); database=initialize_from_config()
if args.command=="start": simulate_all(database,12); print("Normal telemetry generated")
elif args.command=="train":
    for item in database.list_devices(): train_baseline(database,item["device_id"])
    print("Baselines trained")
elif args.command=="attack": print(simulate_window(database,args.device,9999,True))
elif args.command=="status":
    for item in database.list_devices(): print(item["device_id"],item["status"],item["anomaly_score"])

