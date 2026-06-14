# Live Local Lab Diagnostics

Type: Fix  
Date: 2026-06-14  
Status: Complete

Mneme now handles local-lab MediaPipe and model-verification setup failures without crashing or giving invalid instructions. Camera frames continue flowing when optional face detection is unavailable, live status explains the missing detector/model state, and `mneme models verify --profile ...` supports profile-scoped troubleshooting.

