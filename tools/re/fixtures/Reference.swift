import SwiftUI
import AppKit

struct ReferenceView: View {
    var variant = 0
    var body: some View {
        VStack(spacing: 12) {
            Text(variant == 0 ? "Hello, Preview" : "Changed Preview").font(.title)
            Text("Owned native reference").foregroundStyle(.secondary)
        }
        .frame(width: 320, height: 160)
        .background(Color.white)
    }
}

#Preview { ReferenceView() }

@main
struct ReferenceCapture {
    @MainActor static func main() throws {
        _ = NSApplication.shared
        NSApplication.shared.appearance = NSAppearance(named: .aqua)
        let variant = CommandLine.arguments.count == 3 ? Int(CommandLine.arguments[2]) : 0
        guard let variant, (0...1).contains(variant), (2...3).contains(CommandLine.arguments.count) else {
            throw NSError(domain: "ReferenceCapture", code: 2)
        }
        let renderer = ImageRenderer(content: ReferenceView(variant: variant))
        renderer.scale = 1
        guard let image = renderer.nsImage,
              let tiff = image.tiffRepresentation,
              let bitmap = NSBitmapImageRep(data: tiff),
              let png = bitmap.representation(using: .png, properties: [:]) else {
            throw NSError(domain: "ReferenceCapture", code: 1)
        }
        try png.write(to: URL(fileURLWithPath: CommandLine.arguments[1]))
        print("Captured owned ImageRenderer reference; this is not a live Xcode canvas session.")
    }
}
