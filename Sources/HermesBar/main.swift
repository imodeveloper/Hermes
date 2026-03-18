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
    let isLoaded: Bool
    let isRunning: Bool
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
    let prNumber: Int?
    let branchName: String?
    let worktreePath: String?
    let lastHeartbeatAt: String?
    let createdAt: String
    let updatedAt: String
}

struct ProjectItemSummary {
    let title: String
    let issueNumber: Int?
    let repository: String?
}

@MainActor
final class HermesBarApp: NSObject, NSApplicationDelegate {
    private let paths = HermesPaths()
    private let statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
    private let menu = NSMenu()
    private var timer: Timer?
    private var projectItemCache: [String: ProjectItemSummary] = [:]
    private var projectItemCacheUpdatedAt: Date?
    private var nextProjectItemRefreshAt: Date?

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
        let projectItems = claims.isEmpty ? [:] : fetchProjectItems(forceRefresh: false)
        let displayState = humanReadableState(for: service)

        let titleItem = NSMenuItem(title: "Hermes Scheduler", action: nil, keyEquivalent: "")
        titleItem.isEnabled = false
        menu.addItem(titleItem)

        menu.addItem(disabledItem("State: \(displayState)"))
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
                let itemSummary = projectItems[claim.itemID]
                let issuePrefix: String
                if let issueNumber = itemSummary?.issueNumber {
                    issuePrefix = "#\(issueNumber)"
                } else {
                    issuePrefix = claim.itemID
                }
                menu.addItem(disabledItem("\(issuePrefix) \(itemSummary?.title ?? "Unknown ticket")"))
                menu.addItem(disabledItem("  \(claim.repoKey) • \(humanReadableStage(claim.stage)) • \(humanReadableClaimStatus(claim.status))"))

                var timerBits: [String] = []
                timerBits.append("claimed \(relativeTimeString(from: claim.createdAt))")
                if let heartbeat = claim.lastHeartbeatAt {
                    timerBits.append("heartbeat \(relativeTimeString(from: heartbeat))")
                } else {
                    timerBits.append("heartbeat pending")
                }
                menu.addItem(disabledItem("  \(timerBits.joined(separator: " • "))"))

