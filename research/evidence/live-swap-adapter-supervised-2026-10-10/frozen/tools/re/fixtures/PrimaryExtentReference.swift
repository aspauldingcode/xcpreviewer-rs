import SwiftUI
import AppKit

@main
struct PrimaryExtentReference {
    @MainActor static func main() throws {
        let args = CommandLine.arguments
        guard args.count == 7, let variant = Int(args[2]), [4,8,18,19].contains(variant),
              let width = Int(args[3]), let height = Int(args[4]), let stride = Int(args[5]),
              (1...64).contains(width), (1...64).contains(height), stride >= width*4,
              stride <= 256, ["forward","reverse"].contains(args[6]) else {
            throw NSError(domain:"PrimaryExtent",code:1)
        }
        _ = NSApplication.shared
        NSApplication.shared.appearance = NSAppearance(named:.aqua)
        let alphas = [4:[4,2,8],8:[4,4,4],18:[7,7,1],19:[3,1,5]][variant]!
        let red = Color(.sRGB,red:1,green:0,blue:0,opacity:Double(alphas[0])/8)
        let green = Color(.sRGB,red:0,green:1,blue:0,opacity:Double(alphas[1])/8)
        let blue = Color(.sRGB,red:0,green:0,blue:1,opacity:Double(alphas[2])/8)
        let stack = ZStack {
            if args[6] == "reverse" { green; red; blue } else { blue; red; green }
        }.frame(width:CGFloat(width),height:CGFloat(height))
        let renderer = ImageRenderer(content:stack)
        renderer.scale = 1; renderer.colorMode = .nonLinear
        guard let space = CGColorSpace(name:CGColorSpace.sRGB) else { throw NSError(domain:"PrimaryExtent",code:2) }
        var bytes = [UInt8](repeating:0xc3,count:16384)
        for row in 0..<height {
            for col in 0..<stride { bytes[row*stride+col] = col < width*4 ? 0 : 0xa5 }
        }
        try bytes.withUnsafeMutableBytes { buffer in
            guard let context = CGContext(data:buffer.baseAddress,width:width,height:height,
                bitsPerComponent:8,bytesPerRow:stride,space:space,bitmapInfo:0x4001) else {
                throw NSError(domain:"PrimaryExtent",code:3)
            }
            context.setBlendMode(.normal)
            var callbacks = 0; var size = CGSize.zero
            renderer.render(rasterizationScale:1) { reported, draw in callbacks += 1; size = reported; draw(context) }
            guard callbacks == 1, size == CGSize(width:width,height:height) else { throw NSError(domain:"PrimaryExtent",code:4) }
            let metadata:[String:Any] = ["width":context.width,"height":context.height,"stride":context.bytesPerRow,"case":variant,"order":args[6],
                "callback_count":callbacks,"reported_size":[size.width,size.height],"allocation_bytes":buffer.count,
                "bitmap_info":context.bitmapInfo.rawValue,"alpha_info":context.alphaInfo.rawValue,
                "bits_per_component":context.bitsPerComponent,"bits_per_pixel":context.bitsPerPixel,
                "color_space":context.colorSpace?.name as String? ?? "unnamed","rasterization_scale":1,"drawing_group":false]
            try Data(buffer).write(to:URL(fileURLWithPath:args[1]+".raw"))
            try JSONSerialization.data(withJSONObject:metadata,options:[.sortedKeys]).write(to:URL(fileURLWithPath:args[1]+".json"))
        }
    }
}
