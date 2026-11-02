import SwiftUI
@MainActor func failIfRendered() -> Color { fatalError("Owned body must not run during discovery") }
#Preview("Named control") { failIfRendered() }

#Preview { failIfRendered() }
