MART_SHARED_KEYS = {
    "fct_patient_metrics": {"patient_id"},
    "fct_interventions": {"patient_id"},
    "dim_patients": {"patient_id"},
    "dim_conditions": {"patient_id"},
}

MART_COLUMNS = {
    "fct_patient_metrics": {
        "patient_id",
        "first_name",
        "last_name",
        "date_of_birth",
        "sex",
        "race",
        "ethnicity",
        "insurance_name",
        "org_id",
        "org_name",
        "sdoh_score",
        "comprehensive_score",
        "hcc_score",
        "impactability_score",
        "quality_score",
        "latest_score_date",
    },
    "fct_interventions": {
        "patient_id",
        "first_name",
        "last_name",
        "insurance_name",
        "org_id",
        "intervention_name",
        "service_date",
        "cost_actual",
        "intervention_expected_cost",
        "intervention_outcome_cost",
    },
    "dim_patients": {
        "patient_id",
        "first_name",
        "last_name",
        "date_of_birth",
        "sex",
        "race",
        "ethnicity",
        "insurance_name",
        "org_id",
        "org_name",
    },
    "dim_conditions": {
        "patient_id",
        "condition_name",
        "condition_category",
        "onset_date",
        "resolution_date",
    },
}

STAGING_TABLES = {
    "stg_patient",
    "stg_lob",
    "stg_map_patient_metrics",
    "stg_patient_score",
    "stg_contributor_type",
    "stg_contributor_individual",
    "stg_organization",
    "stg_intervention_type",
    "stg_intervention_service",
    "stg_user",
}


def classify_query(rag_tables: str, user_question: str) -> tuple[str, list[str]]:
    mart_tables = [t for t in MART_COLUMNS if t in rag_tables]

    if not mart_tables:
        return "tier_3_staging", list(STAGING_TABLES)

    if len(mart_tables) == 1:
        return "tier_1_single_mart", mart_tables[:1]

    shared = MART_SHARED_KEYS.get(mart_tables[0], set())
    for mt in mart_tables[1:]:
        shared = shared & MART_SHARED_KEYS.get(mt, set())
        if not shared:
            return "tier_3_staging", list(STAGING_TABLES)

    return "tier_2_multi_mart", mart_tables


def build_enriched_prompt(user_question: str, rag_result: str) -> str:
    tier, tables = classify_query(rag_result, user_question)

    schema_text = rag_result

    if tier == "tier_1_single_mart":
        strategy = (
            f"STRATEGY: Query only '{tables[0]}'. No joins needed. "
            f"All columns are pre-joined in this table."
        )
    elif tier == "tier_2_multi_mart":
        shared_keys = MART_SHARED_KEYS.get(tables[0], set())
        for t in tables[1:]:
            shared_keys = shared_keys & MART_SHARED_KEYS.get(t, set())
        join_on = ", ".join(shared_keys) if shared_keys else "patient_id"
        strategy = (
            f"STRATEGY: Join tables {tables} on {join_on}. "
            f"Use simple JOIN on {join_on} = {join_on}."
        )
    else:
        strategy = (
            "STRATEGY: Complex query. Use sql_db_find_table_connections "
            "to discover join paths. Fall back to SchemaGraph if needed."
        )

    return f"""User Question: {user_question}

Relevant Tables:
{schema_text}

{strategy}

Generate SQL to answer the question. Use LIMIT 10. For BINARY(16) IDs use HEX().
Filter by Organization ID if provided in the security context."""
