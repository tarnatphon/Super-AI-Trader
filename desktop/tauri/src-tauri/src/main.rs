// Super-AI-Trader native shell.
//
// The real app is the local Python server (start_app.py -> 127.0.0.1:8787).
// This Tauri shell opens a real native window that loads that local page,
// so there is no browser chrome — everything still runs on-device and is
// reachable over Tailscale from your phone.
fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|_app| {
            // Spawn the local server sidecar. In dev the beforeDevCommand
            // already starts it; in a bundled build you would sidecar the
            // Python launcher (or a bundled interpreter).
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Super-AI-Trader");
}
