// Owned public CoreFoundation plist-date decoding oracle.
#include <CoreFoundation/CoreFoundation.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
int main(int argc,char **argv){
 if(argc!=2)return 2;unsigned char input[4096];FILE*f=fopen(argv[1],"rb");if(!f)return 3;
 size_t n=fread(input,1,sizeof(input),f);int extra=fgetc(f);fclose(f);if(extra!=EOF)return 4;
 CFDataRef data=CFDataCreate(NULL,input,n);CFErrorRef error=NULL;
 CFPropertyListRef plist=CFPropertyListCreateWithData(NULL,data,kCFPropertyListImmutable,NULL,&error);
 if(!plist||CFGetTypeID(plist)!=CFArrayGetTypeID())return 5;
 CFIndex count=CFArrayGetCount((CFArrayRef)plist);printf("[");
 for(CFIndex i=0;i<count;i++){CFDateRef date=(CFDateRef)CFArrayGetValueAtIndex((CFArrayRef)plist,i);if(CFGetTypeID(date)!=CFDateGetTypeID())return 6;
  double time=CFDateGetAbsoluteTime(date);uint64_t bits;memcpy(&bits,&time,8);printf("%s\"%016llx\"",i?",":"",(unsigned long long)bits);
 }
 printf("]\n");CFRelease(plist);CFRelease(data);if(error)CFRelease(error);return 0;
}
