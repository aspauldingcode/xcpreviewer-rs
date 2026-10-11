import SwiftUI
import AppKit

@main
struct PrimaryLayerReference {
    @MainActor static func main() throws {
        guard CommandLine.arguments.count == 4, let variant = Int(CommandLine.arguments[2]),
              (0..<12).contains(variant), ["forward","reverse"].contains(CommandLine.arguments[3]) else {
            throw NSError(domain: "PrimaryLayer", code: 1)
        }
        _ = NSApplication.shared
        NSApplication.shared.appearance = NSAppearance(named: .aqua)
        let alphas = [[0,0,8],[8,0,8],[0,8,8],[0,0,0],[4,2,8],[2,4,8],
                      [1,6,8],[7,3,8],[4,4,4],[3,5,2],[6,1,0],[2,3,6]][variant]
        let red = Color(.sRGB, red: 1, green: 0, blue: 0, opacity: Double(alphas[0])/8)
        let green = Color(.sRGB, red: 0, green: 1, blue: 0, opacity: Double(alphas[1])/8)
        let blue = Color(.sRGB, red: 0, green: 0, blue: 1, opacity: Double(alphas[2])/8)
        let reverse = CommandLine.arguments[3] == "reverse"
        let stack = ZStack {
            if reverse { green; red; blue } else { blue; red; green }
        }.frame(width: 17, height: 9)
        guard let space = CGColorSpace(name: CGColorSpace.sRGB) else { throw NSError(domain:"PrimaryLayer",code:2) }
        for index in 0..<4 {
            let grouped = index >= 2
            let scale: CGFloat = index % 2 == 0 ? 1 : 2
            let view = grouped ? AnyView(stack.drawingGroup(opaque:false,colorMode:.nonLinear)) : AnyView(stack)
            let renderer = ImageRenderer(content: view)
            renderer.scale = 1; renderer.colorMode = .nonLinear
            let prefix = CommandLine.arguments[1] + "." + String(index)
            guard let cg = renderer.cgImage, let data = cg.dataProvider?.data else { throw NSError(domain:"PrimaryLayer",code:3) }
            try Data(bytes: CFDataGetBytePtr(data)!, count: CFDataGetLength(data))
                .write(to: URL(fileURLWithPath: prefix + ".cg.raw"))
            let cgMeta: [String:Any] = ["width":cg.width,"height":cg.height,"bits_per_component":cg.bitsPerComponent,
                "bits_per_pixel":cg.bitsPerPixel,"bytes_per_row":cg.bytesPerRow,"bitmap_info":cg.bitmapInfo.rawValue,
                "alpha_info":cg.alphaInfo.rawValue,"data_bytes":CFDataGetLength(data),"color_space":cg.colorSpace?.name as String? ?? "unnamed"]
            try JSONSerialization.data(withJSONObject:cgMeta,options:[.sortedKeys]).write(to:URL(fileURLWithPath:prefix+".cg.json"))
            var bytes = [UInt8](repeating:0xa5,count:720)
            for row in 0..<9 { for col in 0..<68 { bytes[row*80+col] = 0 } }
            try bytes.withUnsafeMutableBytes { buffer in
                guard let context = CGContext(data:buffer.baseAddress,width:17,height:9,bitsPerComponent:8,bytesPerRow:80,space:space,bitmapInfo:0x4001) else { throw NSError(domain:"PrimaryLayer",code:4) }
                context.setBlendMode(.normal)
                var count = 0; var size = CGSize.zero
                renderer.render(rasterizationScale:scale) { reported,draw in count += 1; size = reported; draw(context) }
                guard count == 1,size == CGSize(width:17,height:9) else { throw NSError(domain:"PrimaryLayer",code:5) }
                let metadata: [String:Any] = ["width":context.width,"height":context.height,"bits_per_component":context.bitsPerComponent,
                    "bits_per_pixel":context.bitsPerPixel,"bytes_per_row":context.bytesPerRow,"bitmap_info":context.bitmapInfo.rawValue,
                    "alpha_info":context.alphaInfo.rawValue,"data_bytes":buffer.count,"color_space":context.colorSpace?.name as String? ?? "unnamed",
                    "callback_count":count,"reported_size":[size.width,size.height],"blend_mode":"normal",
                    "rasterization_scale":scale,"target_index":index,"drawing_group":grouped,"layer_order":CommandLine.arguments[3]]
                try JSONSerialization.data(withJSONObject:metadata,options:[.sortedKeys]).write(to:URL(fileURLWithPath:prefix+".json"))
                try Data(buffer).write(to:URL(fileURLWithPath:prefix+".raw"))
            }
        }
    }
}
