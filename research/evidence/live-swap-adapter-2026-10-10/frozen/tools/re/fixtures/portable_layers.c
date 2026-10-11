// Explicit primary-only premultiplied source-over; callback-target contract.
static unsigned char buffer[16384];
unsigned char *pixels(void) { return buffer; }
unsigned capacity(void) { return sizeof(buffer); }
unsigned render(unsigned w,unsigned h,unsigned stride,unsigned red,unsigned green,unsigned blue,unsigned reverse) {
    if(!w || w>64 || !h || h>64 || stride<w*4 || stride>256 || red>8 || green>8 || blue>8 || reverse>1) return 0;
    unsigned inputs[3]={red,green,blue}, p[4]={0,0,0,0};
    const unsigned forward[3]={2,0,1}, backward[3]={1,0,2};
    for(unsigned layer=0;layer<3;layer++) {
        unsigned channel=(reverse?backward:forward)[layer],a=(inputs[channel]*255+4)/8;
        for(unsigned c=0;c<4;c++) p[c]=(c==channel || c==3 ? a:0)+(p[c]*(255-a)+127)/255;
    }
    for(unsigned y=0;y<h;y++) {
        for(unsigned x=0;x<w;x++) for(unsigned c=0;c<4;c++) buffer[y*stride+x*4+c]=p[c];
        for(unsigned i=w*4;i<stride;i++) buffer[y*stride+i]=0xa5;
    }
    return stride*h;
}
