// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "HermesBar",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(name: "HermesBar", targets: ["HermesBar"])
    ],
    targets: [
        .executableTarget(
            name: "HermesBar",
            path: "Sources/HermesBar",
            linkerSettings: [
                .linkedFramework("AppKit"),
                .linkedFramework("SwiftUI"),
                .linkedLibrary("sqlite3")
            ]
        )
    ]
)

