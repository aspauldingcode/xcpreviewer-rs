// Research event-pump variant. Execution requires scoped review.
// Diagnostic research revision. Native execution requires scoped review.
// Owned public-API research fixture. No Xcode, activation, input or permission request.
#import <Cocoa/Cocoa.h>
#import <ApplicationServices/ApplicationServices.h>
#include <unistd.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
static unsigned long long nanos(void){struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))return 0;return (unsigned long long)t.tv_sec*1000000000ULL+t.tv_nsec;}
static id attr(AXUIElementRef e,CFStringRef key) {
 CFTypeRef value=NULL;AXError err=AXUIElementCopyAttributeValue(e,key,&value);
 return err==kAXErrorSuccess?CFBridgingRelease(value):nil;
}
static BOOL rectFor(AXUIElementRef e,CGRect *r,NSMutableDictionary *detail) {
 CFTypeRef pr=NULL,sr=NULL;AXError pe=AXUIElementCopyAttributeValue(e,kAXPositionAttribute,&pr),se=AXUIElementCopyAttributeValue(e,kAXSizeAttribute,&sr);
 id p=pr?CFBridgingRelease(pr):nil,s=sr?CFBridgingRelease(sr):nil;CGPoint pos;CGSize size;
 detail[@"position_error"]=@(pe);detail[@"size_error"]=@(se);detail[@"position_CF_type"]=@(p?CFGetTypeID((__bridge CFTypeRef)p):0);detail[@"size_CF_type"]=@(s?CFGetTypeID((__bridge CFTypeRef)s):0);
 if(pe!=kAXErrorSuccess||se!=kAXErrorSuccess)return NO;
 if(!p||!s||CFGetTypeID((__bridge CFTypeRef)p)!=AXValueGetTypeID()||CFGetTypeID((__bridge CFTypeRef)s)!=AXValueGetTypeID())return NO;
 detail[@"position_AX_type"]=@(AXValueGetType((__bridge AXValueRef)p));detail[@"size_AX_type"]=@(AXValueGetType((__bridge AXValueRef)s));
 if(!AXValueGetValue((__bridge AXValueRef)p,kAXValueCGPointType,&pos)||!AXValueGetValue((__bridge AXValueRef)s,kAXValueCGSizeType,&size))return NO;
 *r=(CGRect){pos,size};detail[@"AX_rect"]=CFBridgingRelease(CGRectCreateDictionaryRepresentation(*r));return YES;
}
static AXUIElementRef button(AXUIElementRef e,int depth) CF_RETURNS_RETAINED {
 if(depth<0)return NULL;
 if([attr(e,kAXRoleAttribute) isEqual:(__bridge NSString*)kAXButtonRole]&&[attr(e,kAXIdentifierAttribute) isEqual:@"owned-binding-button"])return (AXUIElementRef)CFRetain(e);
 id children=attr(e,kAXChildrenAttribute);if(![children isKindOfClass:[NSArray class]]||[children count]>32)return NULL;
 for(id c in children){if(CFGetTypeID((__bridge CFTypeRef)c)!=AXUIElementGetTypeID())continue;AXUIElementRef found=button((__bridge AXUIElementRef)c,depth-1);if(found)return found;}
 return NULL;
}
static NSDictionary *itemDetail(AXUIElementRef e) {
 pid_t pid=-1;AXError pe=AXUIElementGetPid(e,&pid);NSMutableDictionary *d=[@{@"pid_error":@(pe),@"pid":@(pid)} mutableCopy];
 if(pe!=kAXErrorSuccess||pid!=getpid())return d;
 for(NSString *key in @[@"AXRole"]){CFTypeRef raw=NULL;AXError err=AXUIElementCopyAttributeValue(e,(__bridge CFStringRef)key,&raw);id value=raw?CFBridgingRelease(raw):nil;NSMutableDictionary *a=[@{@"error":@(err),@"CF_type":@(value?CFGetTypeID((__bridge CFTypeRef)value):0)} mutableCopy];if([value isKindOfClass:[NSString class]]){NSUInteger length=[value length];a[@"string"]=[value substringToIndex:MIN(length,(NSUInteger)256)];a[@"string_truncated"]=(length>256?@YES:@NO);}if([value isKindOfClass:[NSArray class]])a[@"count"]=@([value count]);d[key]=a;}
 return d;
}
static NSDictionary *observe(NSDictionary *expected) {
 unsigned long long started=nanos();AXUIElementRef app=AXUIElementCreateApplication(getpid());AXError timeoutResult=AXUIElementSetMessagingTimeout(app,0.2);
 CFTypeRef raw=NULL;AXError windowError=AXUIElementCopyAttributeValue(app,kAXWindowsAttribute,&raw);CFRelease(app);
 CFTypeID returnedType=raw?CFGetTypeID(raw):0;id windows=raw?CFBridgingRelease(raw):nil;
 if(windowError!=kAXErrorSuccess||![windows isKindOfClass:[NSArray class]]||[windows count]!=2){
  NSArray *cg=CFBridgingRelease(CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly|kCGWindowListExcludeDesktopElements,kCGNullWindowID));NSMutableArray *ids=[NSMutableArray array];
  for(NSDictionary *w in cg)if([w[(__bridge NSString*)kCGWindowOwnerPID] intValue]==getpid()&&[w[(__bridge NSString*)kCGWindowLayer] intValue]==0)[ids addObject:w[(__bridge NSString*)kCGWindowNumber]];
  return @{@"status":@"two_AX_windows_unavailable",@"AX_windows_error":@(windowError),@"AX_timeout_setting_error":@(timeoutResult),@"returned_CF_type":@(returnedType),@"AX_window_count":@([windows isKindOfClass:[NSArray class]]?(NSInteger)[windows count]:(NSInteger)-1),@"own_CG_available":@(cg!=nil),@"own_CG_ids":ids,@"observation_started_ns":@(started),@"observation_finished_ns":@(nanos())};
 }
 NSArray *all=CFBridgingRelease(CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly|kCGWindowListExcludeDesktopElements,kCGNullWindowID));
 if(!all)return @{@"status":@"CG_inventory_unavailable"};
 NSMutableArray *owned=[NSMutableArray array];for(NSDictionary *w in all)if([w[(__bridge NSString*)kCGWindowOwnerPID] intValue]==getpid()&&[w[(__bridge NSString*)kCGWindowLayer] intValue]==0)[owned addObject:w];
 NSMutableArray *rows=[NSMutableArray array];
 for(id item in windows){
  CFTypeID itemType=CFGetTypeID((__bridge CFTypeRef)item);if(itemType!=AXUIElementGetTypeID())return @{@"status":@"AX_item_type_rejected",@"item_CF_type":@(itemType),@"expected_AX_CF_type":@(AXUIElementGetTypeID())};
  AXUIElementRef w=(__bridge AXUIElementRef)item;NSDictionary *identity=itemDetail(w);if([identity[@"pid_error"] intValue]!=0||[identity[@"pid"] intValue]!=getpid())return @{@"status":@"AX_item_PID_rejected",@"item_detail":identity};
  AXUIElementRef root=AXUIElementCreateApplication(getpid()),rootControl=AXUIElementCreateApplication(getpid());BOOL rootEqual=CFEqual(w,root),secondRootEqual=CFEqual((__bridge CFTypeRef)windows[1],root),rootControlEqual=CFEqual(root,rootControl);CFRelease(rootControl);CFRelease(root);
  BOOL pairEqual=CFEqual((__bridge CFTypeRef)windows[0],(__bridge CFTypeRef)windows[1]);
  NSDictionary *role=identity[@"AXRole"];if([role[@"error"] intValue]!=kAXErrorSuccess||![role[@"string"] isEqual:(__bridge NSString*)kAXWindowRole])return @{@"status":@"AX_item_role_rejected",@"item_CF_type":@(itemType),@"expected_AX_CF_type":@(AXUIElementGetTypeID()),@"item_detail":identity,@"equals_current_app_root":(rootEqual?@YES:@NO),@"returned_items_equal":(pairEqual?@YES:@NO),@"second_item_equals_app_root":(secondRootEqual?@YES:@NO),@"independent_app_roots_equal_control":(rootControlEqual?@YES:@NO)};
  CGRect rect;NSString *doc=attr(w,kAXDocumentAttribute);AXUIElementRef b=button(w,4);
  id ancestor=b?attr(b,kAXWindowAttribute):nil;BOOL ancestry=ancestor&&CFEqual((__bridge CFTypeRef)ancestor,w);if(b)CFRelease(b);
  NSMutableArray *matches=[NSMutableArray array];NSMutableDictionary *geometry=[NSMutableDictionary dictionary];NSMutableArray *cgGeometry=[NSMutableArray array];
  for(NSDictionary *cg in owned)[cgGeometry addObject:@{@"id":cg[(__bridge NSString*)kCGWindowNumber],@"rect":cg[(__bridge NSString*)kCGWindowBounds]}];
  if(rectFor(w,&rect,geometry))for(NSDictionary *cg in owned){CGRect other;if(CGRectMakeWithDictionaryRepresentation((__bridge CFDictionaryRef)cg[(__bridge NSString*)kCGWindowBounds],&other)&&CGRectEqualToRect(rect,other))[matches addObject:cg[(__bridge NSString*)kCGWindowNumber]];}
  NSNumber *known=[doc isKindOfClass:[NSString class]]?expected[doc]:nil;
  [rows addObject:@{@"document":doc?:@"",@"button_ancestor_matches":@(ancestry),@"candidate_ids":matches,@"fixture_window_id":known?:@0,@"unique_candidate_equals_fixture":((matches.count==1&&[matches[0] isEqual:known])?@YES:@NO),@"AX_geometry":geometry,@"CG_geometry":cgGeometry,@"item_CF_type":@(itemType),@"expected_AX_CF_type":@(AXUIElementGetTypeID()),@"item_detail":identity}];
 }
 return @{@"status":@"observed",@"own_cg_windows":@(owned.count),@"rows":rows,@"AX_windows_error":@(windowError),@"AX_timeout_setting_error":@(timeoutResult),@"returned_CF_type":@(returnedType),@"AX_window_count":@([windows count]),@"observation_started_ns":@(started),@"observation_finished_ns":@(nanos())};
}
// Ordinary AppKit event delivery/transaction update for the owned fixture only.
static void pumpFor(double seconds){
 unsigned long long end=nanos()+(unsigned long long)(seconds*1000000000.0);
 while(nanos()<end){NSEvent *event=[NSApp nextEventMatchingMask:NSEventMaskAny untilDate:[NSDate dateWithTimeIntervalSinceNow:0.01] inMode:NSDefaultRunLoopMode dequeue:YES];if(event)[NSApp sendEvent:event];[NSApp updateWindows];}
}
static NSDictionary *phase(NSDictionary *expected) {
 dispatch_semaphore_t done=dispatch_semaphore_create(0);__block NSDictionary *result=nil;
 dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0),^{@autoreleasepool{result=observe(expected);dispatch_semaphore_signal(done);}});
 unsigned long long end=nanos()+2000000000ULL;
 while(dispatch_semaphore_wait(done,DISPATCH_TIME_NOW)!=0){if(nanos()>=end)return @{@"status":@"owned_phase_deadline"};pumpFor(0.01);}
 return result;
}
static BOOL admitted(NSDictionary *p,NSDictionary *expected,BOOL overlap) {
 if(![p[@"status"] isEqual:@"observed"]||[p[@"own_cg_windows"] intValue]!=2||[p[@"rows"] count]!=2)return NO;
 NSMutableSet *docs=[NSMutableSet set];NSSet *ids=[NSSet setWithArray:expected.allValues];
 for(NSDictionary *row in p[@"rows"]){
  NSString *doc=row[@"document"];if(!expected[doc]||[docs containsObject:doc]||![row[@"button_ancestor_matches"] boolValue])return NO;[docs addObject:doc];
  if(![row[@"fixture_window_id"] isEqual:expected[doc]])return NO;
  if(overlap){if([row[@"candidate_ids"] count]!=2||![[NSSet setWithArray:row[@"candidate_ids"]] isEqual:ids])return NO;}
  else if(![row[@"unique_candidate_equals_fixture"] boolValue])return NO;
 }
 return [docs isEqual:[NSSet setWithArray:expected.allKeys]];
}
static NSInteger ownedOnScreen(pid_t pid){
 NSArray *all=CFBridgingRelease(CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly|kCGWindowListExcludeDesktopElements,kCGNullWindowID));if(!all)return -1;NSInteger n=0;
 for(NSDictionary *w in all)if([w[(__bridge NSString*)kCGWindowOwnerPID] intValue]==pid&&[w[(__bridge NSString*)kCGWindowLayer] intValue]==0)n++;
 return n;
}
static void output(NSDictionary *out){NSData *d=[NSJSONSerialization dataWithJSONObject:out options:0 error:NULL];if(d){write(1,d.bytes,d.length);write(1,"\n",1);}}
int main(int argc,const char **argv) {@autoreleasepool{
 alarm(8);
 if(argc==3&&!strcmp(argv[1],"--inventory")){char *end=NULL;long pid=strtol(argv[2],&end,10);if(!end||*end||pid<=1||pid>INT_MAX)return 2;output(@{@"target_pid":@(pid),@"owned_on_screen_windows":@(ownedOnScreen((pid_t)pid))});return 0;}
 NSMutableDictionary *out=[@{@"pid":@(getpid()),@"trusted":@(AXIsProcessTrusted()),@"scope":@"owned-two-window-public-API-read-only"} mutableCopy];
 if(![out[@"trusted"] boolValue]){out[@"status"]=@"accessibility_prerequisite_missing";output(out);return 77;}
 if(argc==1){out[@"status"]=@"trusted_preflight_only";output(out);return 0;}
 if(argc!=3||strcmp(argv[1],"--fixture"))return 2;
 [NSApplication sharedApplication];[NSApp setActivationPolicy:NSApplicationActivationPolicyAccessory];[NSApp finishLaunching];
 NSMutableArray<NSWindow*> *windows=[NSMutableArray array];NSMutableDictionary *expected=[NSMutableDictionary dictionary];
 for(int i=0;i<2;i++){
  NSWindow *w=[[NSWindow alloc] initWithContentRect:NSMakeRect(160+i*240,160,200,100) styleMask:NSWindowStyleMaskTitled backing:NSBackingStoreBuffered defer:NO];w.title=@"Owned binding sentinel";w.releasedWhenClosed=NO;w.animationBehavior=NSWindowAnimationBehaviorNone;
  NSURL *url=[NSURL fileURLWithPath:[NSString stringWithFormat:@"%s/%c.xcodeproj",argv[2],'a'+i]];w.representedURL=url;
  NSButton *b=[[NSButton alloc] initWithFrame:NSMakeRect(30,30,130,30)];b.title=@"Same control";b.accessibilityIdentifier=@"owned-binding-button";[w.contentView addSubview:b];[w orderBack:nil];[windows addObject:w];expected[url.absoluteString]=@(w.windowNumber);
 }
 pumpFor(0.15);
 NSMutableArray *phases=[NSMutableArray array];BOOL accepted=YES;
 for(int i=0;i<3;i++){
  if(i==1){[windows[1] orderWindow:NSWindowAbove relativeTo:windows[0].windowNumber];pumpFor(0.1);}
  if(i==2){[windows[1] setFrame:windows[0].frame display:NO];pumpFor(0.1);}
  NSDictionary *p=phase(expected);[phases addObject:p];if(!admitted(p,expected,i==2)){accepted=NO;break;}
 }
 for(NSWindow *w in windows)[w close];pumpFor(0.1);
 out[@"phases"]=phases;out[@"own_on_screen_after_close"]=@(ownedOnScreen(getpid()));
 if([out[@"own_on_screen_after_close"] unsignedIntegerValue]!=0)accepted=NO;
 out[@"status"]=accepted?@"owned_geometry_correlation_admitted":@"owned_fixture_rejected";out[@"admitted"]=(accepted?@YES:@NO);output(out);return accepted?0:78;
}}
