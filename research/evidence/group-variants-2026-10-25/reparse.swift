import Foundation
let args = CommandLine.arguments
let input = try Data(contentsOf: URL(fileURLWithPath: args[1]))
let value = try PropertyListSerialization.propertyList(from: input, format: nil)
let output = try PropertyListSerialization.data(fromPropertyList: value, format: .binary, options: 0)
try output.write(to: URL(fileURLWithPath: args[2]))
