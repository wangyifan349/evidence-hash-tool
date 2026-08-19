# Security Policy

## Reporting a security issue

If you discover a security issue in the hashing logic, path handling, manifest generation, or integrity calculations, please open a GitHub issue with a minimal reproducible example.

Do not include:

- private evidence files;
- confidential file names;
- private directory paths;
- credentials;
- API keys;
- personal information;
- sensitive records.

## Scope

This project performs local file hashing and manifest generation only.

It does not provide:

- file encryption;
- secure deletion;
- trusted timestamping;
- identity verification;
- digital signatures;
- remote backup;
- blockchain publication.

For important evidence, preserve the final `Merkle Root` or `Chain Tip` independently from the storage device that contains the original files.
