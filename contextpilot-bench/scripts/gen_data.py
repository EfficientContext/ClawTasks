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

    print(f"Generating workspace in {ws}...")
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

    _gen_amendments(ws, contracts, template)
    _gen_msa(ws)
    _gen_vendor_assessments(ws, contracts)
    _gen_policies(ws)
    _gen_board_minutes(ws, contracts)
    _gen_nda(ws, contracts)

    total = 0
    for f in sorted(ws.iterdir()):
        if f.is_file():
            sz = f.stat().st_size
            total += sz
            print(f"  {f.name}: {sz:,} bytes")
    print(f"  TOTAL: {total:,} bytes ({total // 1024} KB)")


def _gen_amendments(ws, contracts, template):
    for c in contracts:
        vendor = c["party_b"]
        cid = c["id"]
        amendment = f"""FIRST AMENDMENT TO SOFTWARE SERVICE AGREEMENT
Amendment ID: {cid}-A1
Original Contract: {cid}
Date: 2025-01-15

PARTIES:
Party A (Client): TechVentures Pte Ltd
Party B (Provider): {vendor}

RECITALS

WHEREAS, Party A and Party B entered into a Software Service Agreement dated {c["start"]} (the "Original Agreement"), Contract ID {cid};

WHEREAS, the parties desire to amend certain terms of the Original Agreement as set forth herein;

NOW, THEREFORE, in consideration of the mutual covenants and agreements contained herein, and for other good and valuable consideration, the receipt and sufficiency of which are hereby acknowledged, the parties agree as follows:

ARTICLE 1 — AMENDMENTS

1.1 Amendment to Article 4 (Fees and Payment)

Section 4.1 of the Original Agreement is hereby amended to increase the total contract amount by fifteen percent (15%) to reflect expanded scope of services. The revised total contract amount shall be calculated as the original amount plus fifteen percent (15%), effective from the date of this Amendment.

All payment terms, schedules, and conditions set forth in Article 4 of the Original Agreement shall remain in full force and effect, except as specifically modified by this Amendment. The payment schedule shall be adjusted proportionally to reflect the increased contract amount.

1.2 Amendment to Article 2 (Scope of Services)

Section 2.1 of the Original Agreement is hereby amended to include the following additional services:

(a) Enhanced monitoring and alerting capabilities with real-time dashboards accessible to Party A's operations team twenty-four (24) hours a day, seven (7) days a week;

(b) Quarterly business review meetings with senior management representatives from both parties, including performance metrics, trend analysis, and strategic planning;

(c) Dedicated innovation lab sessions (minimum two (2) per quarter) to explore emerging technologies and their potential application to Party A's business requirements;

(d) Extended support hours from Business Hours (9:00 AM to 6:00 PM Singapore Time) to Extended Hours (7:00 AM to 10:00 PM Singapore Time) on Business Days, and on-call support during non-business hours for Severity 1 and Severity 2 issues.

1.3 Amendment to Article 3 (Term)

The Initial Term of the Original Agreement is hereby extended by twelve (12) months. The revised expiration date shall be twelve (12) months after the original expiration date specified in the Original Agreement. All other provisions of Article 3 shall remain unchanged.

1.4 Amendment to Schedule B (Service Level Agreement)

The SLA targets specified in Schedule B of the Original Agreement are hereby amended as follows:

(a) Availability Target: Increased from 99.9% to 99.95% uptime measured monthly;
(b) Severity 1 Response Time: Reduced from 15 minutes to 10 minutes;
(c) Severity 1 Resolution Time: Reduced from 4 hours to 2 hours;
(d) Service Credit Rate: Increased from 2% to 3% per 0.1% below the availability target;
(e) Maximum Service Credit Cap: Increased from 20% to 30% of monthly fees.

1.5 Addition of Article 17A — Sustainability Requirements

The following new article is hereby added to the Original Agreement:

17A.1 Party B shall implement and maintain environmentally sustainable practices in the delivery of Services, including energy-efficient infrastructure, carbon footprint tracking and reporting, and compliance with applicable environmental regulations.

17A.2 Party B shall provide quarterly sustainability reports to Party A, including energy consumption metrics, carbon emissions data, and progress toward agreed sustainability targets.

17A.3 Party B shall achieve carbon neutrality for all Services delivered under this Agreement by December 31, 2025, through a combination of renewable energy procurement, energy efficiency improvements, and verified carbon offset programs.

ARTICLE 2 — GENERAL

2.1 Except as specifically amended by this First Amendment, all terms and conditions of the Original Agreement shall remain in full force and effect and are hereby ratified and confirmed.

2.2 In the event of any conflict between the terms of this Amendment and the Original Agreement, the terms of this Amendment shall prevail.

2.3 This Amendment may be executed in counterparts, each of which shall be deemed an original, and all of which together shall constitute one and the same instrument.

2.4 Capitalized terms used but not defined in this Amendment shall have the meanings ascribed to them in the Original Agreement.

SIGNATURES:

Party A: TechVentures Pte Ltd
Authorized Representative: ____________________
Date: 2025-01-15

Party B: {vendor}
Authorized Representative: ____________________
Date: 2025-01-15
"""
        fname = (
            c["filename"].replace("contract_", "amendment_").replace(".txt", "_a1.txt")
        )
        (ws / fname).write_text(amendment)


