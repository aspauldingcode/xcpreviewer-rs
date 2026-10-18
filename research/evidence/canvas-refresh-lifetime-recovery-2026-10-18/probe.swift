import SwiftUI
import Foundation

struct RefreshIdentityProbe: View {
    @State private var identity = UUID()
    private func bits(_ bytes: [UInt8]) -> [Bool] {
        bytes.flatMap { byte in (0..<8).reversed().map { (byte & (1 << $0)) != 0 } }
    }
    private func band(_ values: [Bool], _ color: Color) -> some View {
        HStack(spacing: 0) {
            ForEach(0..<128, id: \.self) { index in
                Rectangle().fill(values[index] ? color : Color.black).frame(width: 2, height: 12)
            }
        }
    }
    var body: some View {
        let value = identity.uuid
        let token = bits([value.0,value.1,value.2,value.3,value.4,value.5,value.6,value.7,
                          value.8,value.9,value.10,value.11,value.12,value.13,value.14,value.15])
        let pid = UInt32(ProcessInfo.processInfo.processIdentifier)
        let process = (0..<128).map { (pid & (1 << (31 - ($0 % 32)))) != 0 }
        VStack(spacing: 0) {
            band((0..<128).map { ($0 / 4) % 2 == 0 }, Color(.sRGB, red: 1, green: 0, blue: 1, opacity: 1))
            band(process, Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1))
            band(token, Color(.sRGB, red: 0, green: 1, blue: 0, opacity: 1))
            band(token.map { !$0 }, Color(.sRGB, red: 0, green: 0, blue: 1, opacity: 1))
        }.frame(width: 256, height: 48)
    }
}

@main struct PreviewLabApp: App {
    var body: some Scene { WindowGroup { RefreshIdentityProbe() } }
}
#Preview("Refresh identity", traits: .fixedLayout(width: 256, height: 48)) {
    RefreshIdentityProbe().environment(\.colorScheme, .light)
}
