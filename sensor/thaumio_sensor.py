import asyncio
import os
import sys

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from thaumio.main import SimulationRunner

async def main():
    print("=== Thaumio IoT Digital Twin Simulator Starting ===")
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config",
        "thaumio_topology.json"
    )
    print(f"Loading topology from: {config_path}")
    
    runner = SimulationRunner(config_path)
    runner.load_topology()
    
    await runner.start()
    print("=== Thaumio Simulation Subsystems Running (Press Ctrl+C to stop) ===")
    print("Control plane available at http://127.0.0.1:8081/docs")
    
    try:
        while True:
            await asyncio.sleep(3600)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        print("\nStopping Thaumio Simulation subsystems...")
        await runner.stop()
        print("=== Thaumio Simulator Terminated ===")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
