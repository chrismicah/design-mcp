import Foundation
import XCTest

final class ReviewFixtureTests: XCTestCase {
    func testExportsLiveWindowBeforeAndAfterRevealingControl() throws {
        let app = XCUIApplication()
        app.launch()
        defer { app.terminate() }

        let window = app.windows["Desk review fixture"]
        XCTAssertTrue(window.waitForExistence(timeout: 10))
        let reveal = window.buttons["reveal"]
        let revealed = window.buttons["revealed"]
        XCTAssertTrue(reveal.isHittable)
        XCTAssertFalse(revealed.exists)
        XCTAssertTrue(window.staticTexts["Control hidden"].exists)

        let destination = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: destination, withIntermediateDirectories: false)
        let before = try capture(window: window, state: "before", in: destination)
        reveal.click()
        XCTAssertTrue(revealed.waitForExistence(timeout: 5))
        XCTAssertTrue(revealed.isHittable)
        XCTAssertTrue(window.staticTexts["Control revealed"].exists)
        _ = try capture(window: window, state: "after", in: destination)

        let beforeFile = destination.appendingPathComponent("before.json")
        XCTAssertThrowsError(try DesignCapture.export(window: window, to: beforeFile))
        XCTAssertEqual(try Data(contentsOf: beforeFile), before)
        let missing = app.windows["No such fixture window"]
        let refused = destination.appendingPathComponent("missing.json")
        XCTAssertThrowsError(try DesignCapture.export(window: missing, to: refused)) { error in
            guard case DesignCaptureFailure.missingWindow = error else {
                return XCTFail("Expected a missing window, got \(error)")
            }
        }
        XCTAssertFalse(FileManager.default.fileExists(atPath: refused.path))
    }

    private func capture(window: XCUIElement, state: String, in directory: URL) throws -> Data {
        let output = directory.appendingPathComponent("\(state).json")
        try DesignCapture.export(window: window, to: output)
        let data = try Data(contentsOf: output)
        XCTAssertFalse(String(decoding: data, as: UTF8.self).contains("swift-review-fixture-private-marker"))
        let geometry = XCTAttachment(data: data, uniformTypeIdentifier: "public.json")
        geometry.name = "design-capture-\(state)"
        geometry.lifetime = .keepAlways
        add(geometry)

        let pixels = XCTAttachment(screenshot: window.screenshot())
        pixels.name = "window-pixels-\(state)"
        pixels.lifetime = .keepAlways
        add(pixels)
        return data
    }
}
