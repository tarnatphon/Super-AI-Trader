// Super-AI-Trader native shell (Tauri v2).
//
// The whole trading app is the local Python server (super_ai_trader.web),
// running on 127.0.0.1:8787. This native binary:
//   1. starts that local server as a child process (the Python app),
//   2. waits until the port responds,
//   3. opens a native window loading http://127.0.0.1:8787,
//   4. kills the child server when the window closes.
//
// Everything stays local and private; no cloud, no keys leave the machine.

use std::process::{Child, Command, Stdio};
use std::thread;
use std::time::{Duration, Instant};

fn start_server() -> Child {
    // We rely on the bundled PyInstaller binary when packaged; in dev we run
    // the module directly. The launcher script (scripts/run_local_server.sh)
    // is the single place that resolves which one to call.
    let script = concat!(env!("CARGO_MANIFEST_DIR"), "/../../scripts/start_server.sh");
    Command::new("bash")
        .arg(script)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .expect("failed to start the local Super-AI-Trader server")
}

fn wait_for_port(seconds: u64) -> bool {
    let start = Instant::now();
    while start.elapsed().as_secs() < seconds {
        if std::net::TcpStream::connect("127.0.0.1:8787").is_ok() {
            return true;
        }
        thread::sleep(Duration::from_millis(500));
    }
    false
}

fn main() {
    let mut child = start_server();
    wait_for_port(60);

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .on_window_event(move |event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event.event() {
                // Stop the local server when the native window closes.
                let _ = child.kill();
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running Super AI Trader");
}
