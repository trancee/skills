# Xcode MCP over SSH

## Choose the actual server

| Server | Backend/session | Remote fit | Signing limit |
|---|---|---|---|
| Apple traditional `xcrun mcpbridge` | Xcode app/tools, approved Intelligence toggle, open project | SSH transports stdio; a working remote GUI/session/project remains required by this documented path | Same build settings, identities, trust, keychain and profiles |
| Apple Xcode 27 headless preview | New service without an open workspace | Potentially useful for unattended agents; verify installed command/status, permissions, and exact release behavior | Preview can require relaunch/reboot; authorization is separate from signing |
| MobileBuildMCP 2.7.1 (formerly XcodeBuildMCP) | CLI `xcodebuild`/Apple platform tools; optional IDE proxy | Good fit for SSH build/test/simulator/device orchestration, subject to tool/host availability | Documentation explicitly says it cannot configure signing or create/manage profiles automatically |
| `r-huijts/xcode-mcp-server` | Separate Node server exposing project/build/archive/export commands | Can be launched over SSH stdio; inspect exact implementation/tool schema | Not Apple's bridge; broad filesystem/tool access and signing prerequisites still need review |

Default for CI artifacts: **direct xcodebuild archive/export**. Add an MCP server when an agent needs discovery, diagnostics, tests, preview/simulator control, or interactive iteration. No MCP server converts a locked/untrusted/unusable identity into a signing identity.

## Apple traditional bridge

First-party setup: [Giving external agents access to Xcode](https://developer.apple.com/documentation/xcode/giving-external-agents-access-to-xcode).

1. In the remote user's Xcode > Settings > Intelligence, explicitly approve “Allow external agents to use Xcode tools.”
2. Open the intended project in that user's running Xcode.
3. Confirm full Xcode selection and `xcrun --find mcpbridge`; inspect installed bridge help.
4. Launch the bridge through SSH from the external client's stdio configuration:

```json
{
  "mcpServers": {
    "remote-xcode": {
      "command": "ssh",
      "args": [
        "-T", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
        "build-mac",
        "/usr/bin/env DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer' /usr/bin/xcrun mcpbridge"
      ]
    }
  }
}

```
These SSH configurations are transport designs derived from documented local stdio startup, not an observed remote-Mac handshake or an Apple SSH support guarantee. Verify the remote process identity, session/permissions, and actual MCP initialization on the selected host.

`build-mac` is a configured SSH alias, not a discovered project path. Establish its host key privately before unattended use. Authentication failure goes to stderr and must fail; do not disable verification to make startup work. Multiple Xcode instances/session targeting may require version-specific bridge options; inspect help instead of inventing a PID environment variable.

This JSON is a generic stdio-client shape; translate to the actual client's schema. MCP runs **on the Mac**. Local client paths/environment do not describe the remote filesystem or automatically propagate over SSH.

## Xcode 27 headless preview

[Xcode 27 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-27-release-notes), Coding Intelligence, issue 181836944:

- Notes describe a preview introduced in Beta 5 that does not require an open workspace.
- Inspect `xcrun mcp-server --help` and `xcrun mcp-server status` on the actual selected Xcode.
- Administrator enabling uses `sudo xcrun mcp-server enable`; it is an authorization/service configuration change requiring explicit approval.
- Notes also document an **unsafe all-agent permission mode** for unattended environments. Do not choose it by default, edit private HeadlessPermissions JSON, or bypass approval because an SSH process lacks permission.
- Early-preview commands/settings may not work in all configurations and may need Xcode relaunch/reboot. Verify transport endpoint/bridge use and MCP initialize/tool discovery after enabling; do not infer a stable headless API from the feature headline.
- Xcode 27 itself requires macOS 26.6+ per those notes.

Prefer narrow project-directory/agent authorization where the installed service supports it. If the only available unattended policy is broader than the user approves, keep the direct CLI workflow; do not silently grant broad access.

## MobileBuildMCP

Current verified npm/release: `mobilebuildmcp@2.7.1`, git `d13ff0c707b0681769cf31da0eb42c4f94ceafff`. The old getsentry/XcodeBuildMCP repository/site redirect to **MobileBuildMCP**; legacy package/env/config names must not be mixed with the current ones.

Install a pinned package on the Mac or use a reviewed official macOS release. Verify `mobilebuildmcp --help`, `mobilebuildmcp tools`, and relevant subcommand help. README minimums: macOS 14.5+, Xcode 16+, Node 18+ for npm; dependency requirements and chosen Xcode can raise the effective floor. Prefer a supported current Node LTS rather than relying on the README alone.

Example remote stdio configuration (Apple Silicon Homebrew path shown; discover the actual remote executable):

```json
{
  "mcpServers": {
    "remote-mobilebuild": {
      "command": "ssh",
      "args": [
        "-T", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
        "build-mac",
        "/usr/bin/env DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer' MOBILEBUILDMCP_SENTRY_DISABLED=true MOBILEBUILDMCP_CWD='/Users/ci/Projects/MyApp' MOBILEBUILDMCP_ENABLED_WORKFLOWS='simulator' /opt/homebrew/bin/mobilebuildmcp mcp"
      ]
    }
  }
}
```

- No PTY (`-T`), login banners, `echo`, progress output, or stdout logging in the stdio protocol channel. Remote startup diagnostics belong on stderr. Do not allocate `ssh -t` for MCP.
- Set remote working directory/config/session defaults explicitly; paths are Mac paths. `.mobilebuildmcp/config.yaml` and runtime session defaults may override bootstrap env.
- Default workflow is simulator; add `device` only for authorized, paired hardware. A simulator build does not prove device signing.
- Keep `xcode-ide` proxy disabled for a pure CLI/headless job unless that branch's Apple session prerequisites are met.
- Server docs recommend one-time project signing setup in Xcode; actual CLI signing can instead be provisioned through the independently approved keychain/profile workflow. The server itself does not enroll teams or provision profiles.
- Discover tools via MCP `tools/list`; use the exact selected schema. `extraArgs` are build arguments, `launchArgs` are app arguments. Do not assume archive/export exists just because a build tool accepts extra arguments.
- Macro validation may be skipped by this server's build wrappers per its README. That is a supply-chain/trust policy change: review the behavior for the pinned version; do not import it silently into a release pipeline.
- Disable telemetry where required using the **remote** `MOBILEBUILDMCP_SENTRY_DISABLED=true` or project `sentryDisabled: true`; a local client env field is not automatically sent to the Mac.
- Server filesystem/process permissions remain the remote user's permissions. Tool annotations are hints, not authorization. Expose no unauthenticated MCP TCP/HTTP service on the public network.

Sources: [maintained repository](https://github.com/getsentry/MobileBuildMCP), [stdio mode](https://github.com/getsentry/xcodebuildmcp.com/blob/main/app/docs/_content/mcp-mode.mdx), [device signing](https://github.com/getsentry/xcodebuildmcp.com/blob/main/app/docs/_content/device-signing.mdx), [configuration](https://github.com/getsentry/xcodebuildmcp.com/blob/main/app/docs/_content/configuration.mdx), [privacy](https://github.com/getsentry/xcodebuildmcp.com/blob/main/app/docs/_content/privacy.mdx), [separately named server](https://github.com/r-huijts/xcode-mcp-server).
