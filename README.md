# `overeasy`: FUSE for Time Travel

`overeasy` is a FUSE filesystem with overlay semantics implemented in Rust.

The FUSE filesystem is mounted over a directory whose base state is the directory itself. Every mutation is captured as a delta in the *upper* layer via copy-on-write (COW): on first write, a lower file is promoted to upper, and all subsequent reads serve the upper copy.

`overeasy` intercepts the VFS operations (`lookup`, `getattr`, `read`, `write`, `create`, `unlink`, `rename`, `mkdir`, etc.) of the mount. Each hook further emits a structured mutation record to an append-only log.

Ultimately, we aim to use `overeasy` as the underlying technology for time travel over sandbox state.

## Installation

Download the latest `overeasy` binary for your platform from the
[Releases page](https://github.com/modal-labs/overeasy/releases).

```bash
tar -xzf overeasy-<version>-<arch>-unknown-linux-gnu.tar.gz
sudo install -m 0755 overeasy /usr/local/bin/
```

## Setup

Install s2-lite server
```bash
curl -fsSL https://raw.githubusercontent.com/s2-streamstore/s2/main/install.sh | bash
```

Ensure it's in your PATH
```bash
which s2
```

Start the server
```bash
s2 lite --port 8080
```

Overeasy will default look for a localhost s2 lite.
To instead point to managed s2, set `S2_ACCESS_TOKEN`.

## Running

Mount `lower/` as the overlay (lower = existing contents of `lower/`, upper and log stream will go into `./.lower.overeasy`):

run in default session
```bash
overeasy run
```

list sessions
```bash
overeasy session ls
```

branch a session at timestamp
```bash
overeasy session branch --base <session_id> --to <timestamp>
```
