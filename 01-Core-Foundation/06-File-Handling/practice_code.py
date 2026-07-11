# ----------------------------------------------------------------------
# Course: Python Mastery
# Chapter 06: File Handling - Lab Practice
# ----------------------------------------------------------------------
import json
import csv

print("=== Chapter 06: Practice Lab Starting ===")

# ----------------------------------------------------------------------
# 🎯 TASK 1: The Log Collector (Append Mode)
# Instruction: Take a message string from the user. Open a file named
# 'user_logs.txt' in append mode and write the string onto a fresh line.
# ----------------------------------------------------------------------
print("\n--- Task 1: Activity Logger ---")

# Your code here:


# ----------------------------------------------------------------------
# 🎯 TASK 2: JSON Config Builder
# Instruction: Convert the given Python dictionary into a permanent
# file called 'settings.json' with an indentation spacing format of 4.
# ----------------------------------------------------------------------
print("\n--- Task 2: JSON Exporter ---")

system_settings = {"theme": "Dark-Mode", "fontSize": 14, "autoSave": True}

# Your code here:


# ----------------------------------------------------------------------
# 🎯 TASK 3: CSV Student Iterator
# Instruction: Read the given raw matrix string and print only the
# names of students who passed (Grade not equal to F).
# ----------------------------------------------------------------------
print("\n--- Task 3: CSV Parser ---")

# First, let's create a dummy CSV file automatically for you:
with open("students.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["ID", "Name", "Result"])
    writer.writerow(["101", "Rahul", "Pass"])
    writer.writerow(["102", "Amit", "Fail"])
    writer.writerow(["103", "Priya", "Pass"])

# NOW: Write your code below to open 'students.csv', read lines,
# and print names only if the third column value is "Pass"

# Your code here:


print("\n=== End of Chapter 06 Practice Lab ===")
