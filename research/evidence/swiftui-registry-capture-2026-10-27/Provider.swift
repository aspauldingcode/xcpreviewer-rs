import SwiftUI
enum Fixtures {
 struct Bars: PreviewProvider {
  static var previews: some View {
   VStack(spacing:0) {
    Color(red:1,green:0,blue:0)
    Color(red:0,green:0,blue:1)
   }
  }
 }
}
@MainActor func makePreview() -> some View { Fixtures.Bars.previews }
struct NotProvider { static var previews: some View { Color.green } }
