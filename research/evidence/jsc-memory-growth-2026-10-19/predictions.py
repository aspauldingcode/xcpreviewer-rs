"""Independent complete-memory arrays; no acquired bytes used as goldens."""
PAGE=65536
NAMES=['initial','zero-grow','positive-grow','js-failed-grow','wasm-failed-grow']
def expected(stage):
    if stage not in NAMES:raise ValueError('stage')
    index=NAMES.index(stage);b=bytearray(b'\xa5'*PAGE)
    for y in range(5):
        for x in range(17):
            for c in range(4):b[y*96+x*4+c]=(x*7+y*11+c*31)&255
    b[0]=17
    if index>=1:b[1]=34
    if index>=2:b+=bytes(PAGE);b[PAGE+3]=51
    if index>=3:b[2]=68
    if index>=4:b[3]=85
    return bytes(b)