def _gen_msa(ws):
    msa = """MASTER SERVICE AGREEMENT
Agreement ID: MSA-2023-001
Date: 2023-06-01

PARTIES:
Party A (Client): TechVentures Pte Ltd, a company incorporated under the laws of Singapore, with its registered office at 1 Raffles Place, #20-01, One Raffles Place Tower 2, Singapore 048616.

Party B: Any vendor or service provider that executes a Statement of Work or Service Agreement referencing this Master Service Agreement (each, a "Vendor" or "Service Provider").

RECITALS

WHEREAS, Party A engages multiple technology service providers for various aspects of its business operations, including but not limited to cloud infrastructure, artificial intelligence, cybersecurity, and data engineering;

WHEREAS, Party A desires to establish a unified framework of terms and conditions that shall apply to all service engagements with its technology vendors;

WHEREAS, individual Service Agreements executed between Party A and each Vendor shall incorporate the terms of this Master Service Agreement by reference;

NOW, THEREFORE, in consideration of the mutual covenants contained herein, Party A establishes the following Master Service Agreement:

ARTICLE 1 — APPLICABILITY

1.1 This Master Service Agreement ("MSA") establishes the general terms and conditions that apply to all technology service engagements between Party A and its Vendors. Each individual engagement shall be governed by a separate Service Agreement ("SA") that incorporates this MSA by reference.

1.2 In the event of any conflict between the terms of this MSA and an individual SA, the terms of the SA shall prevail to the extent of such conflict, unless the MSA provision is expressly stated to be non-waivable.

1.3 This MSA does not create any obligation on Party A to engage any particular Vendor or to procure any minimum volume of services.

ARTICLE 2 — VENDOR QUALIFICATION

2.1 All Vendors engaged by Party A must meet the following minimum qualification requirements:

(a) Minimum of five (5) years of experience in the relevant technology domain;
(b) Annual revenue of at least USD 10,000,000 or equivalent;
(c) Relevant industry certifications as specified in the applicable SA;
(d) Demonstrated financial stability, evidenced by audited financial statements for the most recent three (3) fiscal years;
(e) Satisfactory results from Party A's vendor due diligence process, including background checks, reference checks, and security assessments;
(f) Compliance with all applicable laws, regulations, and industry standards;
(g) Adequate insurance coverage as specified in Article 8 of this MSA.

2.2 Party A reserves the right to conduct periodic reassessments of Vendor qualifications during the term of any engagement. Failure to maintain the required qualifications may result in termination of the applicable SA.

ARTICLE 3 — GOVERNANCE

3.1 Each Vendor engagement shall be overseen by a governance structure consisting of:

(a) Executive Sponsor: A senior executive from each party with authority to make strategic decisions;
(b) Engagement Manager: A dedicated manager from each party responsible for day-to-day coordination;
(c) Technical Lead: A technical specialist from each party responsible for technical decisions and quality;
(d) Steering Committee: A joint committee meeting quarterly to review performance, address issues, and plan future work.

3.2 The Steering Committee shall:
(a) Review service performance against SLA targets;
(b) Review and approve change requests exceeding USD 50,000;
(c) Resolve escalated disputes;
(d) Review and update risk registers;
(e) Approve annual service improvement plans.

3.3 Party A shall maintain a centralized Vendor Management Office (VMO) responsible for:
(a) Monitoring compliance with this MSA across all Vendor engagements;
(b) Consolidating and analyzing performance metrics;
(c) Coordinating cross-vendor dependencies;
(d) Managing vendor risk assessments;
(e) Facilitating knowledge sharing across Vendor engagements.

ARTICLE 4 — STANDARD TERMS

4.1 Confidentiality: All Vendors shall be bound by confidentiality obligations consistent with Article 6 of each SA. The confidentiality obligations shall survive termination of any SA for a period of five (5) years, or for so long as the information remains a trade secret, whichever is longer.

4.2 Data Protection: All Vendors processing Personal Data on behalf of Party A shall comply with the data protection requirements set forth in Article 7 of each SA and shall execute a Data Processing Agreement in the form provided by Party A.

4.3 Intellectual Property: Unless otherwise specified in the applicable SA, all Intellectual Property created in the performance of Services shall be owned by Party A, consistent with Article 5 of each SA.

4.4 Insurance: All Vendors shall maintain the minimum insurance coverages specified in Article 15 of each SA throughout the term of their engagement and for two (2) years following termination.

4.5 Business Continuity: All Vendors shall maintain business continuity and disaster recovery plans consistent with Article 16 of each SA. Plans shall be tested at least semi-annually, and test results shall be shared with Party A.

4.6 Compliance: All Vendors shall comply with applicable laws, regulations, and industry standards, including but not limited to anti-corruption laws, export control regulations, sanctions requirements, and data protection laws.

ARTICLE 5 — SECURITY REQUIREMENTS

5.1 All Vendors shall comply with Party A's Information Security Policy (ISP-2024-001) and Data Governance Policy (DGP-2024-001), as amended from time to time.

5.2 Minimum security requirements for all Vendor engagements:

(a) Encryption: All data at rest shall be encrypted using AES-256 or equivalent. All data in transit shall be encrypted using TLS 1.2 or higher.

(b) Access Control: Role-based access control (RBAC) with the principle of least privilege. Multi-factor authentication (MFA) for all administrative and privileged access. Access reviews conducted at least quarterly.

(c) Monitoring: Continuous security monitoring with real-time alerting. Security event logs retained for a minimum of one (1) year. Integration with Party A's Security Information and Event Management (SIEM) system.

(d) Vulnerability Management: Monthly vulnerability scanning of all systems and applications. Quarterly penetration testing by an independent third party. Critical vulnerabilities (CVSS >= 9.0) remediated within 24 hours. High vulnerabilities (CVSS 7.0-8.9) remediated within 72 hours.

(e) Incident Response: Documented incident response procedures aligned with NIST SP 800-61. Security incidents reported to Party A within 24 hours. Post-incident reports delivered within 72 hours.

(f) Personnel Security: Background checks for all personnel with access to Party A's systems or data. Annual security awareness training. Confidentiality agreements signed by all personnel.

ARTICLE 6 — PERFORMANCE MANAGEMENT

6.1 All Vendors shall report performance metrics monthly, including:
(a) SLA compliance rates;
(b) Incident counts by severity;
(c) Change request status;
(d) Resource utilization;
(e) Customer satisfaction scores;
(f) Risk register updates.

6.2 Party A shall conduct formal performance reviews:
(a) Monthly: Operational review with Engagement Managers;
(b) Quarterly: Strategic review with Executive Sponsors;
(c) Annually: Comprehensive assessment including benchmarking against industry standards.

6.3 Performance scores below the minimum acceptable threshold (as defined in each SA) for two (2) consecutive quarters shall trigger a Performance Improvement Plan (PIP). Failure to achieve the required improvement within the PIP period may result in termination of the SA for cause.

ARTICLE 7 — FINANCIAL MANAGEMENT

7.1 All invoices shall comply with Party A's accounts payable requirements:
(a) Itemized breakdown of services, hours, and expenses;
(b) Reference to the applicable SA and purchase order number;
(c) Supporting documentation for all expense claims;
(d) Submitted electronically through Party A's vendor portal.

7.2 Payment terms: Net 30 days from receipt of a compliant invoice, unless otherwise specified in the applicable SA.

7.3 Annual rate increases shall not exceed the lesser of: (a) three percent (3%); or (b) the Consumer Price Index (CPI) increase for the preceding twelve (12) months.

7.4 Party A reserves the right to conduct financial audits of any Vendor with thirty (30) days' prior written notice.

ARTICLE 8 — GENERAL PROVISIONS

8.1 This MSA shall be governed by and construed in accordance with the laws of the Republic of Singapore.

8.2 Disputes shall be resolved in accordance with the dispute resolution procedures set forth in the applicable SA.

8.3 This MSA may be amended by Party A with sixty (60) days' prior written notice to all Vendors. Vendors may terminate their SA within thirty (30) days of receiving notice of an MSA amendment that materially and adversely affects their rights or obligations.

8.4 This MSA shall remain in effect until terminated by Party A.

AUTHORIZED BY:

TechVentures Pte Ltd
Chief Technology Officer: ____________________
General Counsel: ____________________
Date: 2023-06-01
"""
    (ws / "master_service_agreement.txt").write_text(msa)


