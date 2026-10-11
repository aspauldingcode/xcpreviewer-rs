"""Require actual instructions at a selected native entry, not a symbol heading."""
import re


def has_entry(text,address):
    for line in text.splitlines():
        match=re.match(r'^\s*([0-9a-f]+):\s+(?:(?:[0-9a-f]{2}\s+){4}|[0-9a-f]{8}\s+)([a-z][a-z0-9.]*)\b',line)
        if match and int(match[1],16)==address:return True
    return False


def normalize_words(text):
    # Generic llvm-objdump prints an ARM64 instruction word; Mach-O mode prints
    # four little-endian bytes. Preserve the exact word and all operands.
    def replace(match):
        raw=int(match[2],16).to_bytes(4,'little')
        return match[1]+' '.join('%02x'%b for b in raw)+'\t'
    return re.sub(r'^(\s*[0-9a-f]+:\s+)([0-9a-f]{8})\s+',replace,text,flags=re.M)
