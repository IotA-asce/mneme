# Mirrors android_brain_memory.models.Fact; object_value maps to object_json.
# Empty supersedes_fact_id means no supersession link.
std_msgs/Header header
string fact_id
string subject
string predicate
string object_json
float32 confidence
string source_type
string status
string[] tags
string[] supporting_episode_ids
string supersedes_fact_id