def _gen_vendor_assessments(ws, contracts):
    for c in contracts:
        vendor = c["party_b"]
        svc = c["service_type"]
        cid = c["id"]
        amt = c["amount"]
        short = c["filename"].replace("contract_", "").replace(".txt", "")

        assessment = f"""VENDOR ASSESSMENT REPORT
Report ID: VA-2024-{short.upper()}
Date: 2024-12-15
Prepared By: TechVentures Vendor Management Office
Subject: Annual Assessment of {vendor}

1. EXECUTIVE SUMMARY

This report presents the annual assessment of {vendor} (Contract {cid}) for {svc} services. The assessment covers the period from {c["start"]} to 2024-12-31 and evaluates performance across five dimensions: service delivery, security compliance, financial management, relationship management, and innovation.

Overall Rating: SATISFACTORY (3.6 / 5.0)

2. CONTRACT OVERVIEW

Vendor: {vendor}
Contract ID: {cid}
Service Type: {svc}
Contract Value: {amt}
Contract Period: {c["start"]} to {c["end"]}
Current Status: Active

3. SERVICE DELIVERY ASSESSMENT (Score: 3.8 / 5.0)

3.1 SLA Performance:
- Availability: 99.92% (Target: 99.9%) — MET
- Severity 1 Response Time: 12 min avg (Target: 15 min) — MET
- Severity 2 Response Time: 48 min avg (Target: 60 min) — MET
- Severity 1 Resolution Time: 3.5 hrs avg (Target: 4 hrs) — MET
- Change Request Turnaround: 8.5 days avg (Target: 10 days) — MET

3.2 Deliverable Quality:
- First-pass acceptance rate: 87% (Target: 90%) — BELOW TARGET
- Defect density: 2.3 per 1000 LOC (Target: <3.0) — MET
- Documentation completeness: 92% (Target: 95%) — BELOW TARGET

3.3 Areas for Improvement:
- First-pass acceptance rate needs improvement; primary issues are incomplete unit tests and missing edge case handling
- Documentation quality inconsistent across teams; recommend standardized templates

4. SECURITY COMPLIANCE ASSESSMENT (Score: 3.5 / 5.0)

4.1 Certifications:
- SOC 2 Type II: Valid (expires 2025-06-30)
- ISO 27001: Valid (expires 2025-09-15)
- PCI-DSS: Not applicable / Not required

4.2 Security Audit Results:
- Last penetration test: 2024-09-15 (by CyberDefense Associates)
- Critical findings: 0
- High findings: 2 (both remediated within SLA)
- Medium findings: 5 (3 remediated, 2 in progress)
- Low findings: 12 (8 remediated, 4 accepted)

4.3 Incident History:
- Total security incidents: 3
- Severity 1: 0
- Severity 2: 1 (unauthorized access attempt, detected and blocked)
- Severity 3: 2 (minor policy violations, corrected)

4.4 Data Protection:
- DPA executed: Yes
- Data breach incidents: 0
- Cross-border data transfers: Compliant with PDPA requirements
- Data retention compliance: Verified

5. FINANCIAL MANAGEMENT ASSESSMENT (Score: 3.7 / 5.0)

5.1 Budget Performance:
- Contract value: {amt}
- Actual spend to date: Within 5% of budget
- Change orders: 3 (total value: USD 150,000)
- Service credits issued: USD 12,500 (Q2 availability dip)

5.2 Invoice Compliance:
- On-time invoice submission: 95%
- Invoice accuracy: 92%
- Disputed invoices: 2 (both resolved)

6. RELATIONSHIP MANAGEMENT ASSESSMENT (Score: 3.4 / 5.0)

6.1 Communication:
- Monthly reports: Delivered on time (11/12 months)
- Quarterly business reviews: All conducted as scheduled
- Escalation response: Generally within SLA, one instance of delayed response

6.2 Personnel:
- Key personnel retention: 80% (1 account manager change in Q3)
- Personnel qualification compliance: 100%
- Knowledge transfer readiness: Adequate

7. INNOVATION ASSESSMENT (Score: 3.6 / 5.0)

7.1 Technology Adoption:
- Proactive technology recommendations: 4 proposals submitted
- Proposals accepted: 2
- Innovation lab sessions conducted: 3 (target: 4)

8. RECOMMENDATIONS

8.1 Renew contract with the following conditions:
- Increase first-pass acceptance rate target to 92%
- Require quarterly documentation quality audits
- Add sustainability reporting requirements per Amendment A1
- Maintain current pricing with CPI adjustment

8.2 Risk Items to Monitor:
- Key personnel retention (account manager transition)
- Medium security findings remediation timeline
- Documentation quality consistency

Report Approved By:
VP of Technology: ____________________
Head of Vendor Management: ____________________
Date: 2024-12-15
"""
        fname = f"vendor_assessment_{short}.txt"
        (ws / fname).write_text(assessment)


