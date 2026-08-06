import os

import modal
import rich

MOUNTPOINT = "/app"

app = modal.App.lookup("overeasy-example", create_if_missing=True)
console = rich.get_console()

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
        .apt_install("curl", "fuse3", "xxd")
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
    cmd = ["bash","-c", (" ".join(cmd) + " && sleep infinity")]

    ready_probe = modal.Probe.with_exec("sh", "-c", 'oe status', interval_ms=50)

    console.print("Creating sandbox", style="yellow")
    sb = modal.Sandbox.create(
        *cmd,
        app=app,
        image=image,
        experimental_options={"vm_runtime": True},
        timeout=20,
        region="us-east",
        env={var: os.environ.get(var) for var in env_vars},
        readiness_probe=ready_probe,
        cpu=2,
        memory=1024
    )

    console.print(f"Mounting session: {session_id if session_id is not None else '<new>'}", style="yellow")
    sb.wait_until_ready()
    if session_id is None:
        # Mount cmd stdouts the session ID
        for line in sb.stdout:
            session_id = line.strip()
            console.print(f"Started new session: {session_id}", style="yellow")
            break
    else:
        console.print("Mounted", style="yellow")

    return sb

def terminate_sandbox(sb: modal.Sandbox):
    # Overeasy events eagerly upload, taking ~150ms to become durable depending on sandbox->s3 latency
    # While not required, we can call `oe checkpoint` to await for all prior writes to become durable
    sb.exec("oe", "checkpoint").wait()

    sb.terminate()

class PersistentSandbox:
    def __init__(self):
        self.sb = None

    def repl(self):
        while True:
            line = input("> ")
            if line == "exit":
                break
            self.exec(line)

    def exec(self, line: str):
        if self.sb is None:
            self.sb = create_sandbox()

        try:
            p = self.sb.exec("bash", "-c", line)
            for line_out in p.stdout:
                print(line_out)
            console.print(p.stderr.read(), style="red")

        except (modal.exception.SandboxTerminatedError, modal.exception.NotFoundError) as e:
            console.print(f"Error: {e}", style="red")
            console.print("Resuming...", style="orange3")
            self.sb = None

            # Retry
            self.exec(line)


if __name__ == "__main__":
    psb = PersistentSandbox()
    psb.repl()
