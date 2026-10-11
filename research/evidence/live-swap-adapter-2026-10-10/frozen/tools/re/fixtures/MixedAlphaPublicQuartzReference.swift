import SwiftUI
import AppKit

@main
struct MixedAlphaPublicQuartzReferenceCapture {
    @MainActor static func main() throws {
        guard CommandLine.arguments.count == 3,
              let variant = Int(CommandLine.arguments[2]), (0...13).contains(variant) else {
            throw NSError(domain: "MixedAlphaPublicQuartzReference", code: 2)
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
        guard let space = CGColorSpace(name: CGColorSpace.sRGB),
              let ns = NSColor(color).usingColorSpace(.sRGB) else {
            throw NSError(domain: "MixedAlphaPublicQuartzReference", code: 1)
        }
        let sources = [rgb + [Double(eighths[variant]) / 8.0],
                       [ns.redComponent, ns.greenComponent, ns.blueComponent, ns.alphaComponent]]
        guard let direct = CGColor(colorSpace: space, components: sources[0].map { CGFloat($0) }),
              let bridged = CGColor(colorSpace: space, components: sources[1].map { CGFloat($0) }),
              let publicColor = color.cgColor else {
            throw NSError(domain: "MixedAlphaPublicQuartzReference", code: 4)
        }
        let fills = [direct, bridged, publicColor, ns.cgColor]
        for (index, fill) in fills.enumerated() {
            let components = fill.components ?? []
            var bytes = [UInt8](repeating: 0xa5, count: 80 * 9)
            for row in 0..<9 { for col in 0..<68 { bytes[row * 80 + col] = 0 } }
            try bytes.withUnsafeMutableBytes { buffer in
                guard let context = CGContext(data: buffer.baseAddress, width: 17, height: 9,
                    bitsPerComponent: 8, bytesPerRow: 80, space: space,
                    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue | CGBitmapInfo.byteOrder32Big.rawValue) else {
                    throw NSError(domain: "MixedAlphaPublicQuartzReference", code: 3)
                }
                context.setBlendMode(.copy)
                context.setFillColor(fill)
                context.fill(CGRect(x: 0, y: 0, width: 17, height: 9))
                let metadata: [String: Any] = ["width": context.width, "height": context.height,
                    "bits_per_component": context.bitsPerComponent, "bits_per_pixel": context.bitsPerPixel,
                    "bytes_per_row": context.bytesPerRow, "bitmap_info": context.bitmapInfo.rawValue,
                    "alpha_info": context.alphaInfo.rawValue, "data_bytes": buffer.count,
                    "color_space": context.colorSpace?.name as String? ?? "unnamed",
                    "components": components, "input_color_space": fill.colorSpace?.name as String? ?? "unnamed"]
                let prefix = CommandLine.arguments[1] + "." + String(index)
                try JSONSerialization.data(withJSONObject: metadata, options: [.sortedKeys])
                    .write(to: URL(fileURLWithPath: prefix + ".json"))
                try Data(buffer).write(to: URL(fileURLWithPath: prefix + ".raw"))
            }
        }
    }
}
