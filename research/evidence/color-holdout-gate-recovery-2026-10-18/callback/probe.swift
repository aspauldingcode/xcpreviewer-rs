import SwiftUI
import AppKit
import CryptoKit
import Darwin

@main struct HalfSourceHoldouts {
    @MainActor static func main() throws {
        alarm(10)
        FileHandle.standardError.write(Data("owned_tree_pid:\(getpid())\n".utf8))
        let args=CommandLine.arguments
        func emit(_ value:[String:Any]) throws {
            var data=try JSONSerialization.data(withJSONObject:value,options:[.sortedKeys]);data.append(10)
            FileHandle.standardOutput.write(data)
        }
        if args.count==3 && args[1]=="--output-control" && args[2]=="output-valid" {
            try emit(["pid":getpid(),"status":"owned_output_control"]);return
        }
        guard args.count==3 && args[1]=="--fixture" else { throw NSError(domain:"HalfHoldouts",code:2) }
        _=NSApplication.shared
        NSApplication.shared.setActivationPolicy(.prohibited)
        NSApplication.shared.appearance=NSAppearance(named:.aqua)
        guard let linear=CGColorSpace(name:CGColorSpace.linearSRGB),let srgb=CGColorSpace(name:CGColorSpace.sRGB) else { throw NSError(domain:"HalfHoldouts",code:3) }
        let samples:[[Double]]=[[0.0625,0.375,0.8125],[0.2,0.6,0.9],[0.0625,0.375,0.8125]]
        let modes:[ColorRenderingMode]=[.linear,.extendedLinear]
        for mode in 0..<2 { for phase in 0..<3 {
            let rgb=samples[phase]
            let encoded=rgb.map { $0 <= 0.0031308 ? 12.92*$0 : 1.055*pow($0,1.0/2.4)-0.055 }
            let halves=encoded.map { Float16($0) }
            guard let direct=CGColor(colorSpace:linear,components:rgb.map { CGFloat($0) }+[1]),
                  let quantized=CGColor(colorSpace:srgb,components:halves.map { CGFloat(Float($0)) }+[1]) else { throw NSError(domain:"HalfHoldouts",code:4) }
            let renderer=ImageRenderer(content:Color(.sRGBLinear,red:rgb[0],green:rgb[1],blue:rgb[2],opacity:1).frame(width:17,height:9).environment(\.colorScheme,.light))
            renderer.scale=1;renderer.colorMode=modes[mode]
            for route in 0..<3 {
                var bytes=[UInt8](repeating:0xa5,count:4096)
                for y in 0..<9 { for x in 0..<272 { bytes[y*288+x]=0 } }
                try bytes.withUnsafeMutableBytes { buffer in
                    let info=CGBitmapInfo.floatComponents.rawValue | CGBitmapInfo.byteOrder32Little.rawValue | CGImageAlphaInfo.premultipliedLast.rawValue
                    guard let context=CGContext(data:buffer.baseAddress,width:17,height:9,bitsPerComponent:32,bytesPerRow:288,space:linear,bitmapInfo:info) else { throw NSError(domain:"HalfHoldouts",code:5) }
                    context.setBlendMode(.copy)
                    var callbacks=0;var size=CGSize(width:17,height:9)
                    if route<2 {
                        context.setFillColor(route==0 ? direct:quantized);context.fill(CGRect(x:0,y:0,width:17,height:9))
                    } else {
                        renderer.render(rasterizationScale:1) { reported,draw in callbacks+=1;size=reported;draw(context) }
                        guard callbacks==1 && size==CGSize(width:17,height:9) else { throw NSError(domain:"HalfHoldouts",code:6) }
                    }
                    let data=Data(buffer);let digest=SHA256.hash(data:data).map { String(format:"%02x",$0) }.joined()
                    let name="mode\(mode)-phase\(phase)-route\(route).raw"
                    try data.write(to:URL(fileURLWithPath:args[2]).appendingPathComponent(name))
                    try emit(["pid":getpid(),"mode":mode,"phase":phase,"route":route,"file":name,"sha256":digest,
                              "input_linear":rgb,"encoded_half_bits":halves.map { Int($0.bitPattern) },
                              "encoded_half_components":halves.map { Double($0) },"callbacks":callbacks,"reported_size":[size.width,size.height],
                              "width":context.width,"height":context.height,"stride":context.bytesPerRow,
                              "bits_per_component":context.bitsPerComponent,"bits_per_pixel":context.bitsPerPixel,
                              "bitmap_info":context.bitmapInfo.rawValue,"alpha_info":context.alphaInfo.rawValue,
                              "color_space":context.colorSpace?.name as String? ?? "unnamed","allocation_bytes":buffer.count])
                }
            }
        } }
    }
}
