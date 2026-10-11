#include "layer_expectations.h"
extern unsigned char *pixels(void);
extern unsigned capacity(void);
extern unsigned render(unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned);
unsigned verify(unsigned variant,unsigned mutation) {
    if(variant>=40 || mutation>4 || capacity()!=16384) return 0xffffffff;
    unsigned char *p=pixels();for(unsigned i=0;i<capacity();i++) p[i]=0xc3;
    const unsigned *a=source_alphas[variant/2];
    if(render(17,9,80,a[0],a[1],a[2],variant%2)!=720) return 0xffffffff;
    if(mutation) p[mutation==1?0:mutation==2?3:mutation==3?68:16383]^=1;
    unsigned count=0;
    for(unsigned i=0;i<capacity();i++) count+=p[i]!=(i<720?native_targets[variant][i]:0xc3);
    return count;
}
unsigned verify_all(unsigned mutation) {
    if(mutation>4) return 0xffffffff;
    unsigned sum=0;
    for(unsigned variant=0;variant<40;variant++) {
        unsigned count=verify(variant,mutation);
        if(count!=(mutation?1:0)) return 0xffffffff;
        sum+=count;
    }
    return sum;
}
