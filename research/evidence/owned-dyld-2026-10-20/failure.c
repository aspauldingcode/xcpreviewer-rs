// Original owned host: synchronous failed creation must return NULL.
#include <CoreGraphics/CoreGraphics.h>
int main(void){CGColorSpaceRef cs=CGColorSpaceCreateWithName(kCGColorSpaceSRGB);CGImageRef image=CGImageCreate(0,2,8,32,16,cs,kCGBitmapByteOrder32Little|kCGImageAlphaPremultipliedFirst,NULL,NULL,false,kCGRenderingIntentDefault);CGColorSpaceRelease(cs);if(image){CGImageRelease(image);return 9;}return 0;}
