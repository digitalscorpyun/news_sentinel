# This file contains the exercises from chapter 3 - lists
names = ['james', 'john', 'jacob', 'joseph']
# print the names in the list
print(names[0].title())
print(names[1].title())
print(names[2].title())
print(names[3].title())
# print a message to each person in the list
print(f"Hello {names[0].title()}, how are you doing today?")
print(f"Hello {names[1].title()}, how are you doing today?")
print(f"Hello {names[2].title()}, how are you doing today?")
print(f"Hello {names[3].title()}, how are you doing today?")
motorcycles = ['honda', 'yamaha', 'suzuki']
print(motorcycles[0].title())
print(motorcycles[1].title())
print(motorcycles[2].title())
# change the first element in the list
motorcycles[0] = 'ducati'
print(motorcycles)
# add an element to the end of the list
motorcycles.append('honda')
print(motorcycles)
# create an empty list and add elements to it
cars = []
cars.append('audi')
cars.append('BMW')
cars.append('mercedes')
print(cars)
# insert an element at a specific index
cars.insert(0, 'toyota')
print(cars)
# remove an element from the list
del cars[0]
print(cars)
# remove an element by value
cars.remove('audi')
print(cars)
# print a message to the user about the car they want to drive
print(f"I'd like to drive a {cars[0].title()}!")
# Modifying elements in a list
motorcycles = ['honda', 'yamaha', 'suzuki']
print(motorcycles)
# change the first element in the list
motorcycles[0] = 'ducati'
print(motorcycles)
# Appending Elements to the End of a List
motorcycles.append('ducati')
print(motorcycles)
# Inserting Elements into a List
motorcycles.insert(0, 'ducati')
print(motorcycles)
# Removing an Item Using the del Statement
del motorcycles[0] 
print(motorcycles)