def _gen_policies(ws):
    security_policy = """INFORMATION SECURITY POLICY
Policy ID: ISP-2024-001
Version: 3.2
Effective Date: 2024-01-01
Review Date: 2025-01-01
Owner: Chief Information Security Officer
Classification: INTERNAL — RESTRICTED

1. PURPOSE AND SCOPE

1.1 This Information Security Policy ("Policy") establishes the principles, standards, and requirements for protecting TechVentures Pte Ltd's information assets against unauthorized access, disclosure, modification, destruction, or disruption.

1.2 This Policy applies to all employees, contractors, consultants, temporary workers, and other personnel ("Users") who access, process, store, or transmit TechVentures information, regardless of location or device used.

1.3 This Policy also applies to all third-party service providers and vendors who process, store, or have access to TechVentures information, as referenced in the Master Service Agreement (MSA-2023-001) and individual Service Agreements.

2. INFORMATION CLASSIFICATION

2.1 All information assets shall be classified into one of the following categories:

(a) PUBLIC: Information intended for public disclosure. No restrictions on access or distribution.

(b) INTERNAL: Information intended for internal use only. Access limited to TechVentures employees and authorized contractors.

(c) CONFIDENTIAL: Sensitive business information. Access restricted to authorized personnel with a legitimate business need. Examples: financial reports, business plans, customer lists, vendor contracts, employee records.

(d) RESTRICTED: Highly sensitive information. Access strictly limited to named individuals. Examples: encryption keys, authentication credentials, personally identifiable information (PII), trade secrets, board meeting minutes, M&A documents.

2.2 Information owners are responsible for classifying their information assets and ensuring appropriate controls are applied.

2.3 When information assets of different classifications are combined, the combined asset shall be classified at the highest classification level of any component.

3. ACCESS CONTROL

3.1 Access to information systems and data shall be granted based on the principle of least privilege: Users shall be granted only the minimum access rights necessary to perform their job functions.

3.2 All access shall be role-based (RBAC). Roles shall be defined, documented, and reviewed at least quarterly by the information owner and the Security team.

3.3 Multi-factor authentication (MFA) is mandatory for:
(a) All remote access to internal systems;
(b) All access to CONFIDENTIAL and RESTRICTED information;
(c) All privileged or administrative accounts;
(d) All access to production environments;
(e) All VPN connections.

3.4 Password requirements:
(a) Minimum length: 14 characters;
(b) Complexity: Must include uppercase, lowercase, numbers, and special characters;
(c) Rotation: Every 90 days for standard accounts, every 60 days for privileged accounts;
(d) History: Cannot reuse the last 12 passwords;
(e) Lockout: Account locked after 5 consecutive failed attempts for 30 minutes.

3.5 Access reviews shall be conducted:
(a) Quarterly for all system access;
(b) Monthly for privileged access;
(c) Upon role change, transfer, or termination;
(d) Annually as part of the comprehensive security audit.

4. DATA PROTECTION

4.1 Encryption Requirements:
(a) Data at rest: AES-256 or equivalent for CONFIDENTIAL and RESTRICTED data;
(b) Data in transit: TLS 1.2 or higher for all internal and external communications;
(c) Key management: Centralized key management system with separation of duties;
(d) Key rotation: Annual for data encryption keys, quarterly for session keys.

4.2 Data Loss Prevention (DLP):
(a) DLP controls shall be implemented on all endpoints, email systems, and cloud services;
(b) Automatic blocking of RESTRICTED data transmission via unauthorized channels;
(c) Monitoring and alerting for CONFIDENTIAL data transmission;
(d) Regular DLP policy review and tuning.

4.3 Data Retention and Disposal:
(a) Retention periods as defined in the Data Retention Schedule;
(b) Secure disposal: NIST SP 800-88 compliant media sanitization;
(c) Certificate of destruction required for physical media;
(d) Automated data lifecycle management for digital assets.

5. NETWORK SECURITY

5.1 Network Segmentation:
(a) Production, development, and corporate networks shall be physically or logically separated;
(b) DMZ for all internet-facing services;
(c) Micro-segmentation for sensitive workloads;
(d) Zero-trust network architecture for all new deployments.

5.2 Firewall and IDS/IPS:
(a) Next-generation firewalls at all network perimeters;
(b) Intrusion detection/prevention systems on all critical network segments;
(c) Regular rule review and optimization (quarterly);
(d) Firewall changes require change management approval.

5.3 Wireless Security:
(a) WPA3-Enterprise for all corporate wireless networks;
(b) Guest networks isolated from corporate network;
(c) Rogue access point detection and prevention;
(d) Regular wireless security assessments.

6. INCIDENT RESPONSE

6.1 All security incidents shall be reported immediately to the Security Operations Center (SOC) via the incident reporting system or emergency hotline.

6.2 Incident severity classification:
(a) Severity 1 (Critical): Active data breach, ransomware, compromise of RESTRICTED systems. Response: Immediate (within 15 minutes).
(b) Severity 2 (High): Detected intrusion attempt, malware on production systems, unauthorized access to CONFIDENTIAL data. Response: Within 1 hour.
(c) Severity 3 (Medium): Policy violation, suspicious activity, failed security controls. Response: Within 4 hours.
(d) Severity 4 (Low): Minor policy deviation, security awareness issue. Response: Within 1 business day.

6.3 Post-incident activities:
(a) Root cause analysis within 5 business days;
(b) Lessons learned review within 10 business days;
(c) Corrective actions tracked to completion;
(d) Regulatory notifications as required by applicable law.

7. VENDOR SECURITY

7.1 All vendors shall comply with this Policy as referenced in the Master Service Agreement (MSA-2023-001).

7.2 Vendor security assessments shall be conducted:
(a) Prior to engagement (due diligence);
(b) Annually during the engagement;
(c) Upon any significant change in the vendor's security posture;
(d) Upon any security incident involving the vendor.

7.3 Vendors processing RESTRICTED data must maintain SOC 2 Type II certification or equivalent.

8. COMPLIANCE AND ENFORCEMENT

8.1 Compliance with this Policy is mandatory for all Users. Non-compliance may result in disciplinary action, up to and including termination of employment or contract.

8.2 This Policy shall be reviewed and updated at least annually by the Chief Information Security Officer.

8.3 Exceptions to this Policy must be approved in writing by the CISO and documented in the exception register.

APPROVED BY:
Chief Information Security Officer: ____________________
Chief Technology Officer: ____________________
Date: 2024-01-01
"""

    data_governance = """DATA GOVERNANCE POLICY
Policy ID: DGP-2024-001
Version: 2.1
Effective Date: 2024-01-01
Review Date: 2025-01-01
Owner: Chief Data Officer
Classification: INTERNAL — CONFIDENTIAL

1. PURPOSE AND SCOPE

1.1 This Data Governance Policy ("Policy") establishes the framework for managing TechVentures Pte Ltd's data assets throughout their lifecycle, ensuring data quality, security, privacy, and compliance with applicable regulations.

1.2 This Policy applies to all structured and unstructured data created, collected, processed, stored, or transmitted by or on behalf of TechVentures, regardless of format, medium, or location.

1.3 This Policy complements the Information Security Policy (ISP-2024-001) and applies to all employees, contractors, and third-party service providers as referenced in the Master Service Agreement (MSA-2023-001).

2. DATA GOVERNANCE FRAMEWORK

2.1 Roles and Responsibilities:

(a) Chief Data Officer (CDO): Overall accountability for data governance strategy, policy, and compliance. Chairs the Data Governance Council.

(b) Data Governance Council: Cross-functional committee comprising the CDO, CISO, General Counsel, and business unit data stewards. Meets monthly to review data governance matters.

(c) Data Stewards: Business unit representatives responsible for data quality, classification, and usage within their domain. Each business unit shall designate at least one Data Steward.

(d) Data Custodians: IT personnel responsible for the technical management of data assets, including storage, backup, access control, and security.

(e) Data Users: All personnel who access or use TechVentures data in the course of their duties. Responsible for complying with data governance policies and procedures.

3. DATA QUALITY

3.1 Data quality dimensions and minimum standards:

(a) Accuracy: Data shall correctly represent the real-world entity or event it describes. Target: 99.5% accuracy for critical data elements.

(b) Completeness: Required data fields shall be populated. Target: 98% completeness for mandatory fields.

(c) Consistency: Data shall be consistent across all systems and repositories. Target: 99% cross-system consistency.

(d) Timeliness: Data shall be available within the required timeframe. Target: Real-time for operational data, T+1 for analytical data.

(e) Validity: Data shall conform to defined formats, ranges, and business rules. Target: 99.9% validity for structured data.

(f) Uniqueness: Data shall not contain unintended duplicates. Target: Less than 0.1% duplicate records for master data.

3.2 Data quality monitoring shall be automated and continuous for critical data assets. Quality dashboards shall be maintained and reviewed weekly by Data Stewards.

3.3 Data quality issues shall be tracked in the Data Quality Issue Register and resolved within the following timeframes:
(a) Critical (affects regulatory reporting or customer-facing systems): 24 hours;
(b) High (affects business decisions or operational efficiency): 72 hours;
(c) Medium (affects internal reporting or analytics): 5 business days;
(d) Low (cosmetic or minor inconsistencies): Next scheduled maintenance window.

4. DATA PRIVACY

4.1 Personal Data Processing:
(a) All processing of Personal Data shall have a lawful basis as defined by applicable Data Protection Laws;
(b) Privacy Impact Assessments (PIA) shall be conducted for any new system, process, or vendor that processes Personal Data;
(c) Data Protection Officer (DPO) shall be consulted on all privacy-related matters;
(d) Records of Processing Activities (ROPA) shall be maintained as required by GDPR Article 30 and PDPA requirements.

4.2 Data Subject Rights:
(a) Processes shall be in place to respond to Data Subject requests within statutory timeframes;
(b) Access requests: Response within 30 days (GDPR) or 30 days (PDPA);
(c) Erasure requests: Completion within 30 days, subject to legal retention requirements;
(d) Portability requests: Data provided in machine-readable format within 30 days.

4.3 Cross-Border Data Transfers:
(a) Personal Data shall not be transferred outside Singapore without appropriate safeguards;
(b) Approved transfer mechanisms: Standard Contractual Clauses (SCCs), Binding Corporate Rules (BCRs), or consent of the Data Subject;
(c) Transfer Impact Assessments shall be conducted for all new cross-border data flows;
(d) All cross-border transfers shall be documented in the Transfer Register.

5. DATA LIFECYCLE MANAGEMENT

5.1 Data Creation and Collection:
(a) Data collection shall be limited to what is necessary for the stated purpose (data minimization);
(b) Data sources shall be documented and validated;
(c) Data entry controls shall ensure accuracy at the point of creation.

5.2 Data Storage:
(a) Data shall be stored in approved systems and locations only;
(b) Storage classification: Hot (frequent access), Warm (periodic access), Cold (archival);
(c) Storage costs shall be optimized through automated tiering.

5.3 Data Retention:
(a) Retention periods shall be defined for all data categories in the Data Retention Schedule;
(b) Default retention periods:
    - Financial records: 7 years;
    - Customer data: Duration of relationship plus 3 years;
    - Employee records: Duration of employment plus 7 years;
    - Contract documents: Duration of contract plus 7 years;
    - Operational logs: 1 year;
    - Security logs: 3 years.
(c) Data beyond retention period shall be securely disposed of within 90 days.

5.4 Data Disposal:
(a) Secure disposal methods as specified in ISP-2024-001 Section 4.3;
(b) Disposal logs maintained for audit purposes;
(c) Third-party disposal vendors must be certified and audited.

6. METADATA MANAGEMENT

6.1 A centralized metadata repository (data catalog) shall be maintained for all critical data assets.

6.2 Required metadata elements:
(a) Data owner and steward;
(b) Classification level;
(c) Source system and lineage;
(d) Quality metrics;
(e) Retention period;
(f) Privacy classification;
(g) Access restrictions.

7. COMPLIANCE AND AUDIT

7.1 Data governance compliance shall be assessed:
(a) Continuously through automated monitoring;
(b) Quarterly through Data Steward reviews;
(c) Annually through internal audit;
(d) As required by external regulatory audits.

7.2 Non-compliance shall be reported to the Data Governance Council and tracked to resolution.

APPROVED BY:
Chief Data Officer: ____________________
General Counsel: ____________________
Date: 2024-01-01
"""
    (ws / "policy_information_security.txt").write_text(security_policy)
    (ws / "policy_data_governance.txt").write_text(data_governance)


