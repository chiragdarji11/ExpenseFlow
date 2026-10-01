"""
ExpenseFlow - Root All-in-One Runner
Run from project root:
    python main.py          # Starts backend + frontend, opens browser
    python main.py --seed   # Seeds demo data and starts server
"""

import os
import sys
import shutil
import argparse
import subprocess
import webbrowser
import threading
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")


def ensure_env_file():
    env_file = os.path.join(BACKEND_DIR, ".env")
    env_example = os.path.join(BACKEND_DIR, ".env.example")
    if not os.path.exists(env_file) and os.path.exists(env_example):
        print("[Setup] '.env' not found in backend/. Creating from '.env.example'...", flush=True)
        shutil.copy(env_example, env_file)
        print("[Setup] Created backend/.env successfully.", flush=True)


def run_seeder():
    print("[Seed] Seeding sample data into database...", flush=True)
    try:
        if BACKEND_DIR not in sys.path:
            sys.path.insert(0, BACKEND_DIR)
        from database.seed import seed_database
        seed_database()
    except Exception as e:
        print(f"[Seed Error] Could not complete database seeding: {e}", flush=True)


def open_browser_delayed(url: str, delay: float = 2.0):
    def _open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    threading.Thread(target=_open, daemon=True).start()


def main():
    parser = argparse.ArgumentParser(description="ExpenseFlow - All-in-one runner")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--seed", action="store_true", help="Seed database with demo data before running")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open the browser")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")

    args = parser.parse_args()

    # Step 1: Ensure .env exists
    ensure_env_file()

    # Step 2: Run seeder if requested
    if args.seed:
        run_seeder()

    import socket
    port = args.port
    # Find free port if requested port is occupied
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex((args.host, port)) == 0:
            for p in range(args.port + 1, args.port + 20):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
                    if s2.connect_ex((args.host, p)) != 0:
                        port = p
                        print(f"[Notice] Port {args.port} is busy. Switched to port {port}.", flush=True)
                        break

    # Step 3: Show status and schedule browser opening
    url = f"http://{args.host}:{port}"
    print("\n" + "=" * 58, flush=True)
    print(" 🚀 ExpenseFlow is starting up!", flush=True)
    print(f" 🌐 Web Application: {url}/", flush=True)
    print(f" 📚 Swagger API Docs: {url}/docs", flush=True)
    print("=" * 58 + "\n", flush=True)

    if not args.no_browser:
        open_browser_delayed(url)

    # Step 4: Run uvicorn server in backend folder
    os.chdir(BACKEND_DIR)
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        args.host,
        "--port",
        str(port),
    ]
    if not args.no_reload:
        cmd.append("--reload")

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[ExpenseFlow] Server stopped by user.", flush=True)


if __name__ == "__main__":
    main()
