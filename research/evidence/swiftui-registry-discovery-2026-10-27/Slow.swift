import SwiftUI
import Foundation
@MainActor func slowName() -> String? { Thread.sleep(forTimeInterval:2); return "Too slow" }
#Preview(slowName()) { Color.red }
