# Local Ollama Cognition Adapter

Date: 2026-06-13
Status: Complete

Added the first local-cognition runtime slice: a fake model runtime for tests, an Ollama HTTP adapter, and `mneme cognition check` for service/model/probe readiness.

This does not make Ollama drive Mneme's dialogue yet. The current UI and terminal responses still use deterministic dialogue planning.
