import numpy as np

array = np.array([1, 3, 5, 8])

print(array)

matrix = np.array([[1, 9, 4], [3, 2, 1]])

# Adds 10 to ALL elements
matrix = matrix + 10

print(matrix)
print(matrix.shape)  # Returs (2, 3) - shape of a matrix

matrix = np.ones((3, 3))  # 3x3 matrix of ones
row = np.array([1, 2, 3])

print(matrix + row)  # Works anyway

random_array = np.random.randint(1, 100, 10)

print(random_array)
print(random_array.mean())
print(random_array[random_array > 50])

# 1. How would you create a one-dimensional NumPy array
# of the numbers from 10 to 100, counting by 10?
array_of_10_by_10 = np.arange(10, 101, 10)

print(array_of_10_by_10)
print(len(array_of_10_by_10))

# 2. How could you create the same NumPy array using a Python range and a list?
array = np.array([i for i in range(10, 101, 10)])

print(array)

# 3. What happens if you pass no arguments to the np.array()?
empty = np.array(2)

print(empty)

# 4. How might you create a NumPy array of the capital letters, A-Z?
letters_array = np.array([chr(code) for code in range(ord("A"), ord("Z") + 1, 1)])
print(letters_array)

# 5. How would you create a ten-element NumPy array object of all zeros?

zeros = np.zeros(10)
print(zeros)

# 6. How would you find the data type given in #4.
print(zeros.dtype)

# 8. What function would return the same number of elements, but of all ones?
ones = np.ones(10)
print(ones)
print(ones.dtype)

# 9. How could you create a ten-element array of
# random integers between 1 and 5 (inclusive)?
randoms = np.random.randint(1, 6, 10)
print(randoms)

# 10. How can you create a normal distribution of 10 numbers, centered on 5?
distributed = np.random.normal(5, 1, 10)
print(distributed)
