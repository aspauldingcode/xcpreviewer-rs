import SwiftUI
import AppKit

@main
struct MixedAlphaGroupReferenceCapture {
    @MainActor static func main() throws {
        guard CommandLine.arguments.count == 4,
              let variant = Int(CommandLine.arguments[2]), (0...13).contains(variant), ["forward","reverse"].contains(CommandLine.arguments[3]) else {
            throw NSError(domain: "MixedAlphaCallbackReference", code: 2)
        }
        _ = NSApplication.shared
        NSApplication.shared.appearance = NSAppearance(named: .aqua)
        // Cases10...13 are new predeclared ties-to-even holdouts.
        // Discovery cases 0...3; predeclared holdouts 4...7; endpoint controls 8...9.
        let channels = [[128,64,192], [17,83,201], [1,7,13], [51,153,230],
                        [29,113,241], [3,127,253], [89,167,211], [11,73,199],
                        [17,83,201], [17,83,201], [5,9,13], [7,11,15], [4,12,20], [4,12,20]]
        let eighths = [4,2,1,6,3,7,5,1,0,8,4,4,3,7]
        let rgb = channels[variant].map { Double($0) / 255.0 }
        let color = Color(.sRGB, red: rgb[0], green: rgb[1], blue: rgb[2],
                          opacity: Double(eighths[variant]) / 8.0)
        let renderer = ImageRenderer(content: color.frame(width: 17, height: 9).drawingGroup(opaque: false, colorMode: .nonLinear))
        renderer.scale = 1
        renderer.colorMode = .nonLinear
        guard let space = CGColorSpace(name: CGColorSpace.sRGB) else {
            throw NSError(domain: "MixedAlphaCallbackReference", code: 1)
        }
        let scales: [CGFloat] = CommandLine.arguments[3] == "forward" ? [1,2,0.5,4] : [4,0.5,2,1]
        for (index, scale) in scales.enumerated() {
            var bytes = [UInt8](repeating: 0xa5, count: 80 * 9)
            for row in 0..<9 { for col in 0..<68 { bytes[row * 80 + col] = 0 } }
            try bytes.withUnsafeMutableBytes { buffer in
                guard let context = CGContext(data: buffer.baseAddress, width: 17, height: 9,
                    bitsPerComponent: 8, bytesPerRow: 80, space: space,
                    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue | CGBitmapInfo.byteOrder32Big.rawValue) else {
                    throw NSError(domain: "MixedAlphaCallbackReference", code: 3)
                }
                context.setBlendMode(.normal)
                var callbackCount = 0
                var reportedSize = CGSize.zero
                renderer.render(rasterizationScale: scale) { size, draw in
                    callbackCount += 1
                    reportedSize = size
                    draw(context)
                }
                guard callbackCount == 1, reportedSize == CGSize(width: 17, height: 9) else {
                    throw NSError(domain: "MixedAlphaCallbackReference", code: 4)
                }
                let metadata: [String: Any] = ["width": context.width, "height": context.height,
                    "bits_per_component": context.bitsPerComponent, "bits_per_pixel": context.bitsPerPixel,
                    "bytes_per_row": context.bytesPerRow, "bitmap_info": context.bitmapInfo.rawValue,
                    "alpha_info": context.alphaInfo.rawValue, "data_bytes": buffer.count,
                    "color_space": context.colorSpace?.name as String? ?? "unnamed",
                    "callback_count": callbackCount, "reported_size": [reportedSize.width, reportedSize.height],
                    "blend_mode": "normal", "rasterization_scale": scale, "target_index": index, "scale_order": CommandLine.arguments[3]]
                let prefix = CommandLine.arguments[1] + "." + String(index)
                try JSONSerialization.data(withJSONObject: metadata, options: [.sortedKeys])
                    .write(to: URL(fileURLWithPath: prefix + ".json"))
                try Data(buffer).write(to: URL(fileURLWithPath: prefix + ".raw"))
            }
        }
    }
}
