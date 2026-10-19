"""Reconstructed verbatim initial parser excerpt; retained failure, never admission."""
import json
from compare import pairs

def parsed(raw):
    def bad(value):
        raise ValueError('non-finite JSON constant')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)

if __name__ == '__main__':
    import math
    result = parsed('{"unused":[{"nested":1e999}]}')
    if math.isfinite(result['unused'][0]['nested']):
        raise ValueError('counterexample missing')
    print('{"retained_initial_parser_accepts_exponent_overflow":true,"native_execution":false}')
