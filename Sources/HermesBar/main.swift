import AppKit
import Foundation
import SQLite3

struct HermesPaths {
    let home = FileManager.default.homeDirectoryForCurrentUser

    var configDirectory: URL { home.appendingPathComponent("Work/Hermes/.hermes", isDirectory: true) }
    var stateDatabase: URL { home.appendingPathComponent(".local/share/hermes/state.sqlite3", isDirectory: false) }
    var launchAgent: URL { home.appendingPathComponent("Library/LaunchAgents/com.imodeveloper.hermes.plist", isDirectory: false) }
    var stateDirectory: URL { home.appendingPathComponent(".local/share/hermes", isDirectory: true) }
    var hermesExecutable: URL { home.appendingPathComponent("Work/Hermes/.venv/bin/hermes", isDirectory: false) }
}

struct ServiceStatus {
    let state: String
    let lastExitCode: String
    let runs: String
    let pid: String?
}

struct ClaimRecord {
    let itemID: String
    let repoKey: String
    let stage: String
    let status: String
    let branchName: String?
    let worktreePath: String?
    let lastHeartbeatAt: String?
}

@MainActor
final class HermesBarApp: NSObject, NSApplicationDelegate {
    private let paths = HermesPaths()
    private let statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
    private let menu = NSMenu()
    private var timer: Timer?

    func applicationDidFinishLaunching(_ notification: Notification) {
        statusItem.button?.title = "Hermes"
        statusItem.menu = menu
        rebuildMenu()
        timer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { [weak self] _ in
            self?.rebuildMenu()
        }
        RunLoop.main.add(timer!, forMode: .common)
    }

    func applicationWillTerminate(_ notification: Notification) {
        timer?.invalidate()
    }

