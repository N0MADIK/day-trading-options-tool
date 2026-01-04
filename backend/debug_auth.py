"""Script to debug auth router import"""
import traceback
import sys

try:
    print("Importing auth router...")
    from app.api.v1.routers.auth import router
    print("auth router imported successfully")
except Exception as e:
    with open("error_traceback.log", "w") as f:
        f.write(f"Error type: {type(e).__name__}\n")
        f.write(f"Error: {e}\n")
        f.write("\n--- Full Traceback ---\n")
        traceback.print_exc(file=f)
    print("Traceback written to error_traceback.log")


