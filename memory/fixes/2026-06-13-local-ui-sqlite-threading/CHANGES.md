# Changes

- Replaced the threaded local UI server with single-threaded `HTTPServer`.
- Added `make_ui_server()` so tests can assert the server type.
- Exported `make_ui_server` from the package.
- Added a regression test that locks the UI server to `HTTPServer`.
- Manually smoke-tested `/`, `/state`, and `/input` against a temporary local UI port.
