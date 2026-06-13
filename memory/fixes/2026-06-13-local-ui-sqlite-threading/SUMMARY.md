# Local UI SQLite Threading Fix

Date: 2026-06-13
Status: Complete

Fixed `mneme ui` failing in the browser with `sqlite3.ProgrammingError` because `ThreadingHTTPServer` handled browser requests on worker threads while `MnemeRuntime` owned a SQLite connection created on the CLI thread.

The local UI now uses a single-threaded `HTTPServer`, which keeps runtime snapshot and input handling on the same thread as the SQLite connection. This is appropriate for the Stage 6 local dashboard and avoids loosening SQLite safety globally.
