# Context

The default `mneme run` command started the virtual head and then blocked on standard input. The user-visible banner made it look alive, but after typing a line the response was accumulated internally and not printed until the process exited. Also, local speech/vision profiles needed a non-keyboard loop for continuous perception ticking.

This fix separates:

- typed terminal mode: waits for user text and prints a response per turn,
- live ticking mode: repeatedly calls runtime ticks so configured perception workers can run.

Plain `mneme run` still does not open microphones or cameras.

