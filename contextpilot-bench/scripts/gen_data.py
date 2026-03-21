#!/usr/bin/env python3
import os
import sys
from pathlib import Path

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")

def _gen_contract(
    template,
    contract_id,
    party_a,
    party_b,
    amount,
    service_type,
    start_date,
    end_date,
    specific_terms,
    payment_schedule,
):
    body = template.format(
        service_type=service_type,
        start_date=start_date,
        end_date=end_date,
        amount=amount,
        payment_schedule=payment_schedule,
        specific_terms=specific_terms,
    )
    header = (
        f"SOFTWARE SERVICE AGREEMENT\nContract ID: {contract_id}\nDate: {start_date}\n\n"
        f"PARTIES:\nParty A (Client): {party_a}\nParty B (Provider): {party_b}\n\n"
    )
    footer = (
        f"\n\nSIGNATURES:\n\nParty A: {party_a}\nAuthorized Representative: ____________________\n"
        f"Date: {start_date}\n\nParty B: {party_b}\nAuthorized Representative: ____________________\n"
        f"Date: {start_date}\n"
    )
    return header + body + footer

def generate_workspace_data():
    base_dir = Path(__file__).parent.parent
    tmpl_path = base_dir / "data" / "contract_template.txt"
    if not tmpl_path.exists():
        print(f"Error: Template not found at {tmpl_path}")
        sys.exit(1)
    
    template = tmpl_path.read_text()
    
    ws = Path(WORKSPACE) / "contracts"
    ws.mkdir(parents=True, exist_ok=True)

    contracts = [
        {
            "filename": "contract_alpha_cloud.txt",
            "id": "SA-2024-001",
            "party_a": "TechVentures Pte Ltd",
            "party_b": "CloudNine Solutions Inc",
            "amount": "USD 2,400,000",
            "service_type": "cloud infrastructure and platform engineering",
            "start": "2024-01-15",
            "end": "2026-01-14",
            "payment": (
                "4.2 Payment shall be made in monthly installments of USD 100,000 each, "
                "payable on the first business day of each calendar month. An additional "
                "performance bonus of up to USD 200,000 shall be payable upon achievement "
                "of the milestones set forth in Schedule D."
            ),
            "specific": (
                "13.1 Cloud Infrastructure Requirements: Party B shall provide and maintain "
                "cloud infrastructure on AWS and Azure with guaranteed 99.95% uptime. All data "
                "shall be hosted in Singapore (ap-southeast-1) and Tokyo (ap-northeast-1) regions. "
                "Multi-region failover must be configured with RPO < 1 hour and RTO < 4 hours.\n\n"
                "13.2 Security Compliance: Party B shall maintain SOC 2 Type II certification and "
                "comply with MAS Technology Risk Management Guidelines (TRM). Annual penetration "
                "testing shall be conducted by an independent third party approved by Party A.\n\n"
                "13.3 Data Sovereignty: All customer data classified as 'restricted' or 'confidential' "
                "shall remain within Singapore jurisdiction at all times. Cross-border data transfers "
                "require explicit written approval from Party A's Data Protection Officer.\n\n"
                "13.4 Disaster Recovery: Party B shall maintain a comprehensive disaster recovery plan "
                "with quarterly testing. Recovery drills must demonstrate successful failover within "
                "the agreed RTO/RPO targets. Results shall be reported to Party A within five (5) "
                "business days of each test."
            ),
        },
        {
            "filename": "contract_beta_ai.txt",
            "id": "SA-2024-002",
            "party_a": "TechVentures Pte Ltd",
            "party_b": "DeepMind Analytics Ltd",
            "amount": "USD 3,600,000",
            "service_type": "artificial intelligence and machine learning platform",
            "start": "2024-03-01",
            "end": "2027-02-28",
            "payment": (
                "4.2 Payment shall be made in quarterly installments of USD 300,000 each, "
                "payable within fifteen (15) business days of the start of each quarter. "
                "Model performance bonuses of up to USD 150,000 per quarter shall be payable "
                "upon achieving accuracy targets defined in Schedule E."
            ),
            "specific": (
                "13.1 AI Model Requirements: Party B shall develop and deploy machine learning models "
                "meeting the performance benchmarks specified in Schedule E. All models must achieve "
                "minimum accuracy of 95% on test datasets and maintain F1 score above 0.92 in production.\n\n"
                "13.2 Model Governance: All AI models shall include bias detection and fairness monitoring. "
                "Party B shall provide model explainability reports using SHAP or LIME for all "
                "customer-facing predictions. Model drift monitoring shall be continuous with alerts "
                "triggered when performance degrades by more than 5% from baseline.\n\n"
                "13.3 Training Data: Party B shall maintain complete lineage and provenance records "
                "for all training data. No publicly sourced data shall be used without Party A's "
                "explicit written approval. All training datasets must be reviewed for PII and "
                "sensitive information before use.\n\n"
                "13.4 Compute Resources: Party B shall utilize GPU clusters with minimum NVIDIA A100 "
                "or equivalent for training workloads. Training infrastructure must support distributed "
                "training across at least 8 nodes. Party B shall provide detailed compute cost reports "
                "monthly and optimize resource utilization to maintain costs within 110% of budget.\n\n"
                "13.5 Model Versioning: All models shall be version-controlled with complete reproducibility. "
                "Party B shall maintain at minimum the current production model and two prior versions "
                "available for rollback at all times."
            ),
        },
        {
            "filename": "contract_gamma_security.txt",
            "id": "SA-2024-003",
            "party_a": "TechVentures Pte Ltd",
            "party_b": "CyberShield Pte Ltd",
            "amount": "USD 1,800,000",
            "service_type": "cybersecurity operations and threat management",
            "start": "2024-06-01",
            "end": "2026-05-31",
            "payment": (
                "4.2 Payment shall be made in monthly installments of USD 75,000 each, "
                "payable on the fifteenth (15th) business day of each calendar month. "
                "Incident response fees for Severity 1 incidents exceeding the included "
                "allocation shall be billed at USD 5,000 per incident."
            ),
            "specific": (
                "13.1 Security Operations Center: Party B shall operate a 24/7/365 Security "
                "Operations Center (SOC) with Level 1, Level 2, and Level 3 analysts. Minimum "
                "staffing levels shall be maintained as specified in Schedule F. All SOC analysts "
                "shall hold CISSP, CEH, or equivalent certifications.\n\n"
                "13.2 Incident Response: Party B shall respond to Severity 1 incidents within "
                "fifteen (15) minutes, Severity 2 within one (1) hour, and Severity 3 within "
                "four (4) hours. Incident response procedures shall follow NIST SP 800-61 guidelines. "
                "Post-incident reports shall be delivered within forty-eight (48) hours.\n\n"
                "13.3 Threat Intelligence: Party B shall provide continuous threat intelligence feeds "
                "covering emerging vulnerabilities, zero-day exploits, and industry-specific threats. "
                "Weekly threat briefings shall be provided to Party A's security team.\n\n"
                "13.4 Vulnerability Management: Party B shall conduct monthly vulnerability assessments "
                "and quarterly penetration testing. Critical vulnerabilities (CVSS >= 9.0) must be "
                "remediated within 24 hours. High vulnerabilities (CVSS 7.0-8.9) within 72 hours.\n\n"
                "13.5 Compliance Monitoring: Party B shall continuously monitor compliance with "
                "ISO 27001, SOC 2, PCI-DSS, and MAS TRM requirements as applicable to Party A's "
                "infrastructure and applications."
            ),
        },
        {
            "filename": "contract_delta_data.txt",
            "id": "SA-2024-004",
            "party_a": "TechVentures Pte Ltd",
            "party_b": "DataStream Technologies Pte Ltd",
            "amount": "USD 2,100,000",
            "service_type": "data engineering and analytics platform",
            "start": "2024-04-15",
            "end": "2026-04-14",
            "payment": (
                "4.2 Payment shall be made in bi-monthly installments of USD 175,000 each, "
                "payable within ten (10) business days of each billing period. A data quality "
                "bonus of up to USD 50,000 per quarter shall be payable when data pipeline "
                "SLAs exceed 99.9% availability."
            ),
            "specific": (
                "13.1 Data Pipeline Requirements: Party B shall design, build, and maintain real-time "
                "and batch data pipelines processing minimum 500 million events per day with end-to-end "
                "latency not exceeding 5 seconds for real-time streams and 30 minutes for batch.\n\n"
                "13.2 Data Quality: Party B shall implement comprehensive data quality checks including "
                "schema validation, completeness checks, consistency rules, and anomaly detection. Data "
                "quality scores must maintain 99.5% accuracy as measured by agreed-upon metrics.\n\n"
                "13.3 Data Lakehouse Architecture: Party B shall implement a medallion architecture "
                "(Bronze/Silver/Gold layers) using Apache Spark and Delta Lake. The platform must "
                "support both structured and unstructured data with unified governance.\n\n"
                "13.4 Analytics and Reporting: Party B shall provide self-service analytics capabilities "
                "using Apache Superset or equivalent tools. Pre-built dashboards for key business metrics "
                "shall be delivered within thirty (30) days of contract commencement.\n\n"
                "13.5 Data Retention: All raw data shall be retained for a minimum of seven (7) years "
                "in compliance with regulatory requirements. Party B shall implement automated data "
                "lifecycle management with tiered storage (hot/warm/cold) to optimize costs."
            ),
        },
    ]

    print(f"Generating contracts in {ws}...")
    for c in contracts:
        content = _gen_contract(
            template,
            c["id"],
            c["party_a"],
            c["party_b"],
            c["amount"],
            c["service_type"],
            c["start"],
            c["end"],
            c["specific"],
            c["payment"],
        )
        (ws / c["filename"]).write_text(content)

    total = 0
    for f in sorted(ws.iterdir()):
        if f.suffix == ".txt":
            sz = f.stat().st_size
            total += sz
            print(f"  {f.name}: {sz:,} bytes")
    print(f"  TOTAL: {total:,} bytes")

if __name__ == "__main__":
    generate_workspace_data()
