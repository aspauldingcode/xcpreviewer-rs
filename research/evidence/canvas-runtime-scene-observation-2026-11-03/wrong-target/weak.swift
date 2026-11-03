import Darwin
private final class WeakBox {
    weak var target: AnyObject?
    init(_ target: AnyObject) { self.target = target }
}
private final class Fixture {
    let fd = open("/dev/null", O_RDONLY)
    init() { precondition(fd >= 0) }
    deinit { precondition(close(fd) == 0) }
}
@_cdecl("canvas_weak_new")
public func weakNew(_ p: UnsafeMutableRawPointer) -> UnsafeMutableRawPointer {
    let object = Unmanaged<AnyObject>.fromOpaque(p).takeUnretainedValue()
    return Unmanaged.passRetained(WeakBox(object)).toOpaque()
}
@_cdecl("canvas_weak_alive")
public func weakAlive(_ p: UnsafeMutableRawPointer) -> Int32 {
    Unmanaged<WeakBox>.fromOpaque(p).takeUnretainedValue().target == nil ? 0 : 1
}
@_cdecl("canvas_weak_dispose")
public func weakDispose(_ p: UnsafeMutableRawPointer) { Unmanaged<WeakBox>.fromOpaque(p).release() }
@_cdecl("canvas_fixture_new")
public func fixtureNew() -> UnsafeMutableRawPointer { Unmanaged.passRetained(Fixture()).toOpaque() }
@_cdecl("canvas_fixture_fd")
public func fixtureFD(_ p: UnsafeMutableRawPointer) -> Int32 { Unmanaged<Fixture>.fromOpaque(p).takeUnretainedValue().fd }
@_cdecl("canvas_fixture_retain")
public func fixtureRetain(_ p: UnsafeMutableRawPointer) { _ = Unmanaged<Fixture>.fromOpaque(p).retain() }
@_cdecl("canvas_fixture_release")
public func fixtureRelease(_ p: UnsafeMutableRawPointer) { Unmanaged<Fixture>.fromOpaque(p).release() }
