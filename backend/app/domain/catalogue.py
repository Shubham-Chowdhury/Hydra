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


def get_synthetic_programmes(include_alternative_demo: bool = False) -> List[ProgrammeFrame]:
    """Returns the four canonical synthetic programmes used in Phase 1 (optionally including alternative demo)."""
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


