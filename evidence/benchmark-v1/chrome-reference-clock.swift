import AppKit
import ApplicationServices

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data("chrome_smoke_pointer: \(message)\n".utf8))
    exit(1)
}

func attribute(_ element: AXUIElement, _ name: String) -> CFTypeRef? {
    var value: CFTypeRef?
    guard AXUIElementCopyAttributeValue(element, name as CFString, &value) == .success else {
        return nil
    }
    return value
}

func attributePoint(_ element: AXUIElement, _ name: String) -> CGPoint? {
    guard let value = attribute(element, name), CFGetTypeID(value) == AXValueGetTypeID() else {
        return nil
    }
    var point = CGPoint.zero
    return AXValueGetValue(value as! AXValue, .cgPoint, &point) ? point : nil
}

func elementCenter(_ element: AXUIElement) -> CGPoint? {
    guard let position = attributePoint(element, kAXPositionAttribute),
          let value = attribute(element, kAXSizeAttribute), CFGetTypeID(value) == AXValueGetTypeID() else {
        return nil
    }
    var size = CGSize.zero
    guard AXValueGetValue(value as! AXValue, .cgSize, &size), size.width > 0, size.height > 0 else {
        return nil
    }
    return CGPoint(x: position.x + size.width / 2, y: position.y + size.height / 2)
}

func findToolbarAction(in window: AXUIElement, title: String) -> AXUIElement {
    var queue = [window]
    var cursor = 0
    var matches = [AXUIElement]()
    var observed = [String]()
    let buttonRoles = ["AXButton", "AXPopUpButton", "AXMenuButton"]
    while cursor < queue.count && cursor < 600 {
        let element = queue[cursor]
        cursor += 1
        let role = attribute(element, kAXRoleAttribute) as? String
        if role == "AXWebArea" { continue }
        if let role, buttonRoles.contains(role) {
            let labels = [kAXTitleAttribute, kAXDescriptionAttribute, kAXHelpAttribute]
                .compactMap { attribute(element, $0) as? String }
            if observed.count < 25, let label = labels.first(where: { !$0.isEmpty }) {
                observed.append("\(role): \(label.prefix(140).debugDescription)")
            }
            // Chrome appends the current site-access status on a second line.
            if labels.contains(where: { $0 == title || $0.hasPrefix(title + "\n") }) {
                matches.append(element)
            }
        }
        queue.append(contentsOf: attribute(element, kAXChildrenAttribute) as? [AXUIElement] ?? [])
    }
    guard cursor == queue.count, matches.count == 1 else {
        fail("Expected one \(title.debugDescription) toolbar button, matched \(matches.count) in \(cursor) elements. Buttons: \(observed.joined(separator: ", "))")
    }
    return matches[0]
}

let args = Array(CommandLine.arguments.dropFirst())
guard args.count == 2, let pid = pid_t(args[0]), pid > 1,
      let chrome = NSRunningApplication(processIdentifier: pid), chrome.bundleIdentifier == "com.google.Chrome",
      NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else { fail("Owned Chrome is not focused") }
let app = AXUIElementCreateApplication(pid)
AXUIElementSetMessagingTimeout(app, 0.25)
guard let focused = attribute(app, kAXFocusedWindowAttribute), CFGetTypeID(focused) == AXUIElementGetTypeID() else {
    fail("No focused Chrome window")
}
let window = focused as! AXUIElement
let title = attribute(window, kAXTitleAttribute) as? String
let address = attribute(window, kAXURLAttribute) as? URL
let expectedURL = "http://127.0.0.1:58232/shuttle-dispatch.html"
guard title == "Evening shuttle dispatch - Google Chrome" || title == "Evening shuttle dispatch",
      address?.absoluteString == expectedURL || address == nil else { fail("Focused Chrome window does not match the isolated fixture") }
let button = findToolbarAction(in: window, title: "Review this page")
guard let center = elementCenter(button), let origin = attributePoint(button, kAXPositionAttribute) else { fail("Toolbar button has no bounds") }
let size = CGSize(width: 2 * (center.x - origin.x), height: 2 * (center.y - origin.y))

guard let count = Int(args[1]), (1...30).contains(count), CGPreflightListenEventAccess() else {
    fail("Expected 1–30 trials and existing event observation permission")
}
let target = CGRect(origin: origin, size: size)
let popupURL = "chrome-extension://lkbieglapbdpfbekfidmoplgoceaacoe/popup.html"

func emit(_ data: [String: Any]) {
    let bytes = try! JSONSerialization.data(withJSONObject: data, options: [.sortedKeys])
    print(String(decoding: bytes, as: UTF8.self))
    fflush(stdout)
}

final class Trial {
    let expected: Int
    let target: CGRect
    let pid: pid_t
    var press: UInt64?
    var actionReady: UInt64?
    var scan: UInt64?
    var completed = 0
    var error: String?

    init(expected: Int, target: CGRect, pid: pid_t) {
        self.expected = expected
        self.target = target
        self.pid = pid
    }
}

func axElement(_ element: AXUIElement, _ name: String) -> AXUIElement? {
    guard let value = attribute(element, name), CFGetTypeID(value) == AXUIElementGetTypeID() else { return nil }
    return value as! AXUIElement
}

