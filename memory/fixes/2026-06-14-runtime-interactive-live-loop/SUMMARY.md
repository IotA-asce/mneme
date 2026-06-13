# Runtime Interactive and Live Loop Fix

Type: Fix  
Date: 2026-06-14  
Status: Complete

Fixed `mneme run` terminal behavior so typed interactive mode prints Mneme responses immediately instead of appearing stuck until exit. Added explicit live ticking flags for perception-driven runs that should poll configured speech/vision workers without blocking on keyboard input.

