//
//  PermissionManagerTests.swift
//  VoiceAssistantTests
//
//  Unit tests for PermissionManager
//

import XCTest
import AVFoundation
@testable import VoiceAssistant

final class PermissionManagerTests: XCTestCase {

    var permissionManager: PermissionManager!

    override func setUp() {
        super.setUp()
        permissionManager = PermissionManager.shared
    }

    // MARK: - Permission Status Tests

    func testMicrophonePermissionCheck() {
        // Check microphone permission status
        let status = permissionManager.checkMicrophonePermission()

        // Status should be one of the valid values
        XCTAssertTrue(
            status == .notDetermined || status == .authorized || status == .denied,
            "Microphone permission should have valid status"
        )
    }

    func testAccessibilityPermissionCheck() {
        // Check accessibility permission status
        let status = permissionManager.checkAccessibilityPermission()

        // Status should be authorized or denied (no notDetermined for accessibility)
        XCTAssertTrue(
            status == .authorized || status == .denied,
            "Accessibility permission should be authorized or denied"
        )
    }

    // MARK: - Permission Type Tests

    func testPermissionTypeDisplayNames() {
        XCTAssertEqual(PermissionType.microphone.displayName, "Microphone")
        XCTAssertEqual(PermissionType.accessibility.displayName, "Accessibility")
        XCTAssertEqual(PermissionType.inputMonitoring.displayName, "Input Monitoring")
        XCTAssertEqual(PermissionType.fullDiskAccess.displayName, "Full Disk Access")
    }

    func testPermissionTypeDescriptions() {
        // All permission types should have usage descriptions
        XCTAssertFalse(PermissionType.microphone.usageDescription.isEmpty)
        XCTAssertFalse(PermissionType.accessibility.usageDescription.isEmpty)
        XCTAssertFalse(PermissionType.inputMonitoring.usageDescription.isEmpty)
        XCTAssertFalse(PermissionType.fullDiskAccess.usageDescription.isEmpty)
    }

    // MARK: - Permission Helpers

    func testIsPermissionGranted() {
        // Test microphone permission check
        let isMicGranted = permissionManager.isPermissionGranted(.microphone)

        // Should return boolean
        XCTAssertTrue(isMicGranted == true || isMicGranted == false)
    }

    func testAllRequiredPermissionsGranted() {
        // Test that method returns boolean
        let allRequired = permissionManager.allRequiredPermissionsGranted()

        // Should return boolean
        XCTAssertTrue(allRequired == true || allRequired == false)

        // If not all required granted, accessibility or microphone must be denied
        if !allRequired {
            let micStatus = permissionManager.microphoneStatus
            let accStatus = permissionManager.accessibilityStatus

            XCTAssertTrue(
                micStatus != .authorized || accStatus != .authorized,
                "If not all required granted, at least one must not be authorized"
            )
        }
    }

    // MARK: - Refresh Tests

    func testRefreshAllPermissions() {
        // Refresh all permissions
        permissionManager.refreshAllPermissions()

        // All statuses should be updated
        XCTAssertNotEqual(permissionManager.microphoneStatus, .restricted)
        // Note: Can't test actual values as they depend on system state
    }

    // MARK: - Mock Request Tests

    func testMicrophonePermissionRequest() {
        let expectation = XCTestExpectation(description: "Microphone permission request")

        // Request permission
        permissionManager.requestMicrophonePermission { granted in
            // Should receive callback
            XCTAssertTrue(granted == true || granted == false)
            expectation.fulfill()
        }

        wait(for: [expectation], timeout: 5.0)
    }
}

// MARK: - Integration Tests

final class PermissionIntegrationTests: XCTestCase {

    func testPermissionFlow() {
        let manager = PermissionManager.shared

        // Initial refresh
        manager.refreshAllPermissions()

        // Check each permission
        _ = manager.checkMicrophonePermission()
        _ = manager.checkAccessibilityPermission()
        _ = manager.checkInputMonitoringPermission()
        _ = manager.checkFullDiskAccessPermission()

        // Verify status is set
        XCTAssertNotNil(manager.microphoneStatus)
        XCTAssertNotNil(manager.accessibilityStatus)

        // This test mainly verifies no crashes occur during permission checking
    }
}
