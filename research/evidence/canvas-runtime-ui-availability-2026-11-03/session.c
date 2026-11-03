#include <CoreGraphics/CGSession.h>
#include <CoreFoundation/CoreFoundation.h>
#include <stdio.h>
static const char *flag(CFDictionaryRef d,CFStringRef key){CFTypeRef v=CFDictionaryGetValue(d,key);return v&&CFGetTypeID(v)==CFBooleanGetTypeID()?(CFBooleanGetValue((CFBooleanRef)v)?"true":"false"):"null";}
int main(void){CFDictionaryRef d=CGSessionCopyCurrentDictionary();if(!d){puts("{\"session_available\":false}");return 0;}printf("{\"session_available\":true,\"on_console\":%s,\"login_done\":%s,\"screen_locked_field\":%s}\n",flag(d,kCGSessionOnConsoleKey),flag(d,kCGSessionLoginDoneKey),flag(d,CFSTR("CGSSessionScreenIsLocked")));CFRelease(d);return 0;}
