// Explicit eighth-step red alpha, optionally over opaque blue; not SwiftUI parsing.
static unsigned char buffer[16384];
unsigned char *pixels(void) { return buffer; }
unsigned capacity(void) { return sizeof(buffer); }
unsigned render(unsigned width, unsigned height, unsigned stride, unsigned eighths, unsigned background) {
    if (!width || width > 64 || !height || height > 64 || stride < width*4 || stride > 256 || eighths > 8 || background > 1) return 0;
    unsigned alpha = (eighths * 255 + 4) / 8;
    for (unsigned y=0; y<height; y++) {
        for (unsigned x=0; x<width; x++) {
            unsigned i=y*stride+x*4;
            buffer[i] = background ? alpha : (alpha ? 255 : 0);
            buffer[i+1] = 0;
            buffer[i+2] = background ? 255-alpha : 0;
            buffer[i+3] = background ? 255 : alpha;
        }
        for (unsigned i=width*4; i<stride; i++) buffer[y*stride+i]=0xcd;
    }
    return stride*height;
}
