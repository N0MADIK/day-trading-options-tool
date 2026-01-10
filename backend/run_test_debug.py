import pytest
import sys

# Redirect stdout/stderr to file
with open('pytest_full_log.txt', 'w') as f:
    sys.stdout = f
    sys.stderr = f
    
    # Run specific test
    retcode = pytest.main([
        "tests/test_finance_flow_integration.py::TestProfilesRouter::test_get_my_profile",
        "-vv",
        "--tb=long"
    ])

print(f"Pytest run finished with code {retcode}", file=sys.__stdout__)
