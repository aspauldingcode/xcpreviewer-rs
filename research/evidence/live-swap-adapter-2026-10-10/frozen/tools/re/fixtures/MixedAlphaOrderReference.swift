import SwiftUI
import AppKit

@main
struct MixedAlphaOrderReferenceCapture {
    @MainActor static func main() throws {
        guard CommandLine.arguments.count == 4,
              let variant = Int(CommandLine.arguments[2]), (0...13).contains(variant), ["callback-first","cg-first"].contains(CommandLine.arguments[3]) else {
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
        let renderer = ImageRenderer(content: color.frame(width: 17, height: 9))
        renderer.scale = 1
        renderer.colorMode = .nonLinear
        guard let space = CGColorSpace(name: CGColorSpace.sRGB) else {
            throw NSError(domain: "MixedAlphaCallbackReference", code: 1)
        }
        let prefix = CommandLine.arguments[1]
        let callbackFirst = CommandLine.arguments[3] == "callback-first"
        var retained: CFData?
        func copyProvider(_ data: CFData) -> Data {
            Data(bytes: CFDataGetBytePtr(data)!, count: CFDataGetLength(data))
        }
        func snapshot(_ stage: String) throws {
            guard let cg = renderer.cgImage, let data = cg.dataProvider?.data else {
                throw NSError(domain: "MixedAlphaOrder", code: 5)
            }
            if retained == nil { retained = data }
            // Force an immediate independent byte copy before any later renderer call.
            try copyProvider(data).write(to: URL(fileURLWithPath: prefix + "." + stage + ".raw"))
            let metadata: [String: Any] = ["width": cg.width, "height": cg.height,
                "bits_per_component": cg.bitsPerComponent, "bits_per_pixel": cg.bitsPerPixel,
                "bytes_per_row": cg.bytesPerRow, "bitmap_info": cg.bitmapInfo.rawValue,
                "alpha_info": cg.alphaInfo.rawValue, "data_bytes": CFDataGetLength(data),
                "color_space": cg.colorSpace?.name as String? ?? "unnamed"]
            try JSONSerialization.data(withJSONObject: metadata, options: [.sortedKeys])
                .write(to: URL(fileURLWithPath: prefix + "." + stage + ".json"))
            try copyProvider(retained!).write(to: URL(fileURLWithPath: prefix + "." + stage + ".retained.raw"))
        }
        func draw(_ stage: String) throws {
            var bytes = [UInt8](repeating: 0xa5, count: 80 * 9)
            for row in 0..<9 { for col in 0..<68 { bytes[row * 80 + col] = 0 } }
            try bytes.withUnsafeMutableBytes { buffer in
                guard let context = CGContext(data: buffer.baseAddress, width: 17, height: 9,
                    bitsPerComponent: 8, bytesPerRow: 80, space: space, bitmapInfo: 0x4001) else {
                    throw NSError(domain: "MixedAlphaOrder", code: 3)
                }
                context.setBlendMode(.normal)
                var count = 0
                var size = CGSize.zero
                renderer.render(rasterizationScale: 1) { reported, drawing in
                    count += 1; size = reported; drawing(context)
                }
                guard count == 1, size == CGSize(width: 17, height: 9) else {
                    throw NSError(domain: "MixedAlphaOrder", code: 4)
                }
                let metadata: [String: Any] = ["width": context.width, "height": context.height,
                    "bits_per_component": context.bitsPerComponent, "bits_per_pixel": context.bitsPerPixel,
                    "bytes_per_row": context.bytesPerRow, "bitmap_info": context.bitmapInfo.rawValue,
                    "alpha_info": context.alphaInfo.rawValue, "data_bytes": buffer.count,
                    "color_space": context.colorSpace?.name as String? ?? "unnamed",
                    "callback_count": count, "reported_size": [size.width,size.height], "blend_mode": "normal"]
                try JSONSerialization.data(withJSONObject: metadata, options: [.sortedKeys])
                    .write(to: URL(fileURLWithPath: prefix + "." + stage + ".json"))
                try Data(buffer).write(to: URL(fileURLWithPath: prefix + "." + stage + ".raw"))
            }
        }
        if callbackFirst { try draw("draw0") }
        try snapshot("initial")
        if !callbackFirst { try draw("draw0") }
        try snapshot("after-draw")
        try draw("draw1")
        try snapshot("after-second-draw")
        guard let image = renderer.nsImage, let tiff = image.tiffRepresentation,
              let bitmap = NSBitmapImageRep(data: tiff),
              let png = bitmap.representation(using: .png, properties: [:]) else {
            throw NSError(domain: "MixedAlphaOrder", code: 6)
        }
        try png.write(to: URL(fileURLWithPath: prefix + ".export.png"))
        try snapshot("after-export")
    }
}
