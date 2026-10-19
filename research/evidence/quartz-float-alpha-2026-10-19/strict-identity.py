"""Retain rejection of the independently predicted complete identity arrays."""
from pathlib import Path
import compare as c
from acquire import observed
value=observed(Path(__file__).resolve().parent)
c.require(all(row['identity']['exact'] for row in value['routes']), 'independent identity prediction rejected')
