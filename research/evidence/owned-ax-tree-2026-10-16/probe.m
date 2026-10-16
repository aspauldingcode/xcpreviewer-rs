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
#include <errno.h>
#include <stdio.h>
#include <signal.h>
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
static void pumpFor(double seconds);
static void output(NSDictionary *out);
static BOOL treeFail(NSMutableDictionary *state,NSString *reason){state[@"enumeration_finished"]=@NO;state[@"failure_reason"]=reason;return NO;}
static NSDictionary *treeString(AXUIElementRef e,CFStringRef key,NSUInteger cap){CFTypeRef raw=NULL;AXError er=AXUIElementCopyAttributeValue(e,key,&raw);id value=raw?CFBridgingRelease(raw):nil;NSMutableDictionary *d=[@{@"error":@(er),@"CF_type":@(value?CFGetTypeID((__bridge CFTypeRef)value):0)} mutableCopy];if([value isKindOfClass:[NSString class]]){d[@"value"]=[value substringToIndex:MIN([value length],cap)];d[@"truncated"]=([value length]>cap?@YES:@NO);}return d;}
static BOOL walkTree(AXUIElementRef e,NSInteger parent,NSString *doc,NSUInteger depth,NSMutableDictionary *state,NSMutableArray *seen,NSMutableArray *path){
 NSMutableArray *nodes=state[@"nodes"];if(nodes.count>=32)return treeFail(state,@"node_limit");if(depth>5)return treeFail(state,@"depth_limit");
 NSMutableDictionary *n=[@{@"index":@(nodes.count),@"parent":@(parent),@"root_document":doc,@"depth":@(depth),@"CF_type":@(CFGetTypeID(e)),@"expected_AX_CF_type":@(AXUIElementGetTypeID())} mutableCopy];[nodes addObject:n];
 if(CFGetTypeID(e)!=AXUIElementGetTypeID())return treeFail(state,@"node_type");pid_t pid=-1;AXError pe=AXUIElementGetPid(e,&pid);n[@"pid_error"]=@(pe);n[@"pid"]=@(pid);if(pe!=kAXErrorSuccess||pid!=getpid())return treeFail(state,@"node_own_PID");
 for(NSUInteger j=0;j<seen.count;j++)if(CFEqual(e,(__bridge CFTypeRef)seen[j])){n[@"alias_to"]=@(j);n[@"cycle"]=([path containsObject:@(j)]?@YES:@NO);return treeFail(state,@"cycle_or_alias");}
 [seen addObject:(__bridge id)e];NSMutableArray *next=[path mutableCopy];[next addObject:n[@"index"]];
 NSDictionary *role=treeString(e,kAXRoleAttribute,128),*identifier=treeString(e,kAXIdentifierAttribute,256);n[@"role"]=role;n[@"identifier"]=identifier;
 if([role[@"error"] intValue]!=0||![role[@"value"] isKindOfClass:[NSString class]]||[role[@"truncated"] boolValue])return treeFail(state,@"role_read_or_bound");
 if(parent==-1&&![role[@"value"] isEqual:(__bridge NSString*)kAXWindowRole])return treeFail(state,@"root_role");
 NSInteger ie=[identifier[@"error"] integerValue];if((ie==0&&![identifier[@"value"] isKindOfClass:[NSString class]])||(ie!=0&&[identifier[@"CF_type"] unsignedLongLongValue]!=0)||(ie!=0&&ie!=kAXErrorAttributeUnsupported&&ie!=kAXErrorNoValue)||[identifier[@"truncated"] boolValue])return treeFail(state,@"identifier_read_or_bound");
 CFTypeRef raw=NULL;AXError ce=AXUIElementCopyAttributeValue(e,kAXChildrenAttribute,&raw);id children=raw?CFBridgingRelease(raw):nil;NSMutableDictionary *c=[@{@"error":@(ce),@"CF_type":@(children?CFGetTypeID((__bridge CFTypeRef)children):0)} mutableCopy];n[@"children"]=c;
 if(ce==kAXErrorNoValue||ce==kAXErrorAttributeUnsupported){
  if(children)return treeFail(state,@"terminal_error_with_value");n[@"terminal_status"]=(ce==kAXErrorNoValue?@"NoValue":@"Unsupported");
  CFArrayRef ar=NULL;AXError ae=AXUIElementCopyAttributeNames(e,&ar);id names=ar?CFBridgingRelease(ar):nil;NSMutableDictionary *a=[@{@"error":@(ae),@"CF_type":@(names?CFGetTypeID((__bridge CFTypeRef)names):0)} mutableCopy];n[@"attribute_names"]=a;
  if(ae!=0||![names isKindOfClass:[NSArray class]]||[names count]>64)return treeFail(state,@"attribute_names_read_or_bound");
  for(id name in names)if(![name isKindOfClass:[NSString class]]||[name length]>128)return treeFail(state,@"attribute_name_string_bound");a[@"names"]=names;a[@"contains_AXChildren"]=([names containsObject:(__bridge NSString*)kAXChildrenAttribute]?@YES:@NO);return YES;
 }
 if(ce!=kAXErrorSuccess||![children isKindOfClass:[NSArray class]]||[children count]>32)return treeFail(state,@"children_read_or_bound");c[@"count"]=@([children count]);
 for(id child in children)if(!walkTree((__bridge AXUIElementRef)child,[n[@"index"] integerValue],doc,depth+1,state,seen,next))return NO;
 return YES;
}
static NSDictionary *treeInventory(NSDictionary *expected){
 NSMutableDictionary *state=[@{@"expected_string_CF_type":@(CFStringGetTypeID()),@"expected_array_CF_type":@(CFArrayGetTypeID()),@"status":@"owned_readonly_tree_inventory",@"enumeration_finished":@YES,@"absence_policy_resolved":@NO,@"input_eligibility_qualified":@NO,@"nodes":[NSMutableArray array],@"roots":[NSMutableArray array],@"limits":@{@"nodes":@32,@"depth":@5,@"children":@32,@"attribute_names":@64,@"role_units":@128,@"identifier_units":@256,@"name_units":@128}} mutableCopy];
 AXUIElementRef app=AXUIElementCreateApplication(getpid());AXUIElementSetMessagingTimeout(app,0.2);CFTypeRef raw=NULL;AXError er=AXUIElementCopyAttributeValue(app,kAXWindowsAttribute,&raw);CFRelease(app);id windows=raw?CFBridgingRelease(raw):nil;state[@"AX_windows_error"]=@(er);
 if(er!=0||![windows isKindOfClass:[NSArray class]]||[windows count]!=2){treeFail(state,@"root_windows");return state;}
 NSMutableSet *docs=[NSMutableSet set];NSMutableArray *seen=[NSMutableArray array];
 for(id item in windows){AXUIElementRef w=(__bridge AXUIElementRef)item;if(CFGetTypeID(w)!=AXUIElementGetTypeID()){treeFail(state,@"root_type");break;}pid_t pid=-1;if(AXUIElementGetPid(w,&pid)!=0||pid!=getpid()){treeFail(state,@"root_own_PID");break;}if(![attr(w,kAXRoleAttribute) isEqual:(__bridge NSString*)kAXWindowRole]){treeFail(state,@"root_role");break;}id doc=attr(w,kAXDocumentAttribute);if(![doc isKindOfClass:[NSString class]]||!expected[doc]||[docs containsObject:doc]){treeFail(state,@"root_document");break;}[docs addObject:doc];NSUInteger index=[state[@"nodes"] count];[state[@"roots"] addObject:@{@"index":@(index),@"document":doc,@"declared_native_window_id":expected[doc]}];if(!walkTree(w,-1,doc,0,state,seen,[NSMutableArray array]))break;}
 if([state[@"enumeration_finished"] boolValue]&&![docs isEqual:[NSSet setWithArray:expected.allKeys]])treeFail(state,@"root_coverage");return state;
}
static NSDictionary *treeJob(NSDictionary *expected){dispatch_semaphore_t done=dispatch_semaphore_create(0);__block NSDictionary *result=nil;dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0),^{@autoreleasepool{result=treeInventory(expected);dispatch_semaphore_signal(done);}});unsigned long long end=nanos()+2000000000ULL;while(dispatch_semaphore_wait(done,DISPATCH_TIME_NOW)!=0){if(nanos()>=end){output(@{@"pid":@(getpid()),@"status":@"owned_tree_deadline",@"admitted":@NO});_exit(79);}pumpFor(0.01);}return result;}
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
  [rows addObject:@{@"document":doc?:@"",@"button_ancestor_matches":@(ancestry),@"candidate_ids":matches,@"fixture_window_id":known?:@0,@"unique_candidate_equals_fixture":((matches.count==1&&[matches[0] isEqual:known])?@YES:@NO),@"AX_geometry":geometry,@"CG_geometry":cgGeometry,@"item_CF_type":@(itemType),@"expected_AX_CF_type":@(AXUIElementGetTypeID()),@"item_detail":identity,@"equals_current_app_root":(rootEqual?@YES:@NO),@"returned_items_equal":(pairEqual?@YES:@NO),@"second_item_equals_app_root":(secondRootEqual?@YES:@NO),@"independent_app_roots_equal_control":(rootControlEqual?@YES:@NO)}];
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
static void output(NSDictionary *out){
 if(![NSJSONSerialization isValidJSONObject:out]){dprintf(2,"owned_output_serialization_failed\n");_exit(81);}
 NSError *error=nil;NSData *d=[NSJSONSerialization dataWithJSONObject:out options:0 error:&error];if(!d||error){dprintf(2,"owned_output_serialization_failed\n");_exit(81);}
 if(d.length>=131072){dprintf(2,"owned_output_limit\n");_exit(82);}const unsigned char *bytes=d.bytes;NSUInteger done=0;
 while(done<d.length){ssize_t n=write(1,bytes+done,d.length-done);if(n<0&&errno==EINTR)continue;if(n<=0){dprintf(2,"owned_output_write_failed\n");_exit(83);}done+=(NSUInteger)n;}
 ssize_t n;do{n=write(1,"\n",1);}while(n<0&&errno==EINTR);if(n!=1){dprintf(2,"owned_output_write_failed\n");_exit(83);}
}
int main(int argc,const char **argv) {@autoreleasepool{
 alarm(8);if(signal(SIGPIPE,SIG_IGN)==SIG_ERR)return 84;if(dprintf(2,"owned_tree_pid:%ld\n",(long)getpid())<=0)return 84;
 if(argc==3&&!strcmp(argv[1],"--output-control")){
  if(!strcmp(argv[2],"output-invalid")){output(@{@"bad":[NSDate date]});return 85;}
  if(!strcmp(argv[2],"output-large")){NSMutableString *large=[NSMutableString string];for(int j=0;j<131072;j++)[large appendString:@"x"];output(@{@"large":large});return 85;}
  if(!strcmp(argv[2],"output-write")){close(1);output(@{@"pid":@(getpid())});return 85;}
  if(!strcmp(argv[2],"output-valid")){output(@{@"pid":@(getpid()),@"status":@"owned_output_control"});return 0;}return 2;
 }
 if(argc==3&&!strcmp(argv[1],"--inventory")){char *end=NULL;long pid=strtol(argv[2],&end,10);if(!end||*end||pid<=1||pid>INT_MAX)return 2;output(@{@"target_pid":@(pid),@"owned_on_screen_windows":@(ownedOnScreen((pid_t)pid))});return 0;}
 NSMutableDictionary *out=[@{@"pid":@(getpid()),@"trusted":@(AXIsProcessTrusted()),@"scope":@"owned-two-window-readonly-AX-tree"} mutableCopy];
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
 NSMutableArray *phases=[NSMutableArray array];BOOL accepted=YES;NSDictionary *tree=nil;
 for(int i=0;i<3;i++){
  if(i==1){[windows[1] orderWindow:NSWindowAbove relativeTo:windows[0].windowNumber];pumpFor(0.1);}
  if(i==2){[windows[1] setFrame:windows[0].frame display:NO];pumpFor(0.1);}
  NSDictionary *p=phase(expected);[phases addObject:p];if(!admitted(p,expected,i==2)){accepted=NO;break;}
  if(i==1){tree=treeJob(expected);if(![tree[@"enumeration_finished"] boolValue]){accepted=NO;break;}}
 }
 for(NSWindow *w in windows)[w close];pumpFor(0.1);
 out[@"tree_inventory"]=tree?:@{};out[@"phases"]=phases;out[@"own_on_screen_after_close"]=@(ownedOnScreen(getpid()));
 if([out[@"own_on_screen_after_close"] unsignedIntegerValue]!=0)accepted=NO;
 out[@"status"]=accepted?@"owned_tree_inventory_recorded":@"owned_fixture_rejected";out[@"admitted"]=(accepted?@YES:@NO);output(out);return accepted?0:78;
}}
