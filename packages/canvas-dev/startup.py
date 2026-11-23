"""Bounded decoder startup; terminate only the process group we create."""
import os
import signal
import subprocess


def run_decoder_build(command, timeout=90):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               start_new_session=True)
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        output, _ = process.communicate(timeout=3)
        raise RuntimeError(f'Decoder startup exceeded {timeout}s; owned build group stopped. '
                           'Other Cargo jobs may hold the package-cache lock.\n' +
                           output.decode(errors='replace')[-12000:]) from None
    if process.returncode:
        raise RuntimeError(f'Decoder build failed (exit {process.returncode}).\n' +
                           output.decode(errors='replace')[-12000:])
    return output
