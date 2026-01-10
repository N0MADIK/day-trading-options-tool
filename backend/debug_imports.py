
try:
    import jose
    print("SUCCESS: jose imported")
    print(f"jose file: {jose.__file__}")
except ImportError as e:
    print(f"ERROR: jose import failed: {e}")

try:
    import passlib
    print("SUCCESS: passlib imported")
except ImportError as e:
    print(f"ERROR: passlib import failed: {e}")
