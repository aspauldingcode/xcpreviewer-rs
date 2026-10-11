import SwiftUI
import AppKit

@main
struct AlphaReferenceCapture {
    @MainActor static func main() throws {
        guard CommandLine.arguments.count == 3,
              let variant = Int(CommandLine.arguments[2]), (0...7).contains(variant) else {
            throw NSError(domain: "AlphaReference", code: 2)
        }
        _ = NSApplication.shared
        NSApplication.shared.appearance = NSAppearance(named: .aqua)
        let alpha = [0.0, 0.25, 0.5, 1.0, 0.25, 0.5, 0.125, 0.75][variant]
        let red = Color(.sRGB, red: 1, green: 0, blue: 0, opacity: alpha)
        let blue = Color(.sRGB, red: 0, green: 0, blue: 1, opacity: 1)
        let view = red.frame(width: 17, height: 9)
            .background(variant >= 4 ? blue : Color.clear)
        let renderer = ImageRenderer(content: view)
        renderer.scale = 1
        renderer.colorMode = .nonLinear
        guard let image = renderer.nsImage, let tiff = image.tiffRepresentation,
              let bitmap = NSBitmapImageRep(data: tiff),
              let png = bitmap.representation(using: .png, properties: [:]) else {
            throw NSError(domain: "AlphaReference", code: 1)
        }
        try png.write(to: URL(fileURLWithPath: CommandLine.arguments[1]))
    }
}