def _gen_board_minutes(ws, contracts):
    vendor_lines = []
    for c in contracts:
        vendor_lines.append(
            f"    - {c['party_b']} ({c['service_type']}): Contract {c['id']}, "
            f"value {c['amount']}, term {c['start']} to {c['end']}."
        )
    vendors_text = "\n".join(vendor_lines)

    minutes = f"""BOARD OF DIRECTORS MEETING MINUTES
Meeting ID: BOD-2024-Q4
Date: 2024-12-20
Time: 10:00 AM — 12:30 PM (SGT)
Location: TechVentures Pte Ltd, 1 Raffles Place, #20-01, Boardroom A
Classification: RESTRICTED

ATTENDEES:
- James Chen, Chairman of the Board
- Sarah Lim, CEO
- David Tan, CFO
- Dr. Mei Wong, CTO
- Rajesh Kumar, Independent Director
- Patricia Ng, Independent Director
- Marcus Lee, General Counsel (Secretary)

ABSENT:
- None

QUORUM: Present (6 of 6 directors)

AGENDA:

1. Opening and Quorum Confirmation
2. Approval of Previous Minutes (BOD-2024-Q3)
3. CEO Report
4. CFO Report — Financial Performance
5. CTO Report — Technology Vendor Review
6. Risk Committee Report
7. Any Other Business
8. Adjournment

MINUTES:

1. OPENING AND QUORUM CONFIRMATION

The Chairman called the meeting to order at 10:00 AM and confirmed that a quorum was present. The Secretary confirmed that proper notice had been given to all directors.

2. APPROVAL OF PREVIOUS MINUTES

The minutes of the previous board meeting (BOD-2024-Q3, dated 2024-09-20) were reviewed. Director Kumar noted a minor correction to Item 5.3 regarding the timeline for the data center migration project. With the correction noted, the minutes were approved unanimously.

RESOLUTION 2024-Q4-01: The Board approved the minutes of the Q3 2024 Board Meeting with the noted correction.

3. CEO REPORT

The CEO presented the quarterly business update:

(a) Revenue for Q4 2024 is on track to meet the annual target of SGD 450M, representing 18% year-over-year growth.

(b) Customer acquisition: 23 new enterprise clients onboarded in Q4, bringing total active enterprise accounts to 187.

(c) Employee count: 1,247 (up from 1,180 in Q3). Voluntary attrition rate: 8.2% (industry average: 12%).

(d) Key strategic initiatives progressing as planned: Southeast Asia expansion (Malaysia and Indonesia offices operational), AI product suite launch scheduled for Q1 2025.

The Board discussed the competitive landscape and the CEO's strategic priorities for 2025. Director Ng inquired about the impact of regulatory changes in the EU on the company's European operations. The CEO confirmed that the legal team is monitoring developments and will provide a detailed assessment in the Q1 2025 meeting.

4. CFO REPORT — FINANCIAL PERFORMANCE

The CFO presented the Q4 2024 financial results:

(a) Revenue: SGD 118M (vs. budget SGD 115M, +2.6%)
(b) Gross margin: 72.3% (vs. budget 71.0%)
(c) Operating expenses: SGD 78M (vs. budget SGD 80M, -2.5%)
(d) EBITDA: SGD 40M (vs. budget SGD 35M, +14.3%)
(e) Net income: SGD 28M
(f) Cash position: SGD 195M
(g) Outstanding receivables: SGD 42M (DSO: 38 days)

Technology vendor spend for 2024:
{vendors_text}

Total technology vendor spend: USD 9.9M (within approved budget of USD 10.5M)

The CFO noted that all vendor contracts are performing within budget, with the exception of a USD 150K change order for the cloud infrastructure contract (Alpha) to support the Southeast Asia expansion. This was approved under the CTO's delegated authority.

Director Tan asked about the foreign exchange impact on USD-denominated contracts. The CFO confirmed that the company maintains FX hedging for 80% of USD exposure through 12-month forward contracts.

RESOLUTION 2024-Q4-02: The Board noted and approved the Q4 2024 financial results.

5. CTO REPORT — TECHNOLOGY VENDOR REVIEW

The CTO presented the annual technology vendor assessment summary:

5.1 Overall Vendor Performance:
- All four primary technology vendors received SATISFACTORY or above ratings in the annual assessment.
- No vendor received an UNSATISFACTORY rating in any category.
- Combined SLA compliance rate: 99.2% across all vendors.

5.2 Key Highlights:
- Cloud infrastructure (CloudNine Solutions): Strong performance, 99.92% availability. Recommended for contract renewal with enhanced SLA targets.
- AI/ML platform (DeepMind Analytics): Good progress on model development. First-pass acceptance rate needs improvement (87% vs. 90% target).
- Cybersecurity (CyberShield): Excellent incident response times. Zero Severity 1 incidents in 2024. SOC operations meeting all SLA targets.
- Data engineering (DataStream Technologies): Data pipeline reliability strong (99.7% availability). Data quality scores meeting targets.

5.3 Contract Renewals:
- Alpha (CloudNine): First Amendment (A1) executed in January 2025, extending term by 12 months and adding sustainability requirements.
- Beta (DeepMind Analytics): Contract expires February 2027. No action required at this time. Performance improvement plan in place for acceptance rate.
- Gamma (CyberShield): Contract expires May 2026. CTO recommends early renewal discussions beginning Q2 2025.
- Delta (DataStream): Contract expires April 2026. Performance satisfactory. Standard renewal process.

5.4 Security Posture:
- All vendors maintain required certifications (SOC 2 Type II, ISO 27001).
- Combined security incidents in 2024: 8 (0 Severity 1, 2 Severity 2, 6 Severity 3).
- Annual penetration testing completed for all vendors with no critical findings.

The Board discussed the vendor concentration risk and the CTO's recommendation to maintain the current four-vendor model rather than consolidating to fewer vendors. Director Kumar expressed support for the diversified approach given the current geopolitical environment.

RESOLUTION 2024-Q4-03: The Board approved the CTO's vendor management strategy and authorized the CTO to proceed with contract renewal discussions for the Gamma (CyberShield) contract.

6. RISK COMMITTEE REPORT

The Risk Committee Chairman (Director Kumar) presented the quarterly risk assessment:

6.1 Top 5 Enterprise Risks:
1. Cybersecurity threats (Risk Level: HIGH — unchanged)
2. Regulatory compliance — cross-border data regulations (Risk Level: HIGH — elevated from MEDIUM)
3. Key personnel retention in competitive market (Risk Level: MEDIUM — unchanged)
4. Vendor concentration and dependency (Risk Level: MEDIUM — unchanged)
5. Technology obsolescence (Risk Level: LOW — unchanged)

6.2 Mitigation Actions:
- Cybersecurity: Enhanced SOC capabilities through CyberShield contract. Quarterly penetration testing. Employee security awareness program refreshed.
- Regulatory: Legal team monitoring EU AI Act and ASEAN data protection developments. Privacy Impact Assessments completed for all cross-border data flows.
- Personnel: Competitive compensation review completed. Enhanced benefits package effective Q1 2025. Succession planning for key roles.
- Vendor: Annual vendor assessments completed. Business continuity plans tested for all critical vendor services.

RESOLUTION 2024-Q4-04: The Board noted the Risk Committee Report and approved the updated risk register.

7. ANY OTHER BUSINESS

7.1 Director Ng raised the topic of ESG reporting requirements for Singapore-listed companies. The CFO confirmed that the company is on track to publish its first sustainability report in Q2 2025, as required by SGX regulations.

7.2 The General Counsel provided an update on the pending intellectual property dispute with a former contractor. The matter is expected to be resolved through mediation in Q1 2025, with estimated exposure of SGD 500K.

8. ADJOURNMENT

There being no further business, the meeting was adjourned at 12:25 PM.

The next Board meeting is scheduled for 2025-03-21 at 10:00 AM.

CONFIRMED:
Chairman: ____________________
Secretary: ____________________
Date: 2024-12-20
"""
    (ws / "board_minutes_2024_q4.txt").write_text(minutes)


