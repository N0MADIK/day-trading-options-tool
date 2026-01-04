import subprocess
import sys

try:
    print("Running app.main...")
    result = subprocess.run(
        ["uv", "run", "python", "-m", "app.main"],
        capture_output=True,
        text=True,
        cwd=r"c:\Users\skyfr\Documents\day-trading-options-tool\backend"
    )
    print("Return code:", result.returncode)
    print("Stdout:", result.stdout[:200])
    
    with open("startup_error.txt", "w") as f:
        f.write(result.stdout)
        f.write("\n--- STDERR ---\n")
        f.write(result.stderr)
        
    print("Output written to startup_error.txt")
except Exception as e:
    print(f"Error running subprocess: {e}")
