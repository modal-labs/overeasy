from re import M

import modal
import os

MOUNTPOINT = "/app"

app = modal.App.lookup("overeasy-example", create_if_missing=True)

# These environment variables are required locally to get started
env_vars = [
    "AWS_REGION",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "OVEREASY_BLOB_BUCKET",
    "S2_ACCESS_TOKEN"
]
for var in env_vars:
    if not os.environ.get(var):
        raise ValueError(f"Environment variable {var} is not set")

# Build the overeasy binary into a Docker image
with modal.enable_output():
    image = (
        modal.Image.debian_slim()
        .apt_install("curl", "fuse3")
        .run_commands(
            "curl -sSL https://raw.githubusercontent.com/modal-labs/overeasy/main/install.sh | bash",
        )
        # Run all execs in an empty mountpoint directory (overeasy cannot mount to root)
        .run_commands(f"mkdir -p {MOUNTPOINT}")
        .workdir(MOUNTPOINT)
    ).build(app)

sb = modal.Sandbox.create(
    app=app,
    image=image,
    experimental_options={"vm_runtime": True},
    timeout=30,
    env={var: os.environ.get(var) for var in env_vars}
)

# Helper function for mounting an overeasy session
def start_session(sb: modal.Sandbox, session_id: str | None = None) -> str:
    """Starts an overeasy session with the given session ID, or creates a new one if none is provided. Returns the session ID."""

    if session_id is None:
        # Create a new session ID
        p = sb.exec("bash", "-c", "oe session new")
        session_id = p.stdout.read().strip()

    # Mount the session
    log = "/tmp/oe.log"
    pidfile = "/tmp/oe.pid"
    p = sb.exec("bash", "-c", f"echo $$ > {pidfile}; exec oe mount {session_id} > {log} 2>&1")

    # Wait until the mountpoint is ready
    poll_ready_cmd = f"""
    until mountpoint -q {MOUNTPOINT}; do
        pid=$(cat {pidfile} 2>/dev/null)
        if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then
            echo "process exited before mountpoint was ready"
            exit 1
        fi
        sleep 0.1
    done
    """
    sb.exec("bash", "-c", poll_ready_cmd).wait()

    return session_id

session_id = start_session(sb)
print(f"Session ID: {session_id}")

print("Writing marker.txt")
sb.exec("bash", "-c", "echo 'hello world' > marker.txt").wait()

print("Reading marker.txt")
p = sb.exec("bash", "-c", "cat marker.txt")
print("->", p.stdout.read())

# Events async upload, taking ~500ms to become durable
# While not required, we can ensure durability with `oe checkpoint`
print("Synced to timestamp:", sb.exec("bash", "-c", "oe checkpoint").stdout.read().strip())

print("Terminating sandbox")
sb.terminate()

print("Resuming session in new sandbox")
sb = modal.Sandbox.create(
    app=app,
    image=image,
    experimental_options={"vm_runtime": True},
    timeout=30,
    env={var: os.environ.get(var) for var in env_vars}
)

start_session(sb, session_id)
print(f"Session ID: {session_id}")

print("Reading marker.txt")
p = sb.exec("bash", "-c", "cat marker.txt")
print("->", p.stdout.read())
