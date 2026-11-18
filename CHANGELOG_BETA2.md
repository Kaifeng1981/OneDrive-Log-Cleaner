# OneDrive Log Cleaner — v1.0 Beta 2

## Safety changes
- Replaced broad extension deletion with a conservative allowlist.
- Added a cleanup preview with file count, estimated size, skipped count, and explicit confirmation.
- Cleanup no longer force-terminates OneDrive processes.
- Locked, inaccessible, symbolic-link, and out-of-scope files are skipped and recorded.
- Background threshold monitoring is alert-only; automatic deletion is disabled.

## Migration changes
- Copy to a staging directory before touching the source.
- Verify copied file count and total bytes.
- Preserve the original directory as a timestamped backup.
- Create the NTFS Junction only after verification; attempt rollback if link creation fails.

## Notes
- This is a development build on the beta2-development branch. The main branch is unchanged.
- Windows runtime testing is still required, especially Junction creation/rollback and OneDrive file-lock behavior.
- Replaced the previous icon with a distinct cloud + log document + checkmark design.
