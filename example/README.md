# Overeasy in Modal Sandbox

This is an example for installing and running Overeasy in a Modal sandbox.

## Setup 
The following environment variables are required:
- `AWS_REGION`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `OVEREASY_BLOB_BUCKET`
- `S2_ACCESS_TOKEN`

For the fastest experience, we will be providing credentials to our own colocated resources, please contact us for those values.

You are also free to self host on your own credentials, acquired via [S2.dev](https://s2.dev) and [AWS S3](https://aws.amazon.com/s3/).

## Usage

With your environment variables set, run the following command from within this example directory:
```bash
uv run main.py
```

[main.py](main.py) shows you how to:
- install Overeasy into a Modal Image
- start a sandbox and mount a working directory
- write new files into that directory
- terminate that sandbox, boot a new one, and mount to the same session
  - and see the same durable content
