// Explicit opaque red/blue rectangle feasibility fixture, not SwiftUI compilation.
static unsigned char buffer[204800];
unsigned char *pixels(void) { return buffer; }
unsigned capacity(void) { return sizeof(buffer); }
unsigned render(unsigned width, unsigned height, unsigned stride, unsigned variant) {
    if (!width || width > 320 || !height || height > 160 || stride < width * 4 || stride > 1280 || (variant != 2 && variant != 3)) return 0;
    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            unsigned i = y * stride + x * 4;
            buffer[i] = variant == 2 ? 255 : 0;
            buffer[i + 1] = 0;
            buffer[i + 2] = variant == 3 ? 255 : 0;
            buffer[i + 3] = 255;
        }
        for (unsigned i = width * 4; i < stride; i++) buffer[y * stride + i] = 0xcd;
    }
    return stride * height;
}