func scopedPopup(_ element: AXUIElement) -> AXUIElement? {
    var node: AXUIElement? = element
    for _ in 0..<12 {
        guard let current = node else { break }
        if attribute(current, kAXRoleAttribute) as? String == "AXWebArea" {
            return (attribute(current, kAXURLAttribute) as? URL)?.absoluteString == popupURL ? current : nil
        }
        node = axElement(current, kAXParentAttribute)
    }
    return nil
}

func focus(named name: String) -> AXUIElement? {
    guard let control = axElement(app, kAXFocusedUIElementAttribute),
          attribute(control, kAXRoleAttribute) as? String == "AXButton",
          attribute(control, kAXEnabledAttribute) as? Bool == true,
          attribute(control, kAXTitleAttribute) as? String == name ||
            attribute(control, kAXDescriptionAttribute) as? String == name,
          elementCenter(control) != nil else { return nil }
    return scopedPopup(control)
}

func findingExists(in root: AXUIElement) -> Bool {
    var queue = [root]
    var index = 0
    while index < queue.count && index < 70 {
        let current = queue[index]
        index += 1
        if attribute(current, kAXRoleAttribute) as? String == "AXStaticText",
           let value = attribute(current, kAXValueAttribute) as? String,
           value.contains("Boarding begins at 6:30 p.m."), value.contains("2.6 to 1"),
           elementCenter(current) != nil { return true }
        queue.append(contentsOf: attribute(current, kAXChildrenAttribute) as? [AXUIElement] ?? [])
    }
    return false
}

let trial = Trial(expected: count, target: target, pid: pid)
let callback: CGEventTapCallBack = { _, type, event, context in
    guard let context else { return Unmanaged.passUnretained(event) }
    let trial = Unmanaged<Trial>.fromOpaque(context).takeUnretainedValue()
    let timestamp = event.timestamp
    let now = DispatchTime.now().uptimeNanoseconds
    if type == .leftMouseDown && trial.target.contains(event.location) && trial.press == nil {
        if timestamp > now || now - timestamp > 100_000_000 { trial.error = "Invalid pointer timestamp" }
        trial.press = timestamp
    } else if type == .keyDown && event.getIntegerValueField(.keyboardEventKeycode) == 36 && trial.actionReady != nil && trial.scan == nil {
        if timestamp > now || now - timestamp > 100_000_000 { trial.error = "Invalid key timestamp" }
        trial.scan = timestamp
    }
    return Unmanaged.passUnretained(event)
}
let mask = (CGEventMask(1) << CGEventType.leftMouseDown.rawValue) | (CGEventMask(1) << CGEventType.keyDown.rawValue)
guard let tap = CGEvent.tapCreateForPid(pid: pid, place: .headInsertEventTap, options: .listenOnly,
                                      eventsOfInterest: mask, callback: callback,
                                      userInfo: Unmanaged.passUnretained(trial).toOpaque()),
      let source = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0) else { fail("Could not observe the owned Chrome event queue") }
let loop = CFRunLoopGetMain()
CFRunLoopAddSource(loop, source, .commonModes)
CGEvent.tapEnable(tap: tap, enable: true)
emit(["state": "armed", "trials": count, "toolbar_bounds": [origin.x, origin.y, size.width, size.height]])
let deadline = ProcessInfo.processInfo.systemUptime + Double(max(25, 5 * count))
func elapsed(_ start: UInt64, _ end: UInt64) -> Double { Double(end - start) / 1_000_000 }
while trial.completed < trial.expected && ProcessInfo.processInfo.systemUptime < deadline {
    if let error = trial.error { fail(error) }
    guard !chrome.isTerminated, NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else {
        fail("The owned Chrome process lost foreground focus")
    }
    if let press = trial.press, trial.actionReady == nil, focus(named: "Review this page") != nil {
        let ready = DispatchTime.now().uptimeNanoseconds
        trial.actionReady = ready
        emit(["state": "action_ready", "attempt": trial.completed + 1, "open_ms": elapsed(press, ready)])
    }
    if let press = trial.press, let ready = trial.actionReady, let scan = trial.scan,
       let popup = focus(named: "Open before and after"), findingExists(in: popup) {
        let found = DispatchTime.now().uptimeNanoseconds
        trial.completed += 1
        emit(["state": "finding", "attempt": trial.completed, "open_ms": elapsed(press, ready),
              "scan_ms": elapsed(scan, found), "press_uptime_ns": String(press),
              "ready_uptime_ns": String(ready), "scan_uptime_ns": String(scan), "found_uptime_ns": String(found)])
        trial.press = nil
        trial.actionReady = nil
        trial.scan = nil
    }
    RunLoop.current.run(until: Date().addingTimeInterval(0.008))
}
CFRunLoopRemoveSource(loop, source, .commonModes)
CFMachPortInvalidate(tap)
if trial.completed != trial.expected {
    emit(["state":"incomplete", "completed":trial.completed, "pressed":trial.press != nil,
          "action_ready":trial.actionReady != nil, "scan_pressed":trial.scan != nil])
    exit(1)
}
