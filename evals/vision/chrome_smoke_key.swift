import AppKit
import CoreGraphics

enum SmokeKey: String {
    case shortcut = "Command+Shift+Y"
    case tab = "Tab"
    case enter = "Return"
    case escape = "Escape"
    case right = "Right"

    var code: CGKeyCode {
        switch self {
        case .shortcut: return 0x10 // ANSI Y
        case .tab: return 0x30
        case .enter: return 0x24
        case .escape: return 0x35
        case .right: return 0x7C
        }
    }

    var flags: CGEventFlags {
        self == .shortcut ? [.maskCommand, .maskShift] : []
    }
}

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data("chrome_smoke_key: \(message)\n".utf8))
    exit(1)
}

func requireInputAccess() {
    guard CGPreflightPostEventAccess() else {
        fail("Accessibility keyboard input is unavailable on this runner (CGPreflightPostEventAccess returned false).")
    }
    guard NSWorkspace.shared.frontmostApplication != nil else {
        fail("The runner has no foreground desktop application for keyboard input.")
    }
}

let arguments = Array(CommandLine.arguments.dropFirst())
if arguments == ["--preflight"] {
    requireInputAccess()
    print("Desktop keyboard input preflight passed.")
    exit(0)
}

guard arguments.count == 2, let pid = pid_t(arguments[0]), pid > 1,
      let key = SmokeKey(rawValue: arguments[1]) else {
    fail("Usage: chrome_smoke_key --preflight | CHROME_PID {Command+Shift+Y|Tab|Return|Escape|Right}")
}
requireInputAccess()

let workspace = NSWorkspace.shared
guard let chrome = NSRunningApplication(processIdentifier: pid), !chrome.isTerminated,
      chrome.bundleURL?.lastPathComponent == "Google Chrome for Testing.app" else {
    fail("PID \(pid) is not a running Chrome for Testing application.")
}

if workspace.frontmostApplication?.processIdentifier != pid {
    guard chrome.activate(options: []) else {
        fail("Could not activate Chrome for Testing PID \(pid).")
    }
    let deadline = Date().addingTimeInterval(3)
    while workspace.frontmostApplication?.processIdentifier != pid && Date() < deadline {
        RunLoop.current.run(until: Date().addingTimeInterval(0.05))
    }
}

guard let down = CGEvent(keyboardEventSource: nil, virtualKey: key.code, keyDown: true),
      let up = CGEvent(keyboardEventSource: nil, virtualKey: key.code, keyDown: false) else {
    fail("Could not create \(key.rawValue) keyboard events.")
}
for event in [down, up] {
    event.flags = key.flags
    guard !chrome.isTerminated, let focused = workspace.frontmostApplication?.processIdentifier,
          focused == pid else {
        fail("Chrome PID \(pid) was not focused immediately before posting \(key.rawValue).")
    }
    event.postToPid(pid)
}
