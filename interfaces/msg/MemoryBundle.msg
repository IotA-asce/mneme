# Mirrors android_brain_memory.models.MemoryBundle; ranking_explanations maps to
# ranking_explanations_json (a JSON array of per-item explanation objects).
std_msgs/Header header
string query_id
string summary
android_brain_interfaces/Fact[] facts
android_brain_interfaces/Episode[] episodes
android_brain_interfaces/MemorySummary[] summaries
string[] warnings
string ranking_explanations_json
string provenance_summary
