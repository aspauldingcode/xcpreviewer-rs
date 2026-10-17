import SwiftUI
import AppKit
import CryptoKit
import Darwin

@main struct QuartzGrayBoundaryOracle {
    @MainActor static func main() throws {
        alarm(10)
        FileHandle.standardError.write(Data("owned_tree_pid:\(getpid())\n".utf8))
        let args = CommandLine.arguments
        func emit(_ value:[String:Any]) throws {
            var data = try JSONSerialization.data(withJSONObject:value,options:[.sortedKeys]);data.append(10)
            FileHandle.standardOutput.write(data)
        }
        if args.count==3 && args[1]=="--output-control" && args[2]=="output-valid" {
            try emit(["pid":getpid(),"status":"owned_output_control"]);return
        }
        guard args.count==3 && args[1]=="--fixture" else { throw NSError(domain:"QuartzGrayBoundary",code:2) }
        _ = NSApplication.shared
        NSApplication.shared.setActivationPolicy(.prohibited)
        NSApplication.shared.appearance=NSAppearance(named:.aqua)
        guard let linear=CGColorSpace(name:CGColorSpace.linearSRGB),
              let srgb=CGColorSpace(name:CGColorSpace.sRGB),
              let nsLinear=NSColorSpace(cgColorSpace:linear) else { throw NSError(domain:"QuartzGrayBoundary",code:3) }
        for phase in 0..<3 {
            let high=phase==1;let value:CGFloat=high ? 0.5:0.25
            guard let direct=CGColor(colorSpace:linear,components:[value,value,value,1]),
                  let roundtrip=direct.converted(to:srgb,intent:.defaultIntent,options:nil) else { throw NSError(domain:"QuartzGrayBoundary",code:4) }
            let bridged=NSColor(Color(.sRGBLinear,red:Double(value),green:Double(value),blue:Double(value),opacity:1))
            guard let normalized=bridged.usingColorSpace(nsLinear) else { throw NSError(domain:"QuartzGrayBoundary",code:5) }
            let colors=[direct,roundtrip,bridged.cgColor,normalized.cgColor]
            for route in 0..<4 {
                var bytes=[UInt8](repeating:0xa5,count:4096)
                for y in 0..<9 { for x in 0..<272 { bytes[y*288+x]=0 } }
                try bytes.withUnsafeMutableBytes { buffer in
                    let info=CGBitmapInfo.floatComponents.rawValue | CGBitmapInfo.byteOrder32Little.rawValue | CGImageAlphaInfo.premultipliedLast.rawValue
                    guard let context=CGContext(data:buffer.baseAddress,width:17,height:9,bitsPerComponent:32,bytesPerRow:288,space:linear,bitmapInfo:info) else { throw NSError(domain:"QuartzGrayBoundary",code:6) }
                    context.setBlendMode(.copy);context.setFillColor(colors[route]);context.fill(CGRect(x:0,y:0,width:17,height:9))
                    let data=Data(buffer);let digest=SHA256.hash(data:data).map { String(format:"%02x",$0) }.joined()
                    let name="phase\(phase)-route\(route).raw"
                    try data.write(to:URL(fileURLWithPath:args[2]).appendingPathComponent(name))
                    try emit(["pid":getpid(),"phase":phase,"route":route,"high":high,"file":name,"sha256":digest,
                              "width":context.width,"height":context.height,"stride":context.bytesPerRow,
                              "bits_per_component":context.bitsPerComponent,"bits_per_pixel":context.bitsPerPixel,
                              "bitmap_info":context.bitmapInfo.rawValue,"alpha_info":context.alphaInfo.rawValue,
                              "color_space":context.colorSpace?.name as String? ?? "unnamed","allocation_bytes":buffer.count,
                              "source_color_space":colors[route].colorSpace?.name as String? ?? "unnamed",
                              "source_components":colors[route].components ?? []])
                }
            }
        }
    }
}
