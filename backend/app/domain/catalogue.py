"""Curated synthetic demonstration catalogue for Hydra.

Strictly synthetic records with fictional institutions and explicit provenance.
"""

from typing import List
from app.domain.frames import (
    AcademicPrerequisite,
    CertificationPrerequisite,
    EntrancePrerequisite,
    ProgrammeFrame,
)


def get_synthetic_programmes(
    include_alternative_demo: bool = False,
    include_all_domains: bool = False,
) -> List[ProgrammeFrame]:
    """Returns the canonical programmes, optionally including all domains and alternative demo."""
    progs = [
        ProgrammeFrame(
            programme_id="SYNTH_IN_CS_01",
            title="B.Tech. in Computer Science (Synthetic)",
            institution_name="Demo Institute of Technology, Bengaluru",
            location="Bengaluru, Karnataka",
            discipline="Computer Science",
            annual_tuition_inr=150000.0,
            duration_years=4,
            estimated_total_tuition_inr=600000.0,
            currency="INR",
            cost_basis="tuition_only_total",
            academic_prerequisites=[
                AcademicPrerequisite(
                    subject_code="MATH",
                    subject_name="Mathematics",
                    min_score=80.0,
                    grading_scale="percentage",
                    is_mandatory=True,
                ),
                AcademicPrerequisite(
                    subject_code="ENG",
                    subject_name="English",
                    min_score=70.0,
                    grading_scale="percentage",
                    is_mandatory=True,
                ),
                AcademicPrerequisite(
                    subject_code="PHYS",
                    subject_name="Physics",
                    min_score=75.0,
                    grading_scale="percentage",
                    is_mandatory=True,
                ),
            ],
            entrance_prerequisites=[
                EntrancePrerequisite(
                    exam_name="JEE Main",
                    max_rank=35000,
                    is_mandatory=True,
                )
            ],
            skills_developed=["Algorithms", "Software Architecture", "Data Structures"],
            career_paths=["Software Engineer", "Systems Architect"],
            parent_frame_id="FRAME_SPEC_CS",
            is_synthetic=True,
            dataset_label="SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL",
            provenance="SYNTHETIC_DEMO_RECORD_V1",
        ),
        ProgrammeFrame(
            programme_id="SYNTH_IN_DS_02",
            title="B.Tech. in Data Science (Synthetic)",
            institution_name="National Demonstration University, Pune",
            location="Pune, Maharashtra",
            discipline="Data Science",
            annual_tuition_inr=175000.0,
            duration_years=4,
            estimated_total_tuition_inr=700000.0,
            currency="INR",
            cost_basis="tuition_only_total",
            academic_prerequisites=[
                AcademicPrerequisite(
                    subject_code="MATH",
                    subject_name="Mathematics",
                    min_score=85.0,
                    grading_scale="percentage",
                    is_mandatory=True,
                ),
                AcademicPrerequisite(
                    subject_code="PROG",
                    subject_name="Programming / Computer Applications",
                    min_score=75.0,
                    grading_scale="percentage",
                    is_mandatory=True,
                ),
            ],
            entrance_prerequisites=[
                EntrancePrerequisite(
                    exam_name="JEE Main",
                    max_rank=25000,
                    is_mandatory=False,
                )
            ],
            skills_developed=["Machine Learning", "Statistical Modeling", "Python Programming"],
            career_paths=["Data Scientist", "Machine Learning Engineer"],
            parent_frame_id="FRAME_SPEC_DS",
            is_synthetic=True,
            dataset_label="SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL",
            provenance="SYNTHETIC_DEMO_RECORD_V1",
        ),
        ProgrammeFrame(
            programme_id="SYNTH_IN_BIO_03",
            title="B.Tech. in Biotechnology (Synthetic)",
            institution_name="Synthetic College of Engineering, Hyderabad",
            location="Hyderabad, Telangana",
            discipline="Biotechnology",
            annual_tuition_inr=125000.0,
            duration_years=4,
            estimated_total_tuition_inr=500000.0,
            currency="INR",
            cost_basis="tuition_only_total",
            academic_prerequisites=[
                AcademicPrerequisite(
                    subject_code="BIO",
                    subject_name="Biology",
                    min_score=75.0,
                    grading_scale="percentage",
                    is_mandatory=True,
                ),
                AcademicPrerequisite(
                    subject_code="CHEM",
                    subject_name="Chemistry",
                    min_score=75.0,
                    grading_scale="percentage",
                    is_mandatory=True,
                ),
            ],
            skills_developed=["Molecular Biology", "Bioinformatics", "Biochemical Analysis"],
            career_paths=["Biomedical Researcher", "Bioinformatics Analyst"],
            parent_frame_id="FRAME_SPEC_BIO",
            is_synthetic=True,
            dataset_label="SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL",
            provenance="SYNTHETIC_DEMO_RECORD_V1",
        ),
        ProgrammeFrame(
            programme_id="SYNTH_IN_ROB_04",
            title="B.Tech. in Robotics & AI (Synthetic)",
            institution_name="Metropolitan Demo University, Delhi NCR",
            location="Delhi NCR",
            discipline="Robotics",
            annual_tuition_inr=400000.0,
            duration_years=4,
            estimated_total_tuition_inr=1600000.0,
            currency="INR",
            cost_basis="tuition_only_total",
            academic_prerequisites=[
                AcademicPrerequisite(
                    subject_code="MATH",
                    subject_name="Mathematics",
                    min_score=75.0,
                    grading_scale="percentage",
                    is_mandatory=True,
                ),
                AcademicPrerequisite(
                    subject_code="PHYS",
                    subject_name="Physics",
                    min_score=75.0,
                    grading_scale="percentage",
                    is_mandatory=True,
                ),
            ],
            skills_developed=["Robotic Control Systems", "Embedded AI", "Computer Vision"],
            career_paths=["Robotics Engineer", "Autonomous Systems Specialist"],
            parent_frame_id="FRAME_SPEC_ROB",
            is_synthetic=True,
            dataset_label="SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL",
            provenance="SYNTHETIC_DEMO_RECORD_V1",
        ),
    ]

    if include_all_domains:
        multi_domain_progs = [
            ProgrammeFrame(
                programme_id="PROG_MED_01",
                title="MBBS - Bachelor of Medicine & Surgery",
                institution_name="National Medical Institute, Mumbai",
                location="Mumbai, Maharashtra",
                discipline="Medicine & Surgery",
                annual_tuition_inr=250000.0,
                duration_years=5,
                estimated_total_tuition_inr=1250000.0,
                currency="INR",
                cost_basis="tuition_only_total",
                academic_prerequisites=[
                    AcademicPrerequisite(subject_code="BIO", subject_name="Biology", min_score=80.0, grading_scale="percentage", is_mandatory=True),
                    AcademicPrerequisite(subject_code="CHEM", subject_name="Chemistry", min_score=75.0, grading_scale="percentage", is_mandatory=True),
                    AcademicPrerequisite(subject_code="PHYS", subject_name="Physics", min_score=75.0, grading_scale="percentage", is_mandatory=True),
                ],
                entrance_prerequisites=[
                    EntrancePrerequisite(exam_name="NEET", max_rank=25000, is_mandatory=True)
                ],
                skills_developed=["Clinical Diagnostics", "Pathology", "Surgical Anatomy", "Patient Care"],
                career_paths=["Physician", "Medical Specialist", "Clinical Researcher"],
                parent_frame_id="FRAME_SPEC_MBBS",
                is_synthetic=True,
                dataset_label="MULTI_DOMAIN_CATALOG",
                provenance="RECORD_MED_01",
            ),
            ProgrammeFrame(
                programme_id="PROG_PHARM_02",
                title="B.Pharm - Bachelor of Pharmacy",
                institution_name="Institute of Pharmaceutical Sciences, Ahmedabad",
                location="Ahmedabad, Gujarat",
                discipline="Pharmacy",
                annual_tuition_inr=120000.0,
                duration_years=4,
                estimated_total_tuition_inr=480000.0,
                currency="INR",
                cost_basis="tuition_only_total",
                academic_prerequisites=[
                    AcademicPrerequisite(subject_code="CHEM", subject_name="Chemistry", min_score=70.0, grading_scale="percentage", is_mandatory=True),
                    AcademicPrerequisite(subject_code="BIO", subject_name="Biology", min_score=70.0, grading_scale="percentage", is_mandatory=True),
                ],
                skills_developed=["Pharmacology", "Drug Formulation", "Medicinal Chemistry"],
                career_paths=["Pharmacist", "Clinical Pharmacologist", "Drug Safety Specialist"],
                parent_frame_id="FRAME_SPEC_PHARM",
                is_synthetic=True,
                dataset_label="MULTI_DOMAIN_CATALOG",
                provenance="RECORD_PHARM_02",
            ),
            ProgrammeFrame(
                programme_id="PROG_LAW_01",
                title="B.A. LL.B. (Hons) - 5-Year Integrated Law",
                institution_name="National Law School of Justice, Bengaluru",
                location="Bengaluru, Karnataka",
                discipline="Law",
                annual_tuition_inr=220000.0,
                duration_years=5,
                estimated_total_tuition_inr=1100000.0,
                currency="INR",
                cost_basis="tuition_only_total",
                academic_prerequisites=[
                    AcademicPrerequisite(subject_code="ENG", subject_name="English", min_score=80.0, grading_scale="percentage", is_mandatory=True),
                ],
                entrance_prerequisites=[
                    EntrancePrerequisite(exam_name="CLAT", max_rank=3500, is_mandatory=True)
                ],
                skills_developed=["Constitutional Law", "Legal Drafting", "Jurisprudence", "Advocacy"],
                career_paths=["Advocate / Litigator", "Corporate Counsel", "Legal Analyst"],
                parent_frame_id="FRAME_SPEC_LLB",
                is_synthetic=True,
                dataset_label="MULTI_DOMAIN_CATALOG",
                provenance="RECORD_LAW_01",
            ),
            ProgrammeFrame(
                programme_id="PROG_LAW_02",
                title="B.B.A. LL.B. (Corporate Law)",
                institution_name="School of Legal Studies, Delhi",
                location="Delhi NCR",
                discipline="Corporate Law",
                annual_tuition_inr=190000.0,
                duration_years=5,
                estimated_total_tuition_inr=950000.0,
                currency="INR",
                cost_basis="tuition_only_total",
                academic_prerequisites=[
                    AcademicPrerequisite(subject_code="ENG", subject_name="English", min_score=75.0, grading_scale="percentage", is_mandatory=True),
                ],
                entrance_prerequisites=[
                    EntrancePrerequisite(exam_name="CLAT", max_rank=6500, is_mandatory=False)
                ],
                skills_developed=["Mergers & Acquisitions Law", "Corporate Governance", "Contract Negotiation"],
                career_paths=["Corporate Counsel", "Compliance Director", "Legal Consultant"],
                parent_frame_id="FRAME_SPEC_LLB",
                is_synthetic=True,
                dataset_label="MULTI_DOMAIN_CATALOG",
                provenance="RECORD_LAW_02",
            ),
            ProgrammeFrame(
                programme_id="PROG_MGMT_01",
                title="B.B.A. in International Business & Analytics",
                institution_name="Global Management Academy, Gurugram",
                location="Gurugram, Haryana",
                discipline="Business Administration",
                annual_tuition_inr=180000.0,
                duration_years=3,
                estimated_total_tuition_inr=540000.0,
                currency="INR",
                cost_basis="tuition_only_total",
                academic_prerequisites=[
                    AcademicPrerequisite(subject_code="ENG", subject_name="English", min_score=75.0, grading_scale="percentage", is_mandatory=True),
                    AcademicPrerequisite(subject_code="MATH", subject_name="Mathematics", min_score=65.0, grading_scale="percentage", is_mandatory=True),
                ],
                entrance_prerequisites=[
                    EntrancePrerequisite(exam_name="IPMAT", max_rank=4000, is_mandatory=False)
                ],
                skills_developed=["Financial Analysis", "Strategic Management", "Marketing Analytics", "Operations"],
                career_paths=["Management Consultant", "Business Operations Lead", "Product Strategist"],
                parent_frame_id="FRAME_SPEC_BBA",
                is_synthetic=True,
                dataset_label="MULTI_DOMAIN_CATALOG",
                provenance="RECORD_MGMT_01",
            ),
            ProgrammeFrame(
                programme_id="PROG_MGMT_02",
                title="B.Com. (Hons) in Financial Technology",
                institution_name="St. Xavier's Commerce College, Kolkata",
                location="Kolkata, West Bengal",
                discipline="Finance & Accounting",
                annual_tuition_inr=110000.0,
                duration_years=3,
                estimated_total_tuition_inr=330000.0,
                currency="INR",
                cost_basis="tuition_only_total",
                academic_prerequisites=[
                    AcademicPrerequisite(subject_code="MATH", subject_name="Mathematics", min_score=75.0, grading_scale="percentage", is_mandatory=True),
                    AcademicPrerequisite(subject_code="ENG", subject_name="English", min_score=70.0, grading_scale="percentage", is_mandatory=True),
                ],
                skills_developed=["Quantitative Finance", "FinTech Systems", "Auditing", "Taxation"],
                career_paths=["Financial Analyst", "Investment Banker", "Fintech Product Manager"],
                parent_frame_id="FRAME_SPEC_BBA",
                is_synthetic=True,
                dataset_label="MULTI_DOMAIN_CATALOG",
                provenance="RECORD_MGMT_02",
            ),
            ProgrammeFrame(
                programme_id="PROG_DES_01",
                title="B.Des. in User Experience & Interaction Design",
                institution_name="National Design Institute, Bengaluru",
                location="Bengaluru, Karnataka",
                discipline="Design",
                annual_tuition_inr=240000.0,
                duration_years=4,
                estimated_total_tuition_inr=960000.0,
                currency="INR",
                cost_basis="tuition_only_total",
                academic_prerequisites=[
                    AcademicPrerequisite(subject_code="ENG", subject_name="English", min_score=70.0, grading_scale="percentage", is_mandatory=True),
                ],
                entrance_prerequisites=[
                    EntrancePrerequisite(exam_name="UCEED", max_rank=2500, is_mandatory=False)
                ],
                skills_developed=["User Experience (UX) Design", "Interaction Design", "Prototyping", "Design Systems"],
                career_paths=["Product Designer", "UI/UX Lead", "Design Technologist"],
                parent_frame_id="FRAME_SPEC_BDES",
                is_synthetic=True,
                dataset_label="MULTI_DOMAIN_CATALOG",
                provenance="RECORD_DES_01",
            ),
            ProgrammeFrame(
                programme_id="PROG_DES_02",
                title="B.Arch. - Bachelor of Architecture (5-Yr)",
                institution_name="Faculty of Architecture & Urban Design, Chandigarh",
                location="Chandigarh, Punjab",
                discipline="Architecture",
                annual_tuition_inr=160000.0,
                duration_years=5,
                estimated_total_tuition_inr=800000.0,
                currency="INR",
                cost_basis="tuition_only_total",
                academic_prerequisites=[
                    AcademicPrerequisite(subject_code="MATH", subject_name="Mathematics", min_score=75.0, grading_scale="percentage", is_mandatory=True),
                ],
                entrance_prerequisites=[
                    EntrancePrerequisite(exam_name="NATA", max_rank=5000, is_mandatory=True)
                ],
                skills_developed=["Architectural Design", "Urban Planning", "BIM Modeling", "Structural Engineering"],
                career_paths=["Architect", "Urban Designer", "BIM Specialist"],
                parent_frame_id="FRAME_SPEC_BDES",
                is_synthetic=True,
                dataset_label="MULTI_DOMAIN_CATALOG",
                provenance="RECORD_DES_02",
            ),
            ProgrammeFrame(
                programme_id="PROG_SCI_01",
                title="B.Sc. (Hons) in Mathematics & Computing",
                institution_name="Center for Mathematical Sciences, Chennai",
                location="Chennai, Tamil Nadu",
                discipline="Mathematics & Computing",
                annual_tuition_inr=95000.0,
                duration_years=3,
                estimated_total_tuition_inr=285000.0,
                currency="INR",
                cost_basis="tuition_only_total",
                academic_prerequisites=[
                    AcademicPrerequisite(subject_code="MATH", subject_name="Mathematics", min_score=88.0, grading_scale="percentage", is_mandatory=True),
                    AcademicPrerequisite(subject_code="ENG", subject_name="English", min_score=70.0, grading_scale="percentage", is_mandatory=True),
                ],
                skills_developed=["Discrete Mathematics", "Combinatorics", "Cryptography", "Stochastic Calculus"],
                career_paths=["Quantitative Researcher", "Cryptographer", "Algorithm Engineer"],
                parent_frame_id="FRAME_SPEC_MATH_COMP",
                is_synthetic=True,
                dataset_label="MULTI_DOMAIN_CATALOG",
                provenance="RECORD_SCI_01",
            ),
            ProgrammeFrame(
                programme_id="PROG_SCI_02",
                title="B.Sc. (Hons) in Economics & Data Analytics",
                institution_name="School of Economics & Public Policy, Mumbai",
                location="Mumbai, Maharashtra",
                discipline="Economics",
                annual_tuition_inr=135000.0,
                duration_years=3,
                estimated_total_tuition_inr=405000.0,
                currency="INR",
                cost_basis="tuition_only_total",
                academic_prerequisites=[
                    AcademicPrerequisite(subject_code="MATH", subject_name="Mathematics", min_score=80.0, grading_scale="percentage", is_mandatory=True),
                    AcademicPrerequisite(subject_code="ENG", subject_name="English", min_score=75.0, grading_scale="percentage", is_mandatory=True),
                ],
                skills_developed=["Econometrics", "Macroeconomic Modeling", "Data Analysis", "Game Theory"],
                career_paths=["Economic Consultant", "Policy Analyst", "Risk Specialist"],
                parent_frame_id="FRAME_SPEC_MATH_COMP",
                is_synthetic=True,
                dataset_label="MULTI_DOMAIN_CATALOG",
                provenance="RECORD_SCI_02",
            ),
            ProgrammeFrame(
                programme_id="PROG_HUM_01",
                title="B.A. (Hons) in Psychology & Cognitive Science",
                institution_name="Apex Institute of Humanities, New Delhi",
                location="New Delhi",
                discipline="Psychology",
                annual_tuition_inr=105000.0,
                duration_years=3,
                estimated_total_tuition_inr=315000.0,
                currency="INR",
                cost_basis="tuition_only_total",
                academic_prerequisites=[
                    AcademicPrerequisite(subject_code="ENG", subject_name="English", min_score=75.0, grading_scale="percentage", is_mandatory=True),
                ],
                skills_developed=["Cognitive Behavioral Research", "Psychometrics", "Neuropsychology", "Statistical Methods"],
                career_paths=["Cognitive Researcher", "Behavioral Analyst", "Counseling Psychologist"],
                parent_frame_id="FRAME_SPEC_MATH_COMP",
                is_synthetic=True,
                dataset_label="MULTI_DOMAIN_CATALOG",
                provenance="RECORD_HUM_01",
            ),
            ProgrammeFrame(
                programme_id="PROG_ENG_AERO",
                title="B.Tech. in Aerospace & Avionics Engineering",
                institution_name="Aeronautical Academy of Technology, Hyderabad",
                location="Hyderabad, Telangana",
                discipline="Aerospace Engineering",
                annual_tuition_inr=210000.0,
                duration_years=4,
                estimated_total_tuition_inr=840000.0,
                currency="INR",
                cost_basis="tuition_only_total",
                academic_prerequisites=[
                    AcademicPrerequisite(subject_code="PHYS", subject_name="Physics", min_score=80.0, grading_scale="percentage", is_mandatory=True),
                    AcademicPrerequisite(subject_code="MATH", subject_name="Mathematics", min_score=85.0, grading_scale="percentage", is_mandatory=True),
                ],
                entrance_prerequisites=[
                    EntrancePrerequisite(exam_name="JEE Main", max_rank=28000, is_mandatory=True)
                ],
                skills_developed=["Aerodynamics", "Avionics Systems", "Propulsion Design", "Flight Control"],
                career_paths=["Aerospace Engineer", "Avionics Systems Designer", "Flight Dynamics Specialist"],
                parent_frame_id="FRAME_ENGINEERING_BASE",
                is_synthetic=True,
                dataset_label="MULTI_DOMAIN_CATALOG",
                provenance="RECORD_ENG_AERO",
            ),
            ProgrammeFrame(
                programme_id="PROG_ENG_ECE",
                title="B.Tech. in Electronics & Communication",
                institution_name="Southern Institute of Technology, Chennai",
                location="Chennai, Tamil Nadu",
                discipline="Electronics",
                annual_tuition_inr=145000.0,
                duration_years=4,
                estimated_total_tuition_inr=580000.0,
                currency="INR",
                cost_basis="tuition_only_total",
                academic_prerequisites=[
                    AcademicPrerequisite(subject_code="PHYS", subject_name="Physics", min_score=75.0, grading_scale="percentage", is_mandatory=True),
                    AcademicPrerequisite(subject_code="MATH", subject_name="Mathematics", min_score=80.0, grading_scale="percentage", is_mandatory=True),
                ],
                entrance_prerequisites=[
                    EntrancePrerequisite(exam_name="JEE Main", max_rank=32000, is_mandatory=True)
                ],
                skills_developed=["Embedded Systems", "VLSI Design", "Signal Processing", "Wireless Networks"],
                career_paths=["Hardware Engineer", "VLSI Designer", "Telecom Engineer"],
                parent_frame_id="FRAME_ENGINEERING_BASE",
                is_synthetic=True,
                dataset_label="MULTI_DOMAIN_CATALOG",
                provenance="RECORD_ENG_ECE",
            ),
        ]
        progs.extend(multi_domain_progs)

    if include_alternative_demo:
        progs.append(get_synthetic_alternative_pathway_programme())
    return progs


