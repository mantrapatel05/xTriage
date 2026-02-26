def route_bug(bug):
    text = (
        bug.get('title', '') + ' ' + bug.get('description', '') + ' ' +
        ' '.join(bug.get('comments', []))
    ).lower()

    if any(keyword in text for keyword in ['crash', 'data loss', 'security', 'vulnerability', 'urgent']):
        return "Core"
    if any(keyword in text for keyword in ['slow', 'performance', 'ui', 'usability']):
        return "Frontend"
    if any(keyword in text for keyword in ['minor', 'enhancement', 'feature request']):
        return "Backend"
    if any(keyword in text for keyword in ['typo', 'documentation', 'suggestion']):
        return "Documentation"
    if any(keyword in text for keyword in ['sql', 'database', 'query']):
        return "Database"
    
    return "Uncategorized"