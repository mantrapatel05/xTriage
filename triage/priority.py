def classify_priority(bug):
    text = (
        bug.get('title', '') + ' ' + bug.get('description', '') + ' ' +
        ' '.join(bug.get('comments', []))
    ).lower()

    reasons = []       
    confidence = 0.0    

    high_keywords = ['crash', 'data loss', 'jwt', 'security', 'vulnerability', 'urgent', '500', 'critical', 'blocker']
    medium_keywords = ['slow', 'performance', 'ui', 'usability', 'minor', 'enhancement', 'feature request', 'ux']
    low_keywords = ['typo', 'documentation', 'suggestion', 'low priority', 'wishlist', 'cosmetic']

    if any(keyword in text for keyword in high_keywords):
        reasons.append('Contains high-priority keywords')
        confidence += 0.9
        return "High", reasons, confidence

    if any(keyword in text for keyword in medium_keywords):
        reasons.append('Contains medium-priority keywords')
        confidence += 0.6
        return "Medium", reasons, confidence

    if any(keyword in text for keyword in low_keywords):
        reasons.append('Contains low-priority keywords')
        confidence += 0.4
        return "Low", reasons, confidence

    reasons.append('No specific priority keywords found')
    confidence += 0.1
    return "Very low", reasons, confidence