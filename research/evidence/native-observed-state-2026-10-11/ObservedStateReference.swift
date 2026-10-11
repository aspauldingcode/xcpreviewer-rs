import SwiftUI
import AppKit
import Darwin
@MainActor final class OwnedModel: ObservableObject { @Published var blue = false }
struct OwnedView: View {
 @ObservedObject var model: OwnedModel
 var body: some View { Color(.sRGB, red: model.blue ? 0 : 1, green: 0, blue: model.blue ? 1 : 0, opacity: 1).frame(width:17,height:9) }
}
@main struct OwnedStateReference {
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
  try draw("initial",renderer,model);try draw("repeat",renderer,model)
  model.blue=true;try draw("changed-immediate",renderer,model);drain();try draw("changed-drained",renderer,model)
  let fresh=ImageRenderer(content:OwnedView(model:model));fresh.scale=1;fresh.colorMode = .nonLinear;try draw("fresh-same-model",fresh,model)
  model.blue=false;try draw("reset-immediate",renderer,model);drain();try draw("reset-drained",renderer,model)
  let replacement=OwnedModel();let reset=ImageRenderer(content:OwnedView(model:replacement));reset.scale=1;reset.colorMode = .nonLinear;try draw("fresh-default-model",reset,replacement)
  try JSONSerialization.data(withJSONObject:["rows":rows,"owned_windows":NSApplication.shared.windows.count],options:[.sortedKeys]).write(to:root.appendingPathComponent("result.json"))
 }
}
