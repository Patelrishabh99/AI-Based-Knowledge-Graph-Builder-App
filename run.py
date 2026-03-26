"""
Run both FastAPI backend and Streamlit frontend simultaneously.
Usage: python run.py
"""

import subprocess
import sys
import os
import signal
import time

# Add project root to path
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)


def main():
    print("=" * 60)
    print("  🧠 AI-Based Graph Builder for Enterprise Intelligence")
    print("=" * 60)
    print()

    # Load env
    from dotenv import load_dotenv
    load_dotenv()

    processes = []

    try:
        # Start FastAPI backend
        print("🚀 Starting FastAPI backend on http://localhost:8000 ...")
        backend = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app",
             "--reload", "--reload-dir", "backend",
             "--host", "127.0.0.1", "--port", "8000"],
            cwd=ROOT,
        )
        processes.append(backend)
        time.sleep(2)

        # Start Streamlit frontend
        print("🖥️  Starting Streamlit frontend on http://localhost:8501 ...")
        frontend = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "frontend/app.py",
             "--server.port", "8501", "--server.address", "localhost",
             "--browser.serverAddress", "localhost"],
            cwd=ROOT,
        )
        processes.append(frontend)

        print()
        print("✅ Both services are running!")
        print("   📡 Backend API:  http://localhost:8000/docs")
        print("   🖥️  Frontend UI:  http://localhost:8501")
        print()
        print("   Press Ctrl+C to stop all services.")
        print()

        # Wait for either process to exit
        while True:
            for p in processes:
                if p.poll() is not None:
                    raise KeyboardInterrupt()
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=5)
            except Exception:
                p.kill()
        print("✅ All services stopped.")


if __name__ == "__main__":
    main()
