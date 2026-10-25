import Foundation
struct ControlledError: Error, CustomStringConvertible { let description: String }
let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
let cases: [([String], Bool)] = [([],false),([""],false),(["first\\nline","second", ""],false),(["join\\n\u{301}","emoji🙂\\nend", "NUL\0CR\r\n"],false),(["failed report write"],true)]
var rows: [[String: Any]] = []
for (index, item) in cases.enumerated() {
 let (descriptions, fail) = item
 let base = root.appendingPathComponent("case-\(index)", isDirectory: true)
 try FileManager.default.createDirectory(at: base, withIntermediateDirectories: true)
 let destination = base.appendingPathComponent("SerializationErrors.txt", isDirectory: false)
 if fail { try FileManager.default.createDirectory(at: destination, withIntermediateDirectories: true) }
 else { try Data("sentinel".utf8).write(to: destination) }
 let errors: [Error] = descriptions.map { ControlledError(description: $0) }
 var attempted = false; var ignoredError = false
 if !errors.isEmpty {
  let report = errors.lazy.map { "\($0)" }.joined(separator: "\n\n").replacingOccurrences(of: "\\n", with: "\n")
  attempted = true
  do { try report.write(to: destination, atomically: true, encoding: .utf8) }
  catch { ignoredError = true }
 }
 let contents = fail ? Data() : try Data(contentsOf: destination)
 rows.append(["descriptions":descriptions,"failWrite":fail,"attempted":attempted,"ignoredWriteError":ignoredError,"bytes":contents])
}
let data = try PropertyListSerialization.data(fromPropertyList: rows, format: .binary, options: 0)
try data.write(to: root.appendingPathComponent("native.bplist"))
