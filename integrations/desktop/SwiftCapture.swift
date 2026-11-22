import Foundation
import XCTest

enum DesignCaptureFailure: Error {
    case missingWindow
    case windowChanged
}

struct DesignCapture {
    private struct Region: Encodable {
        let id: String
        let role: String
        let bounds: [Double]
        let hittable: Bool
    }

    private struct Snapshot: Encodable {
        let version = 1
        let platform = "swift"
        let viewport: [Double]
        let regions: [Region]
    }

    private static func role(for element: XCUIElement) -> String? {
        switch element.elementType {
        case .button: return "button"
        case .link: return "link"
        case .checkBox, .radioButton, .switch: return "toggle"
        case .slider: return "slider"
        case .popUpButton: return "selector"
        case .textField, .secureTextField, .textView, .searchField: return "input"
        default: return nil
        }
    }

    static func export(window: XCUIElement, to destination: URL) throws {
        guard window.exists else { throw DesignCaptureFailure.missingWindow }
        let frame = window.frame
        guard !frame.isEmpty else { throw DesignCaptureFailure.missingWindow }

        var regions: [Region] = []
        for element in window.descendants(matching: .any).allElementsBoundByAccessibilityElement.prefix(240) {
            guard regions.count < 80 else { break }
            guard let role = role(for: element), element.isEnabled else { continue }
            let bounds = element.frame
            guard !bounds.isEmpty, bounds.intersects(frame) else { continue }
            regions.append(Region(id: "r\(regions.count + 1)", role: role,
                                  bounds: [Double(bounds.minX - frame.minX), Double(bounds.minY - frame.minY),
                                           Double(bounds.width), Double(bounds.height)],
                                  hittable: element.isHittable))
        }

        guard window.exists, window.frame == frame else { throw DesignCaptureFailure.windowChanged }
        let evidence = Snapshot(viewport: [Double(frame.width), Double(frame.height)], regions: regions)
        try JSONEncoder().encode(evidence).write(to: destination, options: .withoutOverwriting)
    }
}
