# Context

The browser failed to load `mneme ui`; each GET request produced:

```text
sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread
```

The UI server was using `ThreadingHTTPServer`. `MnemeRuntime` and its SQLite-backed `MemoryEngine` were created in the CLI thread, but request handlers ran in worker threads and called `runtime.snapshot()`, which reads table counts through SQLite.
