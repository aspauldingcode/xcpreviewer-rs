// Research event-pump variant. Execution requires scoped review.
// Diagnostic research revision. Native execution requires scoped review.
// Owned public-API research interaction fixture. No Xcode, explicit activation, synthesized physical event or permission request. AXPress targets owned buttons only.
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
static void pumpFor(double seconds);
static void output(NSDictionary *out);
@interface OwnedCounter : NSObject
@property(nonatomic,strong) NSButton *aButton;
@property(nonatomic,strong) NSButton *bButton;
@property NSUInteger a;
@property NSUInteger b;
@property NSUInteger unknown;
-(void)pressed:(id)sender;
@end
@implementation OwnedCounter
-(void)pressed:(id)sender {if(sender==self.aButton)self.a++;else if(sender==self.bButton)self.b++;else self.unknown++;}
@end
@interface OwnedBinding : NSObject
@property(nonatomic,strong) id window;
@property(nonatomic,strong) id button;
@property(nonatomic,strong) NSString *document;
@property CGRect rect;
@end
@implementation OwnedBinding
@end
static BOOL ownAX(AXUIElementRef e){if(!e||CFGetTypeID(e)!=AXUIElementGetTypeID())return NO;pid_t p=-1;return AXUIElementGetPid(e,&p)==kAXErrorSuccess&&p==getpid();}
static BOOL collectionFailure(NSMutableDictionary *failure,NSString *reason,NSString *role,id error){
 if(!failure.count){failure[@"reason"]=reason;failure[@"role"]=role?:@"";failure[@"AX_error"]=error?:[NSNull null];}return NO;
}
static BOOL collectButtons(AXUIElementRef e,int depth,NSMutableArray *found,NSMutableDictionary *failure){
 if(depth<0)return collectionFailure(failure,@"depth_limit",nil,nil);if(!ownAX(e))return collectionFailure(failure,@"type_or_own_PID",nil,nil);
 CFTypeRef rr=NULL;AXError re=AXUIElementCopyAttributeValue(e,kAXRoleAttribute,&rr);id role=rr?CFBridgingRelease(rr):nil;if(re!=kAXErrorSuccess||![role isKindOfClass:[NSString class]])return collectionFailure(failure,@"role_read",nil,@(re));
 if([role length]>256)return collectionFailure(failure,@"role_length_limit",nil,nil);
 if([role isEqual:(__bridge NSString*)kAXButtonRole]){CFTypeRef ir=NULL;AXError ie=AXUIElementCopyAttributeValue(e,kAXIdentifierAttribute,&ir);id identifier=ir?CFBridgingRelease(ir):nil;if(ie!=kAXErrorSuccess&&ie!=kAXErrorAttributeUnsupported)return collectionFailure(failure,@"identifier_read",role,@(ie));if(ie==kAXErrorSuccess&&![identifier isKindOfClass:[NSString class]])return collectionFailure(failure,@"identifier_type",role,@(ie));if([identifier isEqual:@"owned-binding-button"]){[found addObject:(__bridge id)e];if(found.count>2)return collectionFailure(failure,@"match_limit",role,nil);}}
 CFTypeRef cr=NULL;AXError ce=AXUIElementCopyAttributeValue(e,kAXChildrenAttribute,&cr);id children=cr?CFBridgingRelease(cr):nil;
 // Only declared owned NSButton leaves with null Unsupported/NoValue children may omit AXChildren. Other errors fail closed.
 if((ce==kAXErrorAttributeUnsupported||ce==kAXErrorNoValue)&&!children&&[role isEqual:(__bridge NSString*)kAXButtonRole])return YES;
 if(ce!=kAXErrorSuccess)return collectionFailure(failure,@"children_read",role,@(ce));
 if(![children isKindOfClass:[NSArray class]]||[children count]>32)return collectionFailure(failure,@"children_type_or_count",role,@(ce));
 for(id c in children)if(!collectButtons((__bridge AXUIElementRef)c,depth-1,found,failure))return NO;
 return YES;
}
static NSDictionary *bindingCheck(NSDictionary *expected,NSString *target,OwnedBinding *prior){
 AXUIElementRef app=AXUIElementCreateApplication(getpid());AXUIElementSetMessagingTimeout(app,0.2);CFTypeRef raw=NULL;AXError er=AXUIElementCopyAttributeValue(app,kAXWindowsAttribute,&raw);CFRelease(app);id ws=raw?CFBridgingRelease(raw):nil;
 if(er!=kAXErrorSuccess||![ws isKindOfClass:[NSArray class]]||[ws count]!=2)return @{@"accepted":@NO,@"reason":@"windows_unavailable"};
 NSMutableSet *docs=[NSMutableSet set];id selected=nil;
 for(id x in ws){AXUIElementRef w=(__bridge AXUIElementRef)x;if(!ownAX(w)||![attr(w,kAXRoleAttribute) isEqual:(__bridge NSString*)kAXWindowRole])return @{@"accepted":@NO,@"reason":@"window_identity_or_role"};id doc=attr(w,kAXDocumentAttribute);if(![doc isKindOfClass:[NSString class]]||!expected[doc]||[docs containsObject:doc])return @{@"accepted":@NO,@"reason":@"window_document"};[docs addObject:doc];if([doc isEqual:target])selected=x;}
 if(!selected||![docs isEqual:[NSSet setWithArray:expected.allKeys]])return @{@"accepted":@NO,@"reason":@"target_document_missing"};
 AXUIElementRef w=(__bridge AXUIElementRef)selected;CGRect rect;NSMutableDictionary *geometry=[NSMutableDictionary dictionary];if(!rectFor(w,&rect,geometry))return @{@"accepted":@NO,@"reason":@"window_geometry"};
 NSArray *all=CFBridgingRelease(CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly|kCGWindowListExcludeDesktopElements,kCGNullWindowID));if(!all)return @{@"accepted":@NO,@"reason":@"CG_unavailable"};NSMutableArray *matches=[NSMutableArray array];NSUInteger own=0;
 for(NSDictionary *c in all)if([c[(__bridge NSString*)kCGWindowOwnerPID] intValue]==getpid()&&[c[(__bridge NSString*)kCGWindowLayer] intValue]==0){own++;CGRect other;if(CGRectMakeWithDictionaryRepresentation((__bridge CFDictionaryRef)c[(__bridge NSString*)kCGWindowBounds],&other)&&CGRectEqualToRect(rect,other))[matches addObject:c[(__bridge NSString*)kCGWindowNumber]];}
 if(own!=2||matches.count!=1||![matches[0] isEqual:expected[target]])return @{@"accepted":@NO,@"reason":@"CG_identity_not_unique",@"candidates":matches};
 NSMutableArray *buttons=[NSMutableArray array];NSMutableDictionary *traversalFailure=[NSMutableDictionary dictionary];if(!collectButtons(w,5,buttons,traversalFailure))return @{@"accepted":@NO,@"reason":@"button_traversal_rejected",@"detail":traversalFailure,@"partial_button_matches":@(buttons.count)};if(buttons.count!=1)return @{@"accepted":@NO,@"reason":@"button_not_unique",@"button_matches":@(buttons.count)};id button=buttons[0];id ancestor=attr((__bridge AXUIElementRef)button,kAXWindowAttribute);if(!ancestor||!CFEqual((__bridge CFTypeRef)ancestor,w))return @{@"accepted":@NO,@"reason":@"button_ancestry"};
 if(prior&&(![prior.document isEqual:target]||!CFEqual((__bridge CFTypeRef)prior.window,w)||!CFEqual((__bridge CFTypeRef)prior.button,(__bridge CFTypeRef)button)||!CGRectEqualToRect(prior.rect,rect)))return @{@"accepted":@NO,@"reason":@"binding_changed"};
 CFArrayRef rawActions=NULL;AXError actionError=AXUIElementCopyActionNames((__bridge AXUIElementRef)button,&rawActions);id actions=rawActions?CFBridgingRelease(rawActions):nil;if(actionError!=kAXErrorSuccess||![actions isKindOfClass:[NSArray class]]||[actions count]>32||![actions containsObject:(__bridge NSString*)kAXPressAction])return @{@"accepted":@NO,@"reason":@"AXPress_unavailable",@"AX_action_names_error":@(actionError)};
 OwnedBinding *binding=[OwnedBinding new];binding.window=selected;binding.button=button;binding.document=target;binding.rect=rect;
 return @{@"accepted":@YES,@"reason":@"validated",@"document":target,@"native_window_id":expected[target],@"AXPress_available":@YES,@"AX_action_names_error":@(actionError),@"AX_action_name_count":@([actions count]),@"binding":binding};
}
static NSDictionary *safeBinding(NSDictionary *r){NSMutableDictionary *d=[r mutableCopy];[d removeObjectForKey:@"binding"];return d;}
static NSDictionary *inputJob(NSDictionary *(^job)(void)){
 dispatch_semaphore_t done=dispatch_semaphore_create(0);__block NSDictionary *result=nil;dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0),^{@autoreleasepool{result=job();dispatch_semaphore_signal(done);}});unsigned long long end=nanos()+2000000000ULL;
 while(dispatch_semaphore_wait(done,DISPATCH_TIME_NOW)!=0){if(nanos()>=end){output(@{@"pid":@(getpid()),@"status":@"owned_input_deadline",@"admitted":@NO});_exit(79);}pumpFor(0.01);}
 return result;
}
static NSDictionary *pressBound(NSDictionary *expected,NSString *target,OwnedBinding *binding){
 NSDictionary *fresh=bindingCheck(expected,target,binding);if(![fresh[@"accepted"] boolValue])return @{@"action_attempted":@NO,@"validation":safeBinding(fresh)};
 AXError er=AXUIElementPerformAction((__bridge AXUIElementRef)binding.button,kAXPressAction);return @{@"action_attempted":@YES,@"AX_press_error":@(er),@"validation":safeBinding(fresh)};
}
static NSDictionary *counts(OwnedCounter *c){return @{@"a":@(c.a),@"b":@(c.b),@"unknown":@(c.unknown)};}
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
static void output(NSDictionary *out){NSData *d=[NSJSONSerialization dataWithJSONObject:out options:0 error:NULL];if(d){write(1,d.bytes,d.length);write(1,"\n",1);}}
int main(int argc,const char **argv) {@autoreleasepool{
 alarm(8);
 if(argc==3&&!strcmp(argv[1],"--inventory")){char *end=NULL;long pid=strtol(argv[2],&end,10);if(!end||*end||pid<=1||pid>INT_MAX)return 2;output(@{@"target_pid":@(pid),@"owned_on_screen_windows":@(ownedOnScreen((pid_t)pid))});return 0;}
 NSMutableDictionary *out=[@{@"pid":@(getpid()),@"trusted":@(AXIsProcessTrusted()),@"scope":@"owned-two-window-AXPress-interaction"} mutableCopy];
 if(![out[@"trusted"] boolValue]){out[@"status"]=@"accessibility_prerequisite_missing";output(out);return 77;}
 if(argc==1){out[@"status"]=@"trusted_preflight_only";output(out);return 0;}
 if(argc!=3||strcmp(argv[1],"--fixture"))return 2;
 [NSApplication sharedApplication];[NSApp setActivationPolicy:NSApplicationActivationPolicyAccessory];[NSApp finishLaunching];
 NSMutableArray<NSWindow*> *windows=[NSMutableArray array];NSMutableDictionary *expected=[NSMutableDictionary dictionary];OwnedCounter *counter=[OwnedCounter new];NSString *target=nil;NSMutableArray *steps=[NSMutableArray array];__block OwnedBinding *binding=nil;
 for(int i=0;i<2;i++){
  NSWindow *w=[[NSWindow alloc] initWithContentRect:NSMakeRect(160+i*240,160,200,100) styleMask:NSWindowStyleMaskTitled backing:NSBackingStoreBuffered defer:NO];w.title=@"Owned binding sentinel";w.releasedWhenClosed=NO;w.animationBehavior=NSWindowAnimationBehaviorNone;
  NSURL *url=[NSURL fileURLWithPath:[NSString stringWithFormat:@"%s/%c.xcodeproj",argv[2],'a'+i]];w.representedURL=url;
  NSButton *b=[[NSButton alloc] initWithFrame:NSMakeRect(30,30,130,30)];b.title=@"Same control";b.accessibilityIdentifier=@"owned-binding-button";b.target=counter;b.action=@selector(pressed:);if(i==0)counter.aButton=b;else{counter.bButton=b;target=url.absoluteString;}[w.contentView addSubview:b];[w orderBack:nil];[windows addObject:w];expected[url.absoluteString]=@(w.windowNumber);
 }
 pumpFor(0.15);
 NSMutableArray *phases=[NSMutableArray array];BOOL accepted=YES;
 for(int i=0;i<3;i++){
  if(i==1){[windows[1] orderWindow:NSWindowAbove relativeTo:windows[0].windowNumber];pumpFor(0.1);}
  if(i==2){[windows[1] setFrame:windows[0].frame display:NO];pumpFor(0.1);}
  NSDictionary *p=phase(expected);[phases addObject:p];if(!admitted(p,expected,i==2)){accepted=NO;break;}
  if(i==1){
   NSDictionary *s=inputJob(^{return bindingCheck(expected,target,nil);});binding=s[@"binding"];[steps addObject:@{@"kind":@"selection",@"validation":safeBinding(s),@"counts":counts(counter)}];if(!binding){accepted=NO;break;}
   NSDictionary *press=inputJob(^{return pressBound(expected,target,binding);});pumpFor(0.1);[steps addObject:@{@"kind":@"positive",@"result":press,@"counts":counts(counter)}];if(![press[@"action_attempted"] boolValue]||[press[@"AX_press_error"] intValue]!=0||counter.a!=0||counter.b!=1||counter.unknown!=0){accepted=NO;break;}
   NSRect original=windows[1].frame;[windows[1] setFrame:NSOffsetRect(original,10,0) display:NO];pumpFor(0.1);NSDictionary *stale=inputJob(^{return pressBound(expected,target,binding);});[steps addObject:@{@"kind":@"stale",@"result":stale,@"counts":counts(counter)}];if([stale[@"action_attempted"] boolValue]||![stale[@"validation"][@"reason"] isEqual:@"binding_changed"]||counter.a!=0||counter.b!=1||counter.unknown!=0){accepted=NO;break;}[windows[1] setFrame:original display:NO];pumpFor(0.1);
  }
  if(i==2){NSDictionary *overlap=inputJob(^{return pressBound(expected,target,binding);});[steps addObject:@{@"kind":@"overlap",@"result":overlap,@"counts":counts(counter)}];if([overlap[@"action_attempted"] boolValue]||![overlap[@"validation"][@"reason"] isEqual:@"CG_identity_not_unique"]||counter.a!=0||counter.b!=1||counter.unknown!=0){accepted=NO;break;}}

 }
 for(NSWindow *w in windows)[w close];pumpFor(0.1);
 out[@"interaction_steps"]=steps;out[@"callback_counts"]=counts(counter);out[@"phases"]=phases;out[@"own_on_screen_after_close"]=@(ownedOnScreen(getpid()));
 if([out[@"own_on_screen_after_close"] unsignedIntegerValue]!=0)accepted=NO;
 out[@"status"]=accepted?@"owned_interaction_control_admitted":@"owned_fixture_rejected";out[@"admitted"]=(accepted?@YES:@NO);output(out);return accepted?0:78;
}}
