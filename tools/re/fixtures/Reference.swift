import SwiftUI
import AppKit

struct ReferenceView: View {
    var body: some View {
        VStack(spacing: 12) {
            Text("Hello, Preview").font(.title)
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
        let renderer = ImageRenderer(content: ReferenceView())
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
