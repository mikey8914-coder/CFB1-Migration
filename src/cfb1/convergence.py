"""OLD CELL 34 corrected directional convergence. No routing decisions."""

import pandas as pd


def corrected_convergence(master):
    """Count own positives/opponent negatives as support for the shared side."""
    rows = []
    for _, row in master.iterrows():
        away, home = row.Away_Team, row.Home_Team
        epa, fei = row.EPA_Edge_Team, row.DK_FEI_Edge_Team
        agree = epa == fei and epa != "EVEN"
        shared = epa if agree else ""
        positives, negatives = {}, {}
        for side in ["Away", "Home"]:
            positives[side] = [label for field, label in [
                ("LineYards_Push", "LINE_YARDS"), ("OAY_DAY_Edge", "OAY_DAY")]
                if row[f"{side}_{field}"]]
            negatives[side] = [label for field, label in [
                ("Havoc_Trap", "HAVOC_TRAP"), ("Explosiveness_Fraud", "EXPLOSIVENESS_FRAUD")]
                if row[f"{side}_{field}"]]
        support, conflict = [], []
        if shared == away:
            own, opponent = "Away", "Home"
        elif shared == home:
            own, opponent = "Home", "Away"
        else:
            own = opponent = None
        if own is not None:
            support.extend(f"{row[f'{own}_Team']} +{signal}" for signal in positives[own])
            support.extend(f"{row[f'{opponent}_Team']} -{signal}" for signal in negatives[opponent])
            conflict.extend(f"{row[f'{own}_Team']} -{signal}" for signal in negatives[own])
            conflict.extend(f"{row[f'{opponent}_Team']} +{signal}" for signal in positives[opponent])
        rows.append({"Game": f"{away} at {home}", "EPA_Team": epa, "EPA_Value": row.EPA_Edge_Value,
                     "FEI_Team": fei, "FEI_Value": row.DK_FEI_Edge_Value, "EPA_FEI_Agree": agree,
                     "Shared_Side": shared, "M3_Support": ", ".join(support),
                     "M3_Conflict": ", ".join(conflict), "M3_Support_Count": len(support),
                     "M3_Conflict_Count": len(conflict)})
    result = pd.DataFrame(rows)
    required = ["Game", "EPA_Team", "EPA_Value", "FEI_Team", "FEI_Value", "EPA_FEI_Agree",
                "Shared_Side", "M3_Support_Count", "M3_Conflict_Count"]
    if (len(result) != len(master) or result.duplicated(subset=["Game"], keep=False).sum()
            or result[required].isna().any(axis=1).sum()
            or (result.EPA_FEI_Agree & (result.Shared_Side == "")).sum()):
        raise ValueError("Corrected convergence validation failed")
    return result
