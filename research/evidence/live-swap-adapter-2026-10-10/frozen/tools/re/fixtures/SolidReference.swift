import SwiftUI
import AppKit

@main
struct SolidReferenceCapture {
    @MainActor static func main() throws {
        guard CommandLine.arguments.count == 3,
              let variant = Int(CommandLine.arguments[2]), (2...3).contains(variant) else {
            throw NSError(domain: "SolidReference", code: 2)
        }
        _ = NSApplication.shared
        NSApplication.shared.appearance = NSAppearance(named: .aqua)
        let color = Color(.sRGB, red: variant == 2 ? 1 : 0,
                          green: 0, blue: variant == 3 ? 1 : 0, opacity: 1)
        let renderer = ImageRenderer(content: color.frame(width: 320, height: 160))
        renderer.scale = 1
        guard let image = renderer.nsImage, let tiff = image.tiffRepresentation,
              let bitmap = NSBitmapImageRep(data: tiff),
              let png = bitmap.representation(using: .png, properties: [:]) else {
            throw NSError(domain: "SolidReference", code: 1)
        }
        try png.write(to: URL(fileURLWithPath: CommandLine.arguments[1]))
    }
}
