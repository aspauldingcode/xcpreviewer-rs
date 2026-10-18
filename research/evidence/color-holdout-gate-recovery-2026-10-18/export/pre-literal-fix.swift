import SwiftUI
import AppKit
import CryptoKit
import Darwin

@main struct ExportHoldouts {
    @MainActor static func main() throws {
        alarm(10)
        FileHandle.standardError.write(Data("owned_tree_pid:\(getpid())\n".utf8))
        let args=CommandLine.arguments
        func emit(_ value:[String:Any]) throws {
            var data=try JSONSerialization.data(withJSONObject:value,options:[.sortedKeys]);data.append(10)
            FileHandle.standardOutput.write(data)
        }
        if args.count==3 && args[1]=="--output-control" && args[2]=="output-valid" {try emit(["pid":getpid(),"status":"owned_output_control"]);return}
        guard args.count==3 && args[1]=="--fixture" else {throw NSError(domain:"ExportHoldouts",code:2)}
        _=NSApplication.shared;NSApplication.shared.setActivationPolicy(.prohibited);NSApplication.shared.appearance=NSAppearance(named:.aqua)
        guard let space=CGColorSpace(name:CGColorSpace.linearSRGB) else {throw NSError(domain:"ExportHoldouts",code:3)}
        let samples:[[Double]]=[[.0625,.375,.8125],[.2,.6,.9],[.0625,.375,.8125]]
        let modes:[ColorRenderingMode]=[.linear,.extendedLinear]
        for mode in 0..<2 {for phase in 0..<3 {
            let rgb=samples[phase]
            let renderer=ImageRenderer(content:Color(.sRGBLinear,red:rgb[0],green:rgb[1],blue:rgb[2],opacity:1).frame(width:17,height:9).environment(\.colorScheme,.light))
            renderer.scale=1;renderer.colorMode=modes[mode]
            guard let image=renderer.cgImage,let provider=image.dataProvider,let copied=provider.data else {throw NSError(domain:"ExportHoldouts",code:4)}
            let exported=copied as Data
            let providerName="mode\(mode)-phase\(phase)-provider.raw"
            try exported.write(to:URL(fileURLWithPath:args[2]).appendingPathComponent(providerName))
            var bytes=[UInt8](repeating:0xa5,count:4096)
            for y in 0..<9 {for x in 0..<272 {bytes[y*288+x]=0}}
            try bytes.withUnsafeMutableBytes {buffer in
                let info=CGBitmapInfo.floatComponents.rawValue | CGBitmapInfo.byteOrder32Little.rawValue | CGImageAlphaInfo.premultipliedLast.rawValue
                guard let context=CGContext(data:buffer.baseAddress,width:17,height:9,bitsPerComponent:32,bytesPerRow:288,space:space,bitmapInfo:info) else {throw NSError(domain:"ExportHoldouts",code:5)}
                context.setBlendMode(.copy);context.draw(image,in:CGRect(x:0,y:0,width:17,height:9))
                let data=Data(buffer);let name="mode\(mode)-phase\(phase)-readback.raw"
                try data.write(to:URL(fileURLWithPath:args[2]).appendingPathComponent(name))
                try emit(["pid":getpid(),"mode":mode,"phase":phase,"input_linear":rgb,"file":name,"sha256":SHA256.hash(data:data).map {String(format:"%02x",$0)}.joined(),
                          "provider_file":providerName,"provider_bytes":exported.count,"provider_sha256":SHA256.hash(data:exported).map {String(format:"%02x",$0)}.joined(),
                          "image_width":image.width,"image_height":image.height,"image_stride":image.bytesPerRow,"image_bits_per_component":image.bitsPerComponent,"image_bits_per_pixel":image.bitsPerPixel,"image_bitmap_info":image.bitmapInfo.rawValue,"image_alpha_info":image.alphaInfo.rawValue,"image_color_space":image.colorSpace?.name as String? ?? "unnamed",
                          "width":context.width,"height":context.height,"stride":context.bytesPerRow,"bits_per_component":context.bitsPerComponent,"bits_per_pixel":context.bitsPerPixel,"bitmap_info":context.bitmapInfo.rawValue,"alpha_info":context.alphaInfo.rawValue,"color_space":context.colorSpace?.name as String? ?? "unnamed","allocation_bytes":buffer.count])
            }
        }}
    }
}