def get_synthetic_alternative_pathway_programme() -> ProgrammeFrame:
    """Returns a synthetic programme configured with alternative admission pathways for demonstration.

    Prerequisite Expression (Demonstration of Logic Only, Not University Policy):
    (Math >= 80% AND Physics >= 75%) OR (JEE Main rank <= 15,000)
    """
    from app.rules.expressions import (
        AllOf,
        AnyOf,
        EntranceRankRequirement,
        SubjectScoreRequirement,
    )

    alt_expr = AnyOf(
        expression_id="DEMO_ALT_ADMISSION_PATHWAY",
        label="Alternative Qualifying Pathway: Boards Benchmark OR National Entrance Rank",
        children=[
            AllOf(
                expression_id="DEMO_BOARDS_BRANCH",
                label="Senior Secondary Academic Benchmark (Math >= 80%, Physics >= 75%)",
                children=[
                    SubjectScoreRequirement(subject_code="MATH", min_score=80.0, is_mandatory=True),
                    SubjectScoreRequirement(subject_code="PHYS", min_score=75.0, is_mandatory=True),
                ],
            ),
            EntranceRankRequirement(
                expression_id="DEMO_ENTRANCE_BRANCH",
                exam_name="JEE Main",
                max_rank=15000,
                is_mandatory=True,
            ),
        ],
    )

    return ProgrammeFrame(
        programme_id="SYNTH_IN_ALT_DEMO_05",
        title="B.Tech. in Computational Sciences (Synthetic Alternative Pathway Demo)",
        institution_name="Demo Institute of Technology, Bengaluru",
        location="Bengaluru, Karnataka",
        discipline="Computational Sciences",
        annual_tuition_inr=160000.0,
        duration_years=4,
        estimated_total_tuition_inr=640000.0,
        currency="INR",
        cost_basis="tuition_only_total",
        skills_developed=["High-Performance Computing", "Mathematical Modeling", "Scientific Simulation"],
        career_paths=["Computational Scientist", "Simulation Engineer"],
        parent_frame_id="FRAME_SPEC_CS",
        requirement_expression=alt_expr,
        is_synthetic=True,
        dataset_label="SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL",
        provenance="SYNTHETIC_DEMO_RECORD_V1",
    )


