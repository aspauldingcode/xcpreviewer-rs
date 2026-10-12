import SwiftUI
import AppKit
import Darwin
@MainActor final class OwnedBindingProbe {
 var binding: Binding<Bool>?; var captures=0; var lastBodyBlue=false; var lastToken=0;var lastAlternate=false
 func capture(_ value:Binding<Bool>,blue:Bool,token:Int,alternate:Bool){lastAlternate=alternate;lastToken=token;binding=value;captures+=1;lastBodyBlue=blue}
}
@MainActor struct OwnedStateView: View {
 @State private var blue=false
 let probe:OwnedBindingProbe; let token:Int;let alternate:Bool
 var body:some View { color() }
 private func color()->some View {
  probe.capture($blue,blue:blue,token:token,alternate:alternate)
  return Color(.sRGB,red:blue ? 0:1,green:alternate ? 1:0,blue:blue && !alternate ? 1:0,opacity:1).frame(width:17,height:9)
 }
}
@MainActor struct OwnedIdentityRoot: View {
 let probe:OwnedBindingProbe; let token:Int;let alternate:Bool
 var body:some View { OwnedStateView(probe:probe,token:token,alternate:alternate).id(token) }
}
@main struct OwnedStateContentReference {
 @MainActor static func main() throws {
  alarm(12);guard CommandLine.arguments.count==2 else{throw NSError(domain:"OwnedBinding",code:1)}
  _ = NSApplication.shared;NSApplication.shared.appearance=NSAppearance(named:.aqua)
  let root=URL(fileURLWithPath:CommandLine.arguments[1]),probe=OwnedBindingProbe(),content=OwnedIdentityRoot(probe:probe,token:0,alternate:false)
  let renderer=ImageRenderer(content:content);renderer.scale=1;renderer.colorMode = .nonLinear
  let space=CGColorSpace(name:CGColorSpace.sRGB)!;var rows=[[String:Any]](),actions=[[String:Any]]()
  func draw(_ name:String,_ target:ImageRenderer<OwnedIdentityRoot>,_ observer:OwnedBindingProbe)throws{
   var bytes=[UInt8](repeating:0xc3,count:16384)
   for y in 0..<9{for x in 0..<80{bytes[y*80+x]=x<68 ? 0:0xa5}}
   var callbacks=0,size=CGSize.zero
   try bytes.withUnsafeMutableBytes{buffer in
    guard let context=CGContext(data:buffer.baseAddress,width:17,height:9,bitsPerComponent:8,bytesPerRow:80,space:space,bitmapInfo:0x4001)else{throw NSError(domain:"OwnedBinding",code:2)}
    target.render(rasterizationScale:1){reported,render in callbacks+=1;size=reported;render(context)}
    try Data(buffer).write(to:root.appendingPathComponent(name+".raw"))
    rows.append(["phase":name,"renderer_identity":String(describing:ObjectIdentifier(target)),"probe_identity":String(describing:ObjectIdentifier(observer)),"alternate":target.content.alternate,"last_alternate":observer.lastAlternate,"root_token":target.content.token,"last_token":observer.lastToken,"captures":observer.captures,"last_body_blue":observer.lastBodyBlue,"binding_present":observer.binding != nil,"last_captured_getter":observer.binding?.wrappedValue ?? false,"callbacks":callbacks,"size":[size.width,size.height],"width":context.width,"height":context.height,"stride":context.bytesPerRow,"allocation_bytes":buffer.count,"bitmap_info":context.bitmapInfo.rawValue,"alpha_info":context.alphaInfo.rawValue,"bits_per_component":context.bitsPerComponent,"bits_per_pixel":context.bitsPerPixel,"color_space":context.colorSpace?.name as String? ?? "unnamed"])
   }
  }
  func drain(){RunLoop.current.run(until:Date(timeIntervalSinceNow:0.01))}
  try draw("initial",renderer,probe);try draw("repeat",renderer,probe)
  guard let held=probe.binding else{throw NSError(domain:"OwnedBinding",code:3)}
  let before=held.wrappedValue;held.wrappedValue=true;actions.append(["action":"set-true","before":before,"after":held.wrappedValue])
  try draw("changed-immediate",renderer,probe);drain();try draw("changed-drained",renderer,probe)
  func set(_ name:String,_ value:Bool){let before=held.wrappedValue;held.wrappedValue=value;actions.append(["action":name,"before":before,"after":held.wrappedValue])}
  renderer.content=OwnedIdentityRoot(probe:probe,token:0,alternate:true);try draw("alternate-content",renderer,probe);try draw("alternate-repeat",renderer,probe)
  set("held-false",false);try draw("held-false",renderer,probe)
  set("held-true",true);try draw("held-true",renderer,probe)
  renderer.content=OwnedIdentityRoot(probe:probe,token:0,alternate:false);try draw("original-content",renderer,probe)
  renderer.content=OwnedIdentityRoot(probe:probe,token:1,alternate:false);try draw("changed-id",renderer,probe)
  set("old-held-false",false);try draw("old-binding-after-reset",renderer,probe)
  withExtendedLifetime(held){}
  try JSONSerialization.data(withJSONObject:["rows":rows,"actions":actions,"owned_windows":NSApplication.shared.windows.count],options:[.sortedKeys]).write(to:root.appendingPathComponent("result.json"))
 }
}
