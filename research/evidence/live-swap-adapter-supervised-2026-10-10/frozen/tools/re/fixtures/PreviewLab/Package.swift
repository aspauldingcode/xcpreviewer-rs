// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "PreviewLab",
    platforms: [.macOS(.v14)],
    products: [.executable(name: "PreviewLab", targets: ["PreviewLab"])],
    targets: [.executableTarget(name: "PreviewLab")]
)
