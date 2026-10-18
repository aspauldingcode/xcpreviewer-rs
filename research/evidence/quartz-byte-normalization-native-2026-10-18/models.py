"""Exact rational predictions; diagnostic hypotheses, never native goldens."""
from fractions import Fraction
import struct

def f32_bits(value):
    """Round a nonnegative normal-range rational to binary32, ties to even."""
    value=Fraction(value)
    if value < 0 or value > 2:raise ValueError('domain 0..2')
    if value==0:return 0
    exponent=value.numerator.bit_length()-value.denominator.bit_length()
    if value < Fraction(2)**exponent:exponent-=1
    if exponent < -126:raise ValueError('subnormal outside this experiment')
    scaled=value*Fraction(2)**(23-exponent)
    q,rem=divmod(scaled.numerator,scaled.denominator)
    if rem*2>scaled.denominator or (rem*2==scaled.denominator and q%2):q+=1
    if q==(1<<24):q>>=1;exponent+=1
    return ((exponent+127)<<23)|(q-(1<<23))

def from_bits(bits):
    exponent=(bits>>23)&255;mantissa=bits&((1<<23)-1)
    if exponent==0:return Fraction(mantissa)*Fraction(2)**-149
    if exponent==255:raise ValueError('nonfinite')
    return Fraction((1<<23)+mantissa)*Fraction(2)**(exponent-127-23)

RECIPROCAL_BITS=f32_bits(Fraction(1,255))
def predict(byte,route):
    if type(byte) is not int or not 0<=byte<=255:raise ValueError('byte domain')
    if route=='division':value=Fraction(byte,255)
    elif route=='reciprocal':value=byte*from_bits(RECIPROCAL_BITS)
    else:raise ValueError('unknown model')
    return struct.pack('<I',f32_bits(value))

def domain():
    return [{'byte':i,'division_hex':predict(i,'division').hex(),'reciprocal_hex':predict(i,'reciprocal').hex()} for i in range(256)]
