# Mirrors android_brain_memory.models.MemoryQuery.
# Empty strings disable text filters; empty fact_source_type/fact_status mean "no filter".
std_msgs/Header header
string query_text
string requester
string query_type
string[] entities
string[] tags
string fact_subject
string fact_predicate
string fact_object_text
string fact_source_type
string fact_status
uint32 max_results
bool include_episodes
bool include_facts
bool include_summaries
bool trusted_internal
bool include_internal