    private func rebuildMenu() {
        menu.removeAllItems()

        let service = fetchServiceStatus()
        let claims = fetchClaims()

        let titleItem = NSMenuItem(title: "Hermes Scheduler", action: nil, keyEquivalent: "")
        titleItem.isEnabled = false
        menu.addItem(titleItem)

        menu.addItem(disabledItem("State: \(service.state)"))
        menu.addItem(disabledItem("Last exit: \(service.lastExitCode)"))
        menu.addItem(disabledItem("Runs: \(service.runs)"))
        if let pid = service.pid {
            menu.addItem(disabledItem("PID: \(pid)"))
        }
        menu.addItem(disabledItem("Claims: \(claims.count)"))
        menu.addItem(.separator())

        if claims.isEmpty {
            menu.addItem(disabledItem("No active claims"))
        } else {
            let claimsHeader = disabledItem("Active Claims")
            menu.addItem(claimsHeader)
            for claim in claims {
                let summary = "\(claim.repoKey) • \(claim.stage) • \(claim.status)"
                menu.addItem(disabledItem(summary))
                menu.addItem(disabledItem("  \(claim.itemID)"))
                if let heartbeat = claim.lastHeartbeatAt {
                    menu.addItem(disabledItem("  heartbeat: \(heartbeat)"))
                }
            }
        }

        menu.addItem(.separator())
        menu.addItem(actionItem("Run Now", #selector(runNow)))
        menu.addItem(actionItem("Start Scheduler", #selector(startScheduler)))
        menu.addItem(actionItem("Stop Scheduler", #selector(stopScheduler)))
        menu.addItem(actionItem("Restart Scheduler", #selector(restartScheduler)))
        menu.addItem(.separator())
        menu.addItem(actionItem("Open Config", #selector(openConfig)))
        menu.addItem(actionItem("Open State Folder", #selector(openStateFolder)))
        menu.addItem(actionItem("Open LaunchAgent", #selector(openLaunchAgent)))
        menu.addItem(.separator())
        menu.addItem(actionItem("Quit HermesBar", #selector(quit)))

        updateTitle(for: service)
    }

    private func updateTitle(for status: ServiceStatus) {
        let suffix: String
        switch status.state.lowercased() {
        case "running":
            suffix = "●"
        case "not running":
            suffix = "○"
        default:
            suffix = "!"
        }
        statusItem.button?.title = "Hermes \(suffix)"
    }

    private func disabledItem(_ title: String) -> NSMenuItem {
        let item = NSMenuItem(title: title, action: nil, keyEquivalent: "")
        item.isEnabled = false
        return item
    }

    private func actionItem(_ title: String, _ selector: Selector) -> NSMenuItem {
        NSMenuItem(title: title, action: selector, keyEquivalent: "")
    }

    private func fetchServiceStatus() -> ServiceStatus {
        let command = "launchctl print gui/$(id -u)/com.imodeveloper.hermes"
        let output = runShell(command)
        return ServiceStatus(
            state: capture(in: output, pattern: #"state = ([^\n]+)"#) ?? "unknown",
            lastExitCode: capture(in: output, pattern: #"last exit code = ([^\n]+)"#) ?? "unknown",
            runs: capture(in: output, pattern: #"runs = ([^\n]+)"#) ?? "unknown",
            pid: capture(in: output, pattern: #"pid = ([^\n]+)"#)
        )
    }

    private func fetchClaims() -> [ClaimRecord] {
        var records: [ClaimRecord] = []
        var db: OpaquePointer?
        guard sqlite3_open(paths.stateDatabase.path, &db) == SQLITE_OK, let db else {
            if db != nil { sqlite3_close(db) }
            return records
        }
        defer { sqlite3_close(db) }

        let query = """
        SELECT item_id, repo_key, stage, status, branch_name, worktree_path, last_heartbeat_at
        FROM item_claims
        ORDER BY updated_at DESC
        """
        var statement: OpaquePointer?
        guard sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK, let statement else {
            return records
        }
        defer { sqlite3_finalize(statement) }

        while sqlite3_step(statement) == SQLITE_ROW {
            records.append(
                ClaimRecord(
                    itemID: stringValue(statement, index: 0),
                    repoKey: stringValue(statement, index: 1),
                    stage: stringValue(statement, index: 2),
                    status: stringValue(statement, index: 3),
                    branchName: optionalStringValue(statement, index: 4),
                    worktreePath: optionalStringValue(statement, index: 5),
                    lastHeartbeatAt: optionalStringValue(statement, index: 6)
                )
            )
        }
        return records
    }

    private func stringValue(_ statement: OpaquePointer, index: Int32) -> String {
        guard let cString = sqlite3_column_text(statement, index) else { return "" }
        return String(cString: cString)
    }

    private func optionalStringValue(_ statement: OpaquePointer, index: Int32) -> String? {
        guard sqlite3_column_type(statement, index) != SQLITE_NULL else { return nil }
        return stringValue(statement, index: index)
    }

    private func capture(in text: String, pattern: String) -> String? {
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return nil }
        let range = NSRange(location: 0, length: text.utf16.count)
        guard
            let match = regex.firstMatch(in: text, range: range),
            match.numberOfRanges > 1,
            let valueRange = Range(match.range(at: 1), in: text)
        else {
            return nil
        }
        return String(text[valueRange]).trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func runShell(_ command: String) -> String {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/zsh")
        process.arguments = ["-lc", command]

        let stdout = Pipe()
        let stderr = Pipe()
        process.standardOutput = stdout
        process.standardError = stderr

        do {
            try process.run()
            process.waitUntilExit()
            let out = String(data: stdout.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
            let err = String(data: stderr.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
            return out.isEmpty ? err : out
        } catch {
            return error.localizedDescription
        }
    }

    @objc private func runNow() {
        _ = runShell("launchctl start com.imodeveloper.hermes")
        rebuildMenu()
    }

    @objc private func startScheduler() {
        _ = runShell("launchctl load -w \(paths.launchAgent.path)")
        rebuildMenu()
    }

    @objc private func stopScheduler() {
        _ = runShell("launchctl unload \(paths.launchAgent.path)")
        rebuildMenu()
    }

    @objc private func restartScheduler() {
        _ = runShell("launchctl unload \(paths.launchAgent.path) >/dev/null 2>&1 || true; launchctl load -w \(paths.launchAgent.path); launchctl start com.imodeveloper.hermes")
        rebuildMenu()
    }

    @objc private func openConfig() {
        NSWorkspace.shared.open(paths.configDirectory)
    }

    @objc private func openStateFolder() {
        NSWorkspace.shared.open(paths.stateDirectory)
    }

    @objc private func openLaunchAgent() {
        NSWorkspace.shared.open(paths.launchAgent)
    }

    @objc private func quit() {
        NSApp.terminate(nil)
    }
}

@main
enum HermesBarMain {
    @MainActor
    static func main() {
        let application = NSApplication.shared
        let delegate = HermesBarApp()
        application.setActivationPolicy(.accessory)
        application.delegate = delegate
        application.run()
    }
}