def _gen_nda(ws, contracts):
    for c in contracts[:2]:
        vendor = c["party_b"]
        nda = f"""MUTUAL NON-DISCLOSURE AGREEMENT
NDA ID: NDA-2023-{c["id"][-3:]}
Date: 2023-10-01

PARTIES:
Disclosing/Receiving Party 1: TechVentures Pte Ltd ("TechVentures"), a company incorporated under the laws of Singapore, with its registered office at 1 Raffles Place, #20-01, One Raffles Place Tower 2, Singapore 048616.

Disclosing/Receiving Party 2: {vendor} ("Vendor"), with its principal place of business as set forth in the applicable Service Agreement.

(Each a "Party" and collectively the "Parties")

RECITALS

WHEREAS, the Parties are considering or have entered into a business relationship relating to technology services (the "Purpose");

WHEREAS, in connection with the Purpose, each Party may disclose to the other Party certain Confidential Information (as defined below);

WHEREAS, the Parties desire to protect such Confidential Information from unauthorized use and disclosure;

NOW, THEREFORE, in consideration of the mutual covenants and agreements contained herein, and for other good and valuable consideration, the receipt and sufficiency of which are hereby acknowledged, the Parties agree as follows:

1. DEFINITIONS

1.1 "Confidential Information" means any and all non-public information, in any form or medium, disclosed by either Party (the "Disclosing Party") to the other Party (the "Receiving Party"), whether before or after the date of this Agreement, including but not limited to:

(a) Technical information: software, source code, object code, algorithms, APIs, system architectures, network configurations, database schemas, technical specifications, prototypes, and engineering data;

(b) Business information: business plans, strategies, financial data, pricing, customer lists, vendor lists, marketing plans, sales data, market research, product roadmaps, and competitive analyses;

(c) Personnel information: employee data, organizational charts, compensation structures, and human resources policies;

(d) Legal information: contracts, legal opinions, regulatory filings, intellectual property registrations, and litigation matters;

(e) Operational information: processes, procedures, methodologies, best practices, and operational metrics;

(f) Any information designated as "Confidential," "Proprietary," "Restricted," or similar marking by the Disclosing Party.

1.2 Confidential Information does not include information that:
(a) Is or becomes publicly available without breach of this Agreement;
(b) Was already known to the Receiving Party without restriction prior to disclosure;
(c) Is independently developed by the Receiving Party without use of Confidential Information;
(d) Is rightfully received from a third party without restriction on disclosure;
(e) Is required to be disclosed by law, regulation, or court order, subject to Section 3.3.

2. OBLIGATIONS

2.1 The Receiving Party shall:
(a) Hold all Confidential Information in strict confidence;
(b) Not disclose Confidential Information to any third party without the prior written consent of the Disclosing Party;
(c) Use Confidential Information solely for the Purpose;
(d) Limit access to Confidential Information to those employees, agents, and advisors who have a need to know and who are bound by confidentiality obligations at least as restrictive as those set forth herein;
(e) Protect Confidential Information using at least the same degree of care used to protect its own confidential information, but in no event less than reasonable care;
(f) Promptly notify the Disclosing Party of any unauthorized use or disclosure of Confidential Information.

2.2 The Receiving Party shall not:
(a) Reverse engineer, decompile, or disassemble any Confidential Information;
(b) Copy or reproduce Confidential Information except as necessary for the Purpose;
(c) Use Confidential Information to compete with the Disclosing Party;
(d) File any intellectual property applications based on the Disclosing Party's Confidential Information.

3. TERM AND TERMINATION

3.1 This Agreement shall remain in effect for three (3) years from the date first written above, unless terminated earlier by either Party upon thirty (30) days' written notice to the other Party.

3.2 The obligations of confidentiality set forth in this Agreement shall survive termination for a period of five (5) years, or for as long as the Confidential Information remains a trade secret under applicable law, whichever is longer.

3.3 Upon termination of this Agreement or upon the Disclosing Party's request, the Receiving Party shall promptly return or destroy all Confidential Information and certify such return or destruction in writing.

4. REMEDIES

4.1 The Parties acknowledge that any breach of this Agreement may cause irreparable harm for which monetary damages would be inadequate. Accordingly, the non-breaching Party shall be entitled to seek equitable relief, including injunction and specific performance, in addition to all other remedies available at law or in equity.

4.2 The non-breaching Party shall also be entitled to recover reasonable attorneys' fees and costs incurred in enforcing this Agreement.

5. GENERAL

5.1 This Agreement shall be governed by and construed in accordance with the laws of the Republic of Singapore.

5.2 This Agreement constitutes the entire agreement between the Parties regarding the subject matter hereof and supersedes all prior negotiations, representations, and agreements.

5.3 This Agreement may not be amended except by a written instrument signed by both Parties.

5.4 Neither Party may assign this Agreement without the prior written consent of the other Party.

5.5 If any provision of this Agreement is held to be invalid or unenforceable, the remaining provisions shall continue in full force and effect.

SIGNATURES:

TechVentures Pte Ltd
Name: ____________________
Title: ____________________
Date: 2023-10-01

{vendor}
Name: ____________________
Title: ____________________
Date: 2023-10-01
"""
        idx = c["id"][-3:]
        (ws / f"nda_{idx}_{vendor.split()[0].lower()}.txt").write_text(nda)


if __name__ == "__main__":
    generate_workspace_data()
