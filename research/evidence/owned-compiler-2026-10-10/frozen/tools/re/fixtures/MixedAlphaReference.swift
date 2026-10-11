import SwiftUI
import AppKit

@main
struct MixedAlphaReferenceCapture {
    @MainActor static func main() throws {
        guard CommandLine.arguments.count == 3,
              let variant = Int(CommandLine.arguments[2]), (0...9).contains(variant) else {
            throw NSError(domain: "MixedAlphaReference", code: 2)
        }
        _ = NSApplication.shared
        NSApplication.shared.appearance = NSAppearance(named: .aqua)
        // Discovery cases 0...3; predeclared holdouts 4...7; endpoint controls 8...9.
        let channels = [[128,64,192], [17,83,201], [1,7,13], [51,153,230],
                        [29,113,241], [3,127,253], [89,167,211], [11,73,199],
                        [17,83,201], [17,83,201]]
        let eighths = [4,2,1,6,3,7,5,1,0,8]
        let rgb = channels[variant].map { Double($0) / 255.0 }
        let color = Color(.sRGB, red: rgb[0], green: rgb[1], blue: rgb[2],
                          opacity: Double(eighths[variant]) / 8.0)
        let renderer = ImageRenderer(content: color.frame(width: 17, height: 9))
        renderer.scale = 1
        renderer.colorMode = .nonLinear
        guard let image = renderer.nsImage, let tiff = image.tiffRepresentation,
              let bitmap = NSBitmapImageRep(data: tiff),
              let png = bitmap.representation(using: .png, properties: [:]) else {
            throw NSError(domain: "MixedAlphaReference", code: 1)
        }
        try png.write(to: URL(fileURLWithPath: CommandLine.arguments[1]))
    }
}
