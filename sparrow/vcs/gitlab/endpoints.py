
ENDPOINTS = {
    "projects" : 
    {
        "base": "/projects",
        "filter_membership": "/projects?membership=true",
        "merge_requests": {
            "base": "/projects/{project_id}/merge_requests",
            "filter_iid": "/projects/{project_id}/merge_requests/{mr_iid}",
            "diffs": "/projects/{project_id}/merge_requests/{mr_iid}/diffs",
            "notes": {
                "base": "/projects/{project_id}/merge_requests/{mr_iid}/notes", # supports POST and GET
                "filter_id": "/projects/{project_id}/merge_requests/{mr_iid}/notes/{note_id}",
                "react_emoji": "/projects/{project_id}/merge_requests/{mr_iid}/notes/{note_id}/award_emoji" ## supports post
            }
        },
        "statuses": {
            "base": "/projects/{project_id}/respository/commits/{sha}/statuses",
            "update": "/projects/{project_id}/statuses/{sha}"
        },
        "pipelines": {
            "latest": "/projects/{project_id}/pipelines/latest?ref={ref}"
        }
    },
}
