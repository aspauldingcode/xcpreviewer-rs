import SwiftUI
import AppKit
import Darwin
@MainActor final class OwnedBindingProbe {
 var binding: Binding<Bool>?; var captures=0; var lastBodyBlue=false; var lastToken=0;var lastDark=false
 func capture(_ value:Binding<Bool>,blue:Bool,token:Int,dark:Bool){lastDark=dark;lastToken=token;binding=value;captures+=1;lastBodyBlue=blue}
}
@MainActor struct OwnedStateView: View {
 @State private var blue=false
 @Environment(\.colorScheme) private var scheme
 let probe:OwnedBindingProbe; let token:Int
 var body:some View { color() }
 private func color()->some View {
  let dark=scheme == .dark
  probe.capture($blue,blue:blue,token:token,dark:dark)
  return Color(.sRGB,red:blue ? 0:1,green:dark ? 1:0,blue:blue && !dark ? 1:0,opacity:1).frame(width:17,height:9)
 }
}
@MainActor struct OwnedIdentityRoot: View {
 let probe:OwnedBindingProbe; let token:Int;let dark:Bool
 var body:some View { OwnedStateView(probe:probe,token:token).environment(\.colorScheme,dark ? .dark:.light).id(token) }
}
@main struct OwnedStateSchemeReference {
 @MainActor static func main() throws {
  alarm(12);guard CommandLine.arguments.count==2 else{throw NSError(domain:"OwnedBinding",code:1)}
  _ = NSApplication.shared;NSApplication.shared.appearance=NSAppearance(named:.aqua)
  let root=URL(fileURLWithPath:CommandLine.arguments[1]),probe=OwnedBindingProbe(),content=OwnedIdentityRoot(probe:probe,token:0,dark:false)
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
    rows.append(["phase":name,"renderer_identity":String(describing:ObjectIdentifier(target)),"probe_identity":String(describing:ObjectIdentifier(observer)),"root_dark":target.content.dark,"last_dark":observer.lastDark,"root_token":target.content.token,"last_token":observer.lastToken,"captures":observer.captures,"last_body_blue":observer.lastBodyBlue,"binding_present":observer.binding != nil,"last_captured_getter":observer.binding?.wrappedValue ?? false,"callbacks":callbacks,"size":[size.width,size.height],"width":context.width,"height":context.height,"stride":context.bytesPerRow,"allocation_bytes":buffer.count,"bitmap_info":context.bitmapInfo.rawValue,"alpha_info":context.alphaInfo.rawValue,"bits_per_component":context.bitsPerComponent,"bits_per_pixel":context.bitsPerPixel,"color_space":context.colorSpace?.name as String? ?? "unnamed"])
   }
  }
  func drain(){RunLoop.current.run(until:Date(timeIntervalSinceNow:0.01))}
  try draw("initial",renderer,probe)
  guard let held=probe.binding else{throw NSError(domain:"OwnedBinding",code:3)}
  func set(_ name:String,_ binding:Binding<Bool>,_ value:Bool){let before=binding.wrappedValue;binding.wrappedValue=value;actions.append(["action":name,"before":before,"after":binding.wrappedValue])}
  set("held-true",held,true);try draw("state-blue",renderer,probe)
  renderer.content=OwnedIdentityRoot(probe:probe,token:0,dark:true);try draw("dark-content",renderer,probe);try draw("dark-repeat",renderer,probe)
  set("held-false",held,false);try draw("dark-false",renderer,probe)
  set("held-true-again",held,true);try draw("dark-true",renderer,probe)
  renderer.content=OwnedIdentityRoot(probe:probe,token:0,dark:false);try draw("light-return",renderer,probe)
  renderer.content=OwnedIdentityRoot(probe:probe,token:1,dark:true);try draw("dark-reset",renderer,probe)
  guard let current=probe.binding else{throw NSError(domain:"OwnedBinding",code:4)}
  set("old-held-false",held,false);try draw("old-binding",renderer,probe)
  set("current-true",current,true);try draw("new-positive",renderer,probe)
  withExtendedLifetime([held,current]){}
  try JSONSerialization.data(withJSONObject:["rows":rows,"actions":actions,"owned_windows":NSApplication.shared.windows.count],options:[.sortedKeys]).write(to:root.appendingPathComponent("result.json"))
 }
}
