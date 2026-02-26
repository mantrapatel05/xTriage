def summarize_issue(bug):
    title = bug.get("title", "No Title").strip()
    description = bug.get("description", "").strip()
    comments = [comment.strip() for comment in bug.get("comments", []) if comment.strip()]

    summary = f"Title: {title}\nDescription: {description}\nComments: {'; '.join(comments)}"

    return summary
