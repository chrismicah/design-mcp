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

func findToolbarAction(in window: AXUIElement, title: String) -> AXUIElement? {
    var queue = [window]
    var cursor = 0
    var matches = [AXUIElement]()
    let buttonRoles = ["AXButton", "AXPopUpButton", "AXMenuButton"]
    while cursor < queue.count && cursor < 600 {
        let element = queue[cursor]
        cursor += 1
        let role = attribute(element, kAXRoleAttribute) as? String
        if role == "AXWebArea" { continue }
        let labels = [kAXTitleAttribute, kAXDescriptionAttribute, kAXHelpAttribute]
        if let role, buttonRoles.contains(role), labels.contains(where: {
            attribute(element, $0) as? String == title
        }) {
            matches.append(element)
        }
        queue.append(contentsOf: attribute(element, kAXChildrenAttribute) as? [AXUIElement] ?? [])
    }
    guard cursor == queue.count, matches.count == 1 else { return nil }
    return matches[0]
}

let args = Array(CommandLine.arguments.dropFirst())
guard ProcessInfo.processInfo.environment["GITHUB_ACTIONS"] == "true",
      args.count == 2, let pid = pid_t(args[0]), pid > 1, !args[1].isEmpty else {
    fail("Run only on the hosted fixture: chrome_smoke_pointer CHROME_PID TOOLBAR_TITLE")
}
guard CGPreflightPostEventAccess(), AXIsProcessTrusted() else {
    fail("The hosted runner cannot inspect Chrome accessibility or post pointer events.")
}
guard let chrome = NSRunningApplication(processIdentifier: pid), !chrome.isTerminated,
      chrome.bundleURL?.lastPathComponent == "Google Chrome for Testing.app" else {
    fail("The supplied PID is not the owned Chrome for Testing process.")
}
if NSWorkspace.shared.frontmostApplication?.processIdentifier != pid {
    guard chrome.activate(options: []) else { fail("Could not focus the owned Chrome window.") }
    let deadline = Date().addingTimeInterval(3)
    while NSWorkspace.shared.frontmostApplication?.processIdentifier != pid && Date() < deadline {
        RunLoop.current.run(until: Date().addingTimeInterval(0.05))
    }
}
let app = AXUIElementCreateApplication(pid)
AXUIElementSetMessagingTimeout(app, 0.4)
let windows = attribute(app, kAXWindowsAttribute) as? [AXUIElement] ?? []
guard windows.count == 1, let button = findToolbarAction(in: windows[0], title: args[1]),
      let point = elementCenter(button) else {
    fail("No unique visible toolbar action named \(args[1]) in the owned window.")
}
var hit: AXUIElement?
guard AXUIElementCopyElementAtPosition(app, Float(point.x), Float(point.y), &hit) == .success,
      let hit, CFEqual(hit, button),
      NSWorkspace.shared.frontmostApplication?.processIdentifier == pid, !chrome.isTerminated else {
    fail("The toolbar button did not own its center point in the foreground window.")
}
guard let down = CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: point, mouseButton: .left),
      let up = CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: point, mouseButton: .left) else {
    fail("Could not create the mouse press for the toolbar action.")
}
for event in [down, up] { event.setIntegerValueField(.mouseEventClickState, value: 1) }
let pressedAt = DispatchTime.now().uptimeNanoseconds
down.post(tap: .cghidEventTap)
up.post(tap: .cghidEventTap)
print("{\"pressedUptimeNs\":\"\(pressedAt)\",\"x\":\(point.x),\"y\":\(point.y)}")
