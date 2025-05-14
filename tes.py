import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Data dummy: [gas_level (MQ2), temperature (DHT11), humidity (DHT11)]
data = np.array([
    [250, 28, 65],  # rokok
    [260, 27, 64],
    [255, 29, 63],
    [300, 33, 40],  # kebakaran
    [320, 35, 38],
    [310, 34, 42],
    [150, 25, 70],  # vape
    [140, 24, 72],
    [145, 26, 69],
])

# Normalisasi
scaler = StandardScaler()
scaled_data = scaler.fit_transform(data)

# Clustering K=3
kmeans = KMeans(n_clusters=2, random_state=0)
kmeans.fit(scaled_data)
labels = kmeans.labels_

# Gabungkan data
df = pd.DataFrame(data, columns=["Gas (MQ2)", "Temp (°C)", "Humidity (%)"])
df["Cluster"] = labels
print(df)

# Mapping manual hasil cluster ke jenis asap
cluster_mapping = {}
for cluster in range(3):
    # Ambil baris dari cluster itu
    subset = df[df["Cluster"] == cluster]
    avg_gas = subset["Gas (MQ2)"].mean()
    if avg_gas > 290:
        cluster_mapping[cluster] = "Kebakaran"
    elif avg_gas < 160:
        cluster_mapping[cluster] = "Vape"
    else:
        cluster_mapping[cluster] = "Rokok"

# Visualisasi
plt.figure(figsize=(8,6))
plt.scatter(data[:, 0], data[:, 1], c=labels, cmap='viridis', s=100)
plt.xlabel("Gas (MQ2)")
plt.ylabel("Temperature (°C)")
plt.title("K-Means Clustering of Smoke Types")
plt.grid(True)
plt.show()

# 🔍 Input dari user
gas_input = float(input("Masukkan nilai gas (MQ2): "))
temp_input = float(input("Masukkan suhu (°C): "))
humid_input = float(input("Masukkan kelembapan (%): "))

# Normalisasi & prediksi
user_data = scaler.transform([[gas_input, temp_input, humid_input]])
predicted_cluster = kmeans.predict(user_data)[0]

# Tampilkan hasil
print(f"\nData masuk: Gas={gas_input}, Temp={temp_input}, Humidity={humid_input}")
print(f"Prediksi jenis asap: {cluster_mapping[predicted_cluster]}")
