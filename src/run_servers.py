import concurrent.futures
import subprocess

def run_fastapi():
    subprocess.run(["uvicorn", "./src/app:app", "--host", "127.0.0.1", "--port", "8000"])

def run_dash():
    subprocess.run(["./.venv/Scripts/python.exe", "./src/dash_app.py"])

if __name__ == "__main__":
    with concurrent.futures.ProcessPoolExecutor() as executor:
        fastapi_future = executor.submit(run_fastapi)
        dash_future = executor.submit(run_dash)

        # Ожидание завершения обоих процессов
        concurrent.futures.wait([fastapi_future, dash_future])

