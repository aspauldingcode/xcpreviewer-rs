import SwiftUI
@MainActor enum Fixture {
 static var calls=0
 static func body() -> some View {
  calls+=1;precondition(calls==1,"Owned body called more than once")
  return factory()
 }
 static func factory() -> some View {
  VStack(spacing:0) {
   Color(red:1,green:0,blue:0)
   Color(red:0,green:0,blue:1)
  }
 }
}
#Preview("Bars") { Fixture.body() }
#Preview { Color(red:0.75,green:0.25,blue:0.5).opacity(0.5) }
