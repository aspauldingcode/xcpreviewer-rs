/* Separately compiled checker: render's implementation is opaque to this TU.
 * Expected arrays come from sealed native pixels and independent padding.
 * No LTO. Every byte is compared; mutation controls exercise the checker. */
#include "native_expectations.h"
extern unsigned render(unsigned, unsigned, unsigned, unsigned);
extern unsigned char *pixels(void);

unsigned verify(unsigned index, unsigned mutation) {
    if (index > 3 || mutation > 2) return ~0u;
    unsigned width = index == 3 ? 3 : 320;
    unsigned height = index == 3 ? 2 : 160;
    unsigned stride = index == 3 ? 16 : 1280;
    unsigned length = stride * height;
    const unsigned char *reference = index == 3 ? expected_padding :
        index == 2 ? expected_blue : expected_red;
    if (render(width, height, stride, index == 2 ? 3 : 2) != length)
        return ~0u;
    unsigned char *output = pixels();
    if (mutation == 1) output[0] ^= 1;
    if (mutation == 2) output[length - 1] ^= 1;
    unsigned mismatches = 0;
    for (unsigned i = 0; i < length; ++i)
        mismatches += output[i] != reference[i];
    return mismatches;
}

unsigned verify_rejected(unsigned index) {
    const unsigned invalid[10][4] = {
        {0,160,1280,2}, {321,160,1280,2}, {320,0,1280,2},
        {320,161,1280,2}, {320,160,1279,2}, {320,160,1281,2},
        {320,160,1280,0}, {~0u,160,1280,2},
        {320,~0u,1280,2}, {320,160,~0u,2}
    };
    if (index >= 10) return ~0u;
    if (render(320,160,1280,2) != 204800) return ~0u;
    const unsigned *args = invalid[index];
    if (render(args[0],args[1],args[2],args[3]) != 0) return ~0u;
    unsigned mismatches = 0;
    unsigned char *output = pixels();
    for (unsigned i = 0; i < 204800; ++i)
        mismatches += output[i] != expected_red[i];
    return mismatches;
}
