import modal
import os
import time

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


# Created on first mount
session_id: str | None = None

def create_sandbox() -> modal.Sandbox:
    global session_id

    cmd = ["oe", "mount"]
    if session_id is not None:
        cmd.append(session_id)

    ready_probe = modal.Probe.with_exec("oe", "status", interval_ms=50)
    sb = modal.Sandbox.create(
        *cmd,
        app=app,
        image=image,
        experimental_options={"vm_runtime": True},
        timeout=30,
        region="us-east",
        env={var: os.environ.get(var) for var in env_vars},
        readiness_probe=ready_probe,
    )

    sb.wait_until_ready()
    if session_id is None:
        # Mount cmd stdouts the session ID
        session_id = sb.stdout.read().strip()

    return sb

def terminate_sandbox(sb: modal.Sandbox):
    # Overeasy events eagerly upload, taking ~150ms to become durable depending on sandbox->s3 latency
    # While not required, we can call `oe checkpoint` to await for all prior writes to become durable
    sb.exec("oe", "checkpoint").wait()

    sb.terminate()

if __name__ == "__main__":
    sb = create_sandbox()
    print(f"Session ID: {session_id}")

    print("Writing marker.txt")
    sb.exec("bash", "-c", "echo 'hello world' > marker.txt").wait()

    print("Terminating sandbox")
    terminate_sandbox(sb)

    print("Resuming session in new sandbox")
    sb = create_sandbox()

    print("Reading marker.txt")
    p = sb.exec("bash", "-c", "cat marker.txt")
    print("->", p.stdout.read())
