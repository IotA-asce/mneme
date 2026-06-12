# Context

Mneme's runtime architecture needs parallel perception-style observations before real sensors exist. The repository already had local runtime events, sensory echo, and working memory, but there was no deterministic way to feed realistic event sequences through them.

This feature adds local simulation and replay only. It lets tests and demos publish representative perception observations through the same event bus that future ROS adapters can target.
