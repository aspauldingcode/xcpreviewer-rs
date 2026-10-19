// Research-only public CGRect observation boundary; no private Swift ABI calls.
#include <CoreGraphics/CoreGraphics.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
static void bits(CGFloat x) { uint64_t u;memcpy(&u,&x,8);printf("\"%016llx\"",(unsigned long long)u); }
static void rect(CGRect r) { putchar('[');bits(r.origin.x);putchar(',');bits(r.origin.y);putchar(',');bits(r.size.width);putchar(',');bits(r.size.height);putchar(']'); }
int main(void) {
 CGRect rs[]={CGRectMake(-1.5,2,3.25,4.5),CGRectMake(10,20,-4,-8),CGRectMake(0,0,-0.0,4),CGRectNull,CGRectInfinite,CGRectMake(INFINITY,INFINITY,2,3),CGRectMake(INFINITY,0,0,0),CGRectMake(0,INFINITY,0,0),CGRectMake(0,0,INFINITY,INFINITY),CGRectMake(NAN,2,3,4),CGRectMake(-INFINITY,0,1,2),CGRectMake(0,-INFINITY,1,2),CGRectMake(-INFINITY,-INFINITY,INFINITY,INFINITY),CGRectMake(CGRectInfinite.origin.x,CGRectInfinite.origin.y,CGRectInfinite.size.width-0x1p972,CGRectInfinite.size.height),CGRectMake(CGRectInfinite.origin.x+0x1p971,CGRectInfinite.origin.y,CGRectInfinite.size.width,CGRectInfinite.size.height),CGRectMake(0,0,NAN,4),CGRectMake(-0.0,-0.0,-0.0,-0.0),CGRectMake(1,2,7,11)};
 double factors[]={0.5,1.0/3.0,2,-2,0,-0.0,INFINITY,-INFINITY,NAN,3};
 printf("[\n");
 for(size_t i=0;i<sizeof(rs)/sizeof(rs[0]);i++)for(size_t j=0;j<sizeof(factors)/sizeof(factors[0]);j++) {
  CGRect r=rs[i],o=r;double s=factors[j];bool nul=CGRectIsNull(r),inf=CGRectIsInfinite(r);
  if(!nul&&!inf) {o.origin.x=r.origin.x*s;o.origin.y=r.origin.y*s;o.size.width=CGRectGetWidth(r)*s;o.size.height=CGRectGetHeight(r)*s;}
  printf("{\"rect_case\":%zu,\"factor_case\":%zu,\"input\":",i,j);rect(r);printf(",\"factor\":");bits(s);printf(",\"is_null\":%s,\"is_infinite\":%s,\"output\":",nul?"true":"false",inf?"true":"false");rect(o);CGRect point=r;double reciprocal=1.0/s;if(!nul&&!inf){point.origin.x=r.origin.x*reciprocal;point.origin.y=r.origin.y*reciprocal;point.size.width=CGRectGetWidth(r)*reciprocal;point.size.height=CGRectGetHeight(r)*reciprocal;}printf(",\"point_output\":");rect(point);printf(",\"size_points\":[");bits(r.size.width/s);putchar(',');bits(r.size.height/s);printf("]");printf("}%s\n",i==sizeof(rs)/sizeof(rs[0])-1&&j==sizeof(factors)/sizeof(factors[0])-1?"":",");
 }
 printf("]\n");return 0;
}
