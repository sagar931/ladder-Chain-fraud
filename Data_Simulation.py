import pandas as pd
import numpy as np

# Parameters
np.random.seed(42)
months = pd.date_range("2020-01-01", periods=36, freq="M")  # 3 years of fraud
development_lags = 24  # Claims develop over 24 months
base_loss = 50_000  # Average ultimate loss per month

# Simulate reported fraud losses
data = []
for i, month in enumerate(months):
    ultimate_loss = base_loss * (1 + 0.05 * (i // 12))  # 5% annual inflation
    for lag in range(1, development_lags + 1):
        if lag <= len(months) - i:  # Ensure no future data
            # Reported loss pattern (logistic curve for slow buildup)
            reported_pct = 0.4 * (1 - np.exp(-lag/3)) + 0.6 * (1 - np.exp(-lag/12))
            reported_loss = ultimate_loss * reported_pct * np.random.lognormal(0, 0.1)
            data.append({
                "FraudMonth": month.strftime("%b-%Y"),
                "Lag (Months)": lag,
                "ReportedLoss": round(reported_loss, 2)
            })

df = pd.DataFrame(data)
pivot_df = df.pivot(index="FraudMonth", columns="Lag (Months)", values="ReportedLoss")
pivot_df.to_csv("insurance_fraud_chain_ladder_data.csv")  # Save for analysis
print(pivot_df.head(10))