                if let prNumber = claim.prNumber {
                    menu.addItem(disabledItem("  PR #\(prNumber)"))
                }
            }
        }

        menu.addItem(.separator())
        menu.addItem(actionItem("Run Now", #selector(runNow)))
        menu.addItem(actionItem("Start Scheduler", #selector(startScheduler), enabled: !service.isLoaded))
        menu.addItem(actionItem("Stop Scheduler", #selector(stopScheduler), enabled: service.isLoaded))
        menu.addItem(actionItem("Restart Scheduler", #selector(restartScheduler), enabled: service.isLoaded))
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
        switch humanReadableState(for: status) {
        case "Running now":
            suffix = "●"
        case "Idle":
            suffix = "○"
        case "Stopped":
            suffix = "⏸"
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
        actionItem(title, selector, enabled: true)
    }

    private func actionItem(_ title: String, _ selector: Selector, enabled: Bool) -> NSMenuItem {
        let item = NSMenuItem(title: title, action: selector, keyEquivalent: "")
        item.isEnabled = enabled
        return item
    }

    private func fetchServiceStatus() -> ServiceStatus {
        let command = "launchctl print gui/$(id -u)/com.imodeveloper.hermes"
        let output = runShell(command)
        let isLoaded = !output.contains("Could not find service") && !output.contains("not found")
        let rawState = capture(in: output, pattern: #"state = ([^\n]+)"#) ?? (isLoaded ? "unknown" : "not loaded")
        return ServiceStatus(
            isLoaded: isLoaded,
            isRunning: rawState == "running",
            state: rawState,
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
        SELECT item_id, repo_key, stage, status, pr_number, branch_name, worktree_path, last_heartbeat_at, created_at, updated_at
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
                    prNumber: optionalIntValue(statement, index: 4),
                    branchName: optionalStringValue(statement, index: 5),
                    worktreePath: optionalStringValue(statement, index: 6),
                    lastHeartbeatAt: optionalStringValue(statement, index: 7),
                    createdAt: stringValue(statement, index: 8),
                    updatedAt: stringValue(statement, index: 9)
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

    private func optionalIntValue(_ statement: OpaquePointer, index: Int32) -> Int? {
        guard sqlite3_column_type(statement, index) != SQLITE_NULL else { return nil }
        return Int(sqlite3_column_int(statement, index))
    }

    private func fetchProjectItems(forceRefresh: Bool) -> [String: ProjectItemSummary] {
        let now = Date()
        if !forceRefresh, let nextRefreshAt = nextProjectItemRefreshAt, now < nextRefreshAt {
            return projectItemCache
        }
        if !forceRefresh, let updatedAt = projectItemCacheUpdatedAt, now.timeIntervalSince(updatedAt) < 300 {
            return projectItemCache
        }

        guard
            let config = loadProjectConfiguration(),
            let data = runShellData("gh project item-list \(config.number) --owner \(config.owner) --format json")
        else {
            nextProjectItemRefreshAt = now.addingTimeInterval(600)
            return projectItemCache
        }

        guard
            let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
            let items = root["items"] as? [[String: Any]]
        else {
            nextProjectItemRefreshAt = now.addingTimeInterval(600)
            return projectItemCache
        }

        var summaries: [String: ProjectItemSummary] = [:]
        for item in items {
            guard let itemID = item["id"] as? String else { continue }
            let content = item["content"] as? [String: Any]
            let itemTitle = (content?["title"] as? String) ?? (item["title"] as? String) ?? "Unknown ticket"
            let issueNumber = content?["number"] as? Int
            let repository = content?["repository"] as? String
            summaries[itemID] = ProjectItemSummary(title: itemTitle, issueNumber: issueNumber, repository: repository)
        }

        projectItemCache = summaries
        projectItemCacheUpdatedAt = now
        nextProjectItemRefreshAt = now.addingTimeInterval(300)
        return summaries
    }

    private func loadProjectConfiguration() -> (owner: String, number: Int)? {
        guard let text = try? String(contentsOf: paths.configDirectory.appendingPathComponent("hermes.yaml")) else {
            return nil
        }
        guard
            let owner = capture(in: text, pattern: #"owner:\s*([^\n]+)"#),
            let numberText = capture(in: text, pattern: #"number:\s*([0-9]+)"#),
            let number = Int(numberText)
        else {
            return nil
        }
        return (owner.trimmingCharacters(in: .whitespacesAndNewlines), number)
    }

    private func humanReadableState(for status: ServiceStatus) -> String {
        if !status.isLoaded {
            return "Stopped"
        }
        if status.isRunning {
            return "Running now"
        }
        if status.lastExitCode == "0" {
            return "Idle"
        }
        return "Failed"
    }

    private func humanReadableStage(_ stage: String) -> String {
        switch stage.lowercased() {
        case "triage":
            return "Triaging"
        case "execute":
            return "Executing"
        case "review":
            return "Reviewing"
        case "release":
            return "Releasing"
        default:
            return stage.capitalized
        }
    }

    private func humanReadableClaimStatus(_ status: String) -> String {
        switch status.lowercased() {
        case "claimed":
            return "Claimed"
        case "active":
            return "Active"
        case "stale":
            return "Stale"
        default:
            return status.capitalized
        }
    }

    private func relativeTimeString(from timestamp: String) -> String {
        guard let date = parseTimestamp(timestamp) else {
            return timestamp
        }
        let seconds = max(0, Int(Date().timeIntervalSince(date)))
        if seconds < 60 {
            return "\(seconds)s ago"
        }
        let minutes = seconds / 60
        if minutes < 60 {
            return "\(minutes)m ago"
        }
        let hours = minutes / 60
        if hours < 24 {
            return "\(hours)h ago"
        }
        let days = hours / 24
        return "\(days)d ago"
    }

    private func parseTimestamp(_ text: String) -> Date? {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = formatter.date(from: text) {
            return date
        }

        let fallback = ISO8601DateFormatter()
        fallback.formatOptions = [.withInternetDateTime]
        return fallback.date(from: text)
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
        guard let data = runShellData(command) else {
            return ""
        }
        return String(data: data, encoding: .utf8) ?? ""
    }

    private func runShellData(_ command: String) -> Data? {
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
            let out = stdout.fileHandleForReading.readDataToEndOfFile()
            let err = stderr.fileHandleForReading.readDataToEndOfFile()
            return out.isEmpty ? err : out
        } catch {
            return error.localizedDescription.data(using: .utf8)
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
