import SwiftUI
import AppKit
import Darwin

@main struct ColorModeGrayOracle {
    @MainActor static func main() throws {
        alarm(10)
        FileHandle.standardError.write(Data("owned_tree_pid:\(getpid())\n".utf8))
        let args = CommandLine.arguments
        func emit(_ value: [String:Any]) throws {
            var data = try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])
            data.append(10)
            FileHandle.standardOutput.write(data)
        }
        if args.count == 3 && args[1] == "--output-control" && args[2] == "output-valid" {
            try emit(["pid":getpid(),"status":"owned_output_control"])
            return
        }
        guard args.count == 3 && args[1] == "--fixture" else { throw NSError(domain:"GrayOracle",code:2) }
        _ = NSApplication.shared
        NSApplication.shared.setActivationPolicy(.prohibited)
        NSApplication.shared.appearance = NSAppearance(named:.aqua)
        guard let space = CGColorSpace(name:CGColorSpace.linearSRGB) else { throw NSError(domain:"GrayOracle",code:3) }
        let modes: [ColorRenderingMode] = [.linear,.extendedLinear]
        for mode in 0..<2 {
            for phase in 0..<3 {
                let high = phase == 1
                let value = high ? 0.5 : 0.25
                let color = Color(.sRGBLinear,red:value,green:value,high:value,opacity:1)
                let renderer = ImageRenderer(content:color.frame(width:17,height:9).environment(\.colorScheme,.light))
                renderer.scale = 1
                renderer.colorMode = modes[mode]
                guard let image = renderer.cgImage else { throw NSError(domain:"GrayOracle",code:4) }
                for route in 0..<2 {
                    var bytes = [UInt8](repeating:0xa5,count:4096)
                    for y in 0..<9 { for x in 0..<272 { bytes[y*288+x]=0 } }
                    try bytes.withUnsafeMutableBytes { buffer in
                        let info = CGBitmapInfo.floatComponents.rawValue | CGBitmapInfo.byteOrder32Little.rawValue | CGImageAlphaInfo.premultipliedLast.rawValue
                        guard let context = CGContext(data:buffer.baseAddress,width:17,height:9,bitsPerComponent:32,bytesPerRow:288,space:space,bitmapInfo:info) else { throw NSError(domain:"GrayOracle",code:5) }
                        context.setBlendMode(.copy)
                        var callbacks = 0
                        var size = CGSize(width:17,height:9)
                        if route == 0 {
                            context.draw(image,in:CGRect(x:0,y:0,width:17,height:9))
                        } else {
                            renderer.render(rasterizationScale:1) { reported,draw in
                                callbacks += 1
                                size = reported
                                draw(context)
                            }
                            guard callbacks == 1 && size == CGSize(width:17,height:9) else { throw NSError(domain:"GrayOracle",code:6) }
                        }
                        let name = "mode\(mode)-phase\(phase)-route\(route).raw"
                        try Data(buffer).write(to:URL(fileURLWithPath:args[2]).appendingPathComponent(name))
                        try emit(["pid":getpid(),"mode":mode,"phase":phase,"route":route,"high":high,"file":name,
                                  "callbacks":callbacks,"reported_size":[size.width,size.height],
                                  "width":context.width,"height":context.height,"stride":context.bytesPerRow,
                                  "bits_per_component":context.bitsPerComponent,"bits_per_pixel":context.bitsPerPixel,
                                  "bitmap_info":context.bitmapInfo.rawValue,"alpha_info":context.alphaInfo.rawValue,
                                  "color_space":context.colorSpace?.name as String? ?? "unnamed","allocation_bytes":buffer.count,
                                  "image_width":image.width,"image_height":image.height,"image_stride":image.bytesPerRow,
                                  "image_bits_per_component":image.bitsPerComponent,"image_bits_per_pixel":image.bitsPerPixel,
                                  "image_bitmap_info":image.bitmapInfo.rawValue,"image_alpha_info":image.alphaInfo.rawValue,
                                  "image_color_space":image.colorSpace?.name as String? ?? "unnamed"])
                    }
                }
            }
        }
    }
}
