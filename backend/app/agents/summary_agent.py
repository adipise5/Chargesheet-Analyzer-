def case_summary(case: dict, counts: dict) -> str:
    return (f"{case['case_number']} contains {counts.get('documents', 0)} document(s) and {counts.get('pages', 0)} page(s). "
            f"The workspace has identified {counts.get('claims', 0)} candidate claim(s) and {counts.get('evidence', 0)} evidence reference(s). "
            "All machine-extracted findings remain decision-support material and should be checked against cited source pages.")

