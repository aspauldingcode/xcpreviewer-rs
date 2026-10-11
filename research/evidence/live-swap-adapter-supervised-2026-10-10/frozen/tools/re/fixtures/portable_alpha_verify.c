#include "alpha_expectations.h"
extern unsigned char *pixels(void);
extern unsigned capacity(void);
extern unsigned render(unsigned,unsigned,unsigned,unsigned,unsigned);
static const unsigned numerator[8]={0,2,4,8,2,4,1,6};
static const unsigned background[8]={0,0,0,0,1,1,1,1};
unsigned verify(unsigned variant, unsigned mutation) {
    if (variant>=8 || mutation>3 || capacity()!=16384) return 0xffffffff;
    unsigned char *p=pixels();
    for(unsigned i=0;i<capacity();i++) p[i]=0xa5;
    if(render(17,9,80,numerator[variant],background[variant])!=720) return 0xffffffff;
    if(mutation) p[mutation==1?0:mutation==2?68:16383]^=1;
    unsigned mismatches=0;
    for(unsigned i=0;i<capacity();i++) {
        unsigned char expected=0xa5;
        if(i<720) expected=i%80<68?native_pixels[variant][(i/80)*68+i%80]:0xcd;
        mismatches+=p[i]!=expected;
    }
    return mismatches;
}
