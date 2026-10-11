import SwiftUI
import AppKit
import Darwin
@MainActor final class OwnedModel: ObservableObject { @Published var blue = false; var presses = 0 }
struct OwnedView: View {
 @ObservedObject var model: OwnedModel
 var body: some View { Color(.sRGB, red: model.blue ? 0 : 1, green: 0, blue: model.blue ? 1 : 0, opacity: 1).frame(width:17,height:9) }
}
struct OwnedButton: View { @ObservedObject var model:OwnedModel; var body:some View { Button("Owned increment") { model.presses += 1; model.blue.toggle() } } }
@MainActor final class OwnedTarget:NSObject {
 let model:OwnedModel
 init(_ model:OwnedModel) { self.model=model }
 @objc func press(_ sender:Any?) { model.presses += 1;model.blue.toggle() }
}
@main struct OwnedPlacementButtonReference {
 @MainActor static func main() throws {
  alarm(12)
  guard CommandLine.arguments.count==2 else { throw NSError(domain:"OwnedState",code:1) }
  _ = NSApplication.shared;NSApplication.shared.appearance=NSAppearance(named:.aqua)
  let root=URL(fileURLWithPath:CommandLine.arguments[1]);let model=OwnedModel();let renderer=ImageRenderer(content:OwnedView(model:model));renderer.scale=1;renderer.colorMode = .nonLinear
  let space=CGColorSpace(name:CGColorSpace.sRGB)!;var rows=[[String:Any]]()
  func draw(_ name:String,_ target:ImageRenderer<OwnedView>,_ owner:OwnedModel) throws {
   var bytes=[UInt8](repeating:0xc3,count:16384)
   for y in 0..<9 { for x in 0..<80 { bytes[y*80+x]=x<68 ? 0 : 0xa5 } }
   var count=0;var size=CGSize.zero
   try bytes.withUnsafeMutableBytes { buffer in
    guard let context=CGContext(data:buffer.baseAddress,width:17,height:9,bitsPerComponent:8,bytesPerRow:80,space:space,bitmapInfo:0x4001) else { throw NSError(domain:"OwnedState",code:2) }
    target.render(rasterizationScale:1) { reported,render in count+=1;size=reported;render(context) }
    try Data(buffer).write(to:root.appendingPathComponent(name+".raw"))
    rows.append(["phase":name,"model_blue":owner.blue,"model_identity":String(describing:ObjectIdentifier(owner)),"renderer_identity":String(describing:ObjectIdentifier(target)),"callbacks":count,"size":[size.width,size.height],"width":context.width,"height":context.height,"stride":context.bytesPerRow,"allocation_bytes":buffer.count,"bitmap_info":context.bitmapInfo.rawValue,"alpha_info":context.alphaInfo.rawValue,"bits_per_component":context.bitsPerComponent,"bits_per_pixel":context.bitsPerPixel,"color_space":context.colorSpace?.name as String? ?? "unnamed"])
   }
  }
  func drain() { RunLoop.current.run(until:Date(timeIntervalSinceNow:0.01)) }
  let window=NSWindow(contentRect:NSRect(x:0,y:0,width:160,height:60),styleMask:[.titled],backing:.buffered,defer:false)
  guard let screen=NSScreen.main else { throw NSError(domain:"OwnedState",code:3) }
  let area=screen.visibleFrame
  window.setFrameOrigin(NSPoint(x:area.midX-80,y:area.midY-30))
  let target=OwnedTarget(model);let native=NSButton(title:"Owned native increment",target:target,action:#selector(OwnedTarget.press(_:)))
  window.contentView=native;native.frame=NSRect(x:0,y:0,width:160,height:60)
  window.orderBack(nil);native.layoutSubtreeIfNeeded();native.displayIfNeeded();drain()
  let nativeCenter=window.convertPoint(toScreen:native.convert(NSPoint(x:80,y:30),to:nil))
  let nativeHit=native.accessibilityHitTest(nativeCenter)
  let nativeRole=(nativeHit as? any NSAccessibilityProtocol)?.accessibilityRole()?.rawValue ?? "none"
  var nativePresses=[[String:Any]]()
  for index in 1...3 {
   let accepted=native.accessibilityPerformPress();drain()
   nativePresses.append(["index":index,"accepted":accepted,"model_presses":model.presses,"model_blue":model.blue])
   try draw("native-press-\(index)",renderer,model)
  }
  let nativeSnapshot:[String:Any]=["role":native.accessibilityRole()?.rawValue ?? "none","hit_role":nativeRole,"screen_point":[nativeCenter.x,nativeCenter.y],"point_in_display":area.contains(nativeCenter),"visible":window.isVisible,"key":window.isKeyWindow,"presses":nativePresses]
  model.blue=false;model.presses=0;window.orderOut(nil)
  let host=NSHostingView(rootView:OwnedButton(model:model));window.contentView=host;host.frame=NSRect(x:0,y:0,width:160,height:60);host.layoutSubtreeIfNeeded();drain()
  defer { window.close() }
  var inspected=0;var found:(any NSAccessibilityProtocol)?;var roles=[String]()
  func find(_ item:Any,_ depth:Int) {
   guard depth<8,inspected<64 else { return };inspected+=1
   guard let node=item as? any NSAccessibilityProtocol else { return }
   let role=node.accessibilityRole()?.rawValue ?? "none";roles.append(role)
   if role==NSAccessibility.Role.button.rawValue { found=node;return }
   for child in node.accessibilityChildren() ?? [] { if found==nil { find(child,depth+1) } }
  }
  find(host,0)
  let hidden:[String:Any]=["button_found":found != nil,"roles":roles,"inspected":inspected,"visible":window.isVisible]
  window.orderBack(nil);host.layoutSubtreeIfNeeded();host.displayIfNeeded();drain()
  inspected=0;found=nil;roles=[];find(host,0)
  let visible:[String:Any]=["button_found":found != nil,"roles":roles,"inspected":inspected,"visible":window.isVisible,"key":window.isKeyWindow]
  inspected=0;found=nil;roles=[]
  for child in host.accessibilityChildrenInNavigationOrder() ?? [] { if found==nil { find(child,0) } }
  let navigation:[String:Any]=["button_found":found != nil,"roles":roles,"inspected":inspected]
  let center=window.convertPoint(toScreen:host.convert(NSPoint(x:80,y:30),to:nil))
  inspected=0;found=nil;roles=[]
  let hit=host.accessibilityHitTest(center)
  if let hit { find(hit,0) }
  let hitSnapshot:[String:Any]=["button_found":found != nil,"roles":roles,"inspected":inspected,"returned":hit != nil,"screen_point":[center.x,center.y],"point_in_display":area.contains(center)]
  var presses=[[String:Any]]();try draw("initial",renderer,model)
  if let button=found {
   for index in 1...3 {
    let accepted=button.accessibilityPerformPress();drain()
    presses.append(["index":index,"accepted":accepted,"model_presses":model.presses,"model_blue":model.blue])
    try draw("press-\(index)",renderer,model)
   }
  }
  window.close()
  try JSONSerialization.data(withJSONObject:["rows":rows,"owned_windows":NSApplication.shared.windows.count,"roles":roles,"inspected":inspected,"button_found":found != nil,"presses":presses,"hidden":hidden,"visible":visible,"navigation":navigation,"hit":hitSnapshot,"native_control":nativeSnapshot,"visible_frame":[area.minX,area.minY,area.width,area.height]],options:[.sortedKeys]).write(to:root.appendingPathComponent("result.json"))
 }
}
