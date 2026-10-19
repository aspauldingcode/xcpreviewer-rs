"""Independent marker arrays and predeclared observable event relations."""
def marker():
 b=bytearray(b'\xa5'*1024)
 for y in range(3):
  for x in range(5):
   for c in range(4):b[y*32+x*4+c]=(x*13+y*7+c*31)&255
 return bytes(b)
