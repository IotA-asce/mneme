# Mirrors android_brain_memory.models.Episode; context maps to context_json.
std_msgs/Header header
string episode_id
builtin_interfaces/Time start_time
builtin_interfaces/Time end_time
string summary
string context_json
float32 salience
float32 confidence
string[] participants
string[] objects
string[] provenance_refs
