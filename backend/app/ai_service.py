import ipaddress
import re

from app.time_utils import utc_isoformat, utc_now_naive


_IOC_PATTERNS = (
    ("SHA-256 hash", re.compile(r"(?i)\b[a-f0-9]{64}\b")),
    ("SHA-1 hash", re.compile(r"(?i)\b[a-f0-9]{40}\b")),
    ("MD5 hash", re.compile(r"(?i)\b[a-f0-9]{32}\b")),
    ("URL", re.compile(r"(?i)\bhttps?://[^\s<>\"']+")),
    ("IPv4 address", re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")),
    (
        "Domain",
        re.compile(
            r"(?i)\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
            r"(?:com|net|org|io|co|ru|cn|info|biz|dev|app|xyz|example)\b"
        ),
    ),
)

_RULES = (
    {
        "classification": "Data Exfiltration",
        "severity": "Critical",
        "patterns": (
            r"\bdata exfiltration\b",
            r"\b(?:data|files?) (?:was |were )?(?:staged|exfiltrated|leaked|transferred out)\b",
            r"\bunauthorized data transfer\b",
            r"\b(?:large|unusual) outbound transfer\b",
        ),
        "activity": "Possible unauthorized outbound data transfer or data staging was reported.",
        "action": "Preserve network and access logs, identify affected data, and contain suspicious outbound transfers.",
    },
    {
        "classification": "Ransomware Activity",
        "severity": "Critical",
        "patterns": (
            r"\bransomware\b",
            r"\bfiles? (?:were |being )?encrypt(?:ed|ing|ion)\b",
            r"\bransom note\b",
        ),
        "activity": "Ransomware or file-encryption activity was reported.",
        "action": "Isolate affected systems using established procedures and preserve forensic evidence before recovery.",
    },
    {
        "classification": "SQL Injection",
        "severity": "High",
        "patterns": (
            r"\bsql injection\b",
            r"\bunion\s+select\b",
            r"\b(?:or|and)\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+",
            r"\bselect\b.{0,80}\bfrom\b.{0,80}(?:--|/\*|;\s*drop\b)",
        ),
        "activity": "SQL-injection-like input or database query manipulation was found.",
        "action": "Preserve the request and application logs, check database access for successful exploitation, and validate parameterized query handling.",
    },
    {
        "classification": "Malware Activity",
        "severity": "High",
        "patterns": (
            r"\bmalware\b",
            r"\btrojan\b",
            r"\b(?:virus|worm)\b",
            r"\bmalicious (?:file|process|payload)\b",
            r"\bcommand[- ]and[- ]control\b",
        ),
        "activity": "Malware, a malicious process, or command-and-control activity was reported.",
        "action": "Quarantine identified files and investigate affected endpoints for persistence and lateral movement.",
    },
    {
        "classification": "Unauthorized Access",
        "severity": "High",
        "patterns": (
            r"\bunauthorized access\b",
            r"\baccount compromised\b",
            r"\bprivilege escalation\b",
            r"\baccessed without authorization\b",
            r"\bunauthorized login\b",
        ),
        "activity": "Unauthorized account access or privilege escalation was reported.",
        "action": "Validate the account activity, revoke suspicious sessions, and restrict compromised credentials as appropriate.",
    },
    {
        "classification": "Brute-Force / Credential Attack",
        "severity": "High",
        "patterns": (
            r"\bbrute[\s-]?force\b",
            r"\bcredential stuffing\b",
            r"\bpassword spraying\b",
            r"\brepeated failed (?:login|logon|authentication)",
            r"\b\d+\s+(?:failed|unsuccessful) (?:login|logon|authentication) attempts?\b",
        ),
        "activity": "Repeated authentication failures or automated credential-guessing activity was reported.",
        "action": "Review authentication logs, apply rate limits or account protections, and verify whether any attempts succeeded.",
    },
    {
        "classification": "Phishing",
        "severity": "High",
        "patterns": (
            r"\bphishing\b",
            r"\bspear[\s-]?phishing\b",
            r"\bcredential harvesting\b",
            r"\bsuspicious (?:email|attachment|link)\b",
        ),
        "activity": "A phishing message, suspicious link, or attachment was reported.",
        "action": "Remove the message from affected mailboxes, block confirmed malicious indicators, and check for link or attachment execution.",
    },
    {
        "classification": "Port Scanning",
        "severity": "Medium",
        "patterns": (
            r"\bport scan(?:ning)?\b",
            r"\b(?:tcp|udp) scan\b",
            r"\bscanned (?:\d+ )?ports?\b",
            r"\b(?:syn|connect) scan\b",
        ),
        "activity": "Network reconnaissance or port-scanning behavior was reported.",
        "action": "Review firewall and flow logs, identify the scanning source and target range, and confirm whether exposed services were accessed.",
    },
    {
        "classification": "Suspicious Login",
        "severity": "Medium",
        "patterns": (
            r"\bsuspicious login\b",
            r"\bunusual login\b",
            r"\blogin from (?:an? )?(?:unknown|unusual|new) (?:ip|location|device|host)\b",
            r"\bimpossible travel\b",
            r"\bauthentication from (?:an? )?unknown (?:ip|location|device)\b",
        ),
        "activity": "A login from an unusual location, device, or context was reported.",
        "action": "Verify the login with the account owner and correlate its source, device, and session with authentication records.",
    },
)

_SEVERITY_RANK = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
_SUCCESSFUL_EXPLOITATION = re.compile(
    r"\b(?:successful(?:ly)? (?:login|logon|access|exploit(?:ation)?)|"
    r"exploit(?:ed|ation)? succeeded|account compromised|data exfiltrat(?:ed|ion)|"
    r"database dump|privilege escalation confirmed)\b",
    re.IGNORECASE,
)


def _extract_iocs(text: str) -> list[str]:
    indicators: list[str] = []
    seen: set[str] = set()
    for label, pattern in _IOC_PATTERNS:
        for match in pattern.findall(text):
            value = match.rstrip(".,;:)")
            if label == "IPv4 address":
                try:
                    ipaddress.IPv4Address(value)
                except ipaddress.AddressValueError:
                    continue
            key = value.lower()
            if key not in seen:
                indicators.append(f"{label}: {value}")
                seen.add(key)
    return indicators


def _matched_evidence(text: str, patterns: tuple[str, ...]) -> list[str]:
    matched = []
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            excerpt = re.sub(r"\s+", " ", match.group(0)).strip()
            if excerpt not in matched:
                matched.append(excerpt)
    return matched


def analyze_incident(description: str, log_text: str | None = None) -> dict:
    description = description.strip()
    log_text = (log_text or "").strip()
    evidence = f"{description}\n{log_text}".strip()
    matched_rules = []
    for rule in _RULES:
        matches = _matched_evidence(evidence, rule["patterns"])
        if matches:
            matched_rules.append((rule, matches))

    successful_exploitation = bool(_SUCCESSFUL_EXPLOITATION.search(evidence))
    if matched_rules:
        primary_rule, _ = max(
            matched_rules,
            key=lambda matched: _SEVERITY_RANK[matched[0]["severity"]],
        )
        severity = primary_rule["severity"]
        if successful_exploitation and severity != "Critical":
            severity = "Critical"

        classification = primary_rule["classification"]
        if len(matched_rules) > 1:
            classification = "Multiple Threat Indicators"
        activities = [
            f"{rule['activity']} Matched evidence: {', '.join(matches)}."
            for rule, matches in matched_rules
        ]
        actions = list(dict.fromkeys(rule["action"] for rule, _ in matched_rules))
        rationale_parts = [
            f"{rule['classification']} matched: {', '.join(matches)}"
            for rule, matches in matched_rules
        ]
        rationale = (
            f"Rule-based analysis identified {'; '.join(rationale_parts)}. "
            f"The highest matched baseline risk is {primary_rule['severity']}."
        )
        if successful_exploitation:
            rationale += " Evidence of successful access or impact raises the suggested risk to Critical."
    else:
        classification = "Unclassified Security Event"
        severity = "Low"
        activities = ["No supported threat pattern was recognized in the submitted text."]
        actions = [
            "Review the affected asset and time window, then add relevant authentication, endpoint, or network telemetry for further triage."
        ]
        rationale = (
            "The supplied description and log excerpt did not match the local detection rules. "
            "This is not proof that the activity is benign; an analyst should review the original evidence."
        )

    iocs = _extract_iocs(evidence)
    if iocs:
        activities.append(f"Potential indicators were present in the submitted evidence ({len(iocs)} unique indicator(s)).")
    else:
        iocs = ["No IP address, domain, URL, or file hash detected in the supplied text."]

    summary = (
        f"Local rule-based triage classified this event as {classification} with {severity} suggested severity. "
        f"{activities[0]}"
    )
    return {
        "provider": "Demo AI",
        "classification": classification,
        "suggested_severity": severity,
        "executive_summary": summary,
        "suspicious_activity": activities,
        "indicators_of_compromise": iocs,
        "potential_impact": (
            "Potential account, endpoint, application, network, or data impact depends on whether the reported activity "
            "is confirmed and whether access, exploitation, or execution succeeded."
        ),
        "affected_systems": [],
        "investigation_steps": [],
        "containment_recommendations": actions,
        "remediation_suggestions": [],
        "monitoring_recommendations": [],
        "rationale": rationale,
        "timestamp": utc_isoformat(utc_now_naive()),
    }
