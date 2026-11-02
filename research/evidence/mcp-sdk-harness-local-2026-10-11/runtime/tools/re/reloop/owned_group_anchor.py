"""Remain the owned process-group leader until its creator drains the group.

The target cannot write the dedicated control descriptor. No shell, existing PID,
or runtime attachment is used. Children inheriting the group are in scope;
children escaping the group are not.
"""
import json
import os
import subprocess
import sys
import time


def main():
    try:
        target = subprocess.Popen(sys.argv[1:], close_fds=True)
        code = target.wait()
        report = {'target_code': code}
    except Exception as error:
        report = {'target_code': 127, 'error': type(error).__name__}
    os.write(3, (json.dumps(report) + '\n').encode())
    # The creator terminates this still-live group after receiving the report,
    # including when the target exited and an inherited child still holds pipes.
    while True:
        time.sleep(3600)


if __name__ == '__main__':
    main()
