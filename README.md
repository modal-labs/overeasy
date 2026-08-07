# 🍳 Overeasy - branching filesystem for agents and RL

Overeasy is a filesystem state manager for coding agents and RL rollouts. It uses an [append-only log](https://s2.dev) on [S3](https://aws.amazon.com/s3/) for durability, allowing you to pause-resume an agent/RL filesystem state across hosts, revert to previous states, and cheaply branch into parallel states.

The filesystem is served as a [FUSE](https://www.kernel.org/doc/html/next/filesystems/fuse.html) mount overlay over a base directory. Changes are copy-on-write, isolating mutations from your agent/rollout under a `Session` ID. Sessions can be paused, resumed, branched, and reverted to any prior state using the Overeasy CLI.

## Quickstart
The intended way to use Overeasy is in [Modal Sandboxes](https://modal.com/docs/guide/sandboxes#sandboxes), though it'd work on any Linux machine /dev/fuse available!

[See here for a working example](example/README.md) of Overeasy running as the filesystem durability layer in a Modal Sandbox environment.

## Installation
```bash
curl -sSL https://raw.githubusercontent.com/modal-labs/overeasy/main/install.sh | bash
```
This will install the `overeasy` CLI (aliased to `oe`) into your machine.

### Environment Setup
Overeasy uses S3 and S2 keys as dependencies. For the fastest experience, we will be providing credentials to our own colocated resources, please contact us for those values.

You are also free to self host on your own credentials, acquired via S2.dev and AWS S3.

## Example Usage:
### Create a new session
```bash
oe session new 
# -> <new_session_id>
```
Create a new session relative to the current directory.

> Each session is a diff relative to a stable "lower" directory, so the session becomes invalid if the lower directory changes outside of a session mount. The lower may be specified using `--lower`, defaulting to the current working directory.

### Serve a session as a mounted overlay
```bash
oe mount <session_id>
```

Mount over the current directory and [serve](https://www.kernel.org/doc/html/next/filesystems/fuse.html) the state for <session_id>.

For a newly created session, the mounted view will show the unmodified lower directory. Modifications to the file contents while the server is running will be isolated to the session.

To unmount:
```bash
oe unmount
```
This will make the current directory return to its unmodified state.

> Important: A session should only ever be served by one host at a time.

### Resume a session
```bash
oe mount <session_id>
# -> <session_id>
```
Mounting over the current directory with a session ID will resume from the latest state.

### List sessions
```bash
oe session ls
```
List sessions known to this host. Sessions started on other hosts may not be listed, but will be discovered when used in a mount.

### Branch from the current state
```bash
oe session branch <session_id>
# -> <new_session_id>
```
Branch from the tail of the specified session, creating a new session ID. 

The original session remains valid, and may be resumed from. 


### Revert to a previous state
```bash
oe session branch <session_id> --to <timestamp>
# -> <new_session_id>
```
Revert back to a previous state of the specified session using the `--to` flag in a `branch` commmand.

Session logs are append-only, so reverts really are just new branches starting from a previous state. The original session remains valid.

### Ensure durability
```bash
oe checkpoint
# -> timestamp
```
Block until all outstanding writes have been acked durable on S3, returning the timestamp of the tail of the durable stream.

This operation is equivalent to `fsync` to the durable tier. This is not required, as writes eagerly push to durable, but is useful for producing a timestamp to use in a `session branch --to <timestamp>`.
