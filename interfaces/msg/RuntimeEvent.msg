# Mirrors android_brain_memory.runtime.RuntimeEvent; payload maps to payload_json.
# timestamp and ttl_ms are milliseconds; expires_at is derived (timestamp + ttl_ms)
# and intentionally not transmitted. Zero ttl_ms/sequence/confidence mean "unset".
std_msgs/Header header
string event_id
string kind
string topic
int64 timestamp
string source
float32 confidence
int64 ttl_ms
int64 sequence
string payload_json
