import pandas as pd
import matplotlib.pyplot as plt

# Load the uploaded CSV
df = pd.read_csv("y_axis_steering.csv")

# Plot the steering value and direction
plt.figure(figsize=(14, 6))

# Line plot of steering value
plt.plot(df["frame"], df["steering_smooth"], label="Steering Value", color='blue')

# Highlight direction changes
for idx, row in df.iterrows():
    if row["stable_direction"] != "NEUTRAL":
        color = 'green' if row["stable_direction"] == "RIGHT TURN" else 'red'
        plt.axvline(x=row["frame"], color=color, linestyle='--', alpha=0.2)

plt.title("Steering Value Over Time with Stable Direction Indicators")
plt.xlabel("Frame")
plt.ylabel("Steering Value (-1: Left, 0: Neutral, 1: Right)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
