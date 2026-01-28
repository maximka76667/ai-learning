import numpy as np

data = np.array(
    [
        33998.0,
        25934.0,
        33469.0,
        23848.0,
        23948.0,
        21492.0,
        8393.0,
        36725.0,
        21017.0,
        20894.0,
        15267.0,
        31746.0,
        18693.0,
        24364.0,
        32921.0,
        39527.0,
        21791.0,
        25354.0,
        31122.0,
        18656.0,
        19211.0,
        24278.0,
        23641.0,
        25571.0,
        19541.0,
        19512.0,
        30886.0,
        17796.0,
        30070.0,
        19432.0,
        29989.0,
    ]
)

print(len(data))
print(data[15])

mean = np.round(data.mean() / 1000, 2)

print(mean)

indices = np.where(data / 1000 >= mean)[0]
values = data[indices]

spikes = list(zip(indices, values))
clean_spikes = [print(idx.item(), val.item()) for idx, val in spikes]
print(len(clean_spikes))
print(31 * mean)
