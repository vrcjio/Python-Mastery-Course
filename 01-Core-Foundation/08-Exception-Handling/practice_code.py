# ----------------------------------------------------------------------
# Course: Python Mastery
# Chapter 08: Exception Handling - Lab Practice
# ----------------------------------------------------------------------

print("=== Chapter 08: Practice Lab Starting ===")

# ----------------------------------------------------------------------
# 🎯 TASK 1: Safe Division Engine
# Instruction: Wrap the calculation inside a try-except structure.
# Explicitly handle ZeroDivisionError and print a friendly alert message.
# ----------------------------------------------------------------------
print("\n--- Task 1: Safe Division Manager ---")

numerator = 100
denominator = 0

# Your code here:


# ----------------------------------------------------------------------
# 🎯 TASK 2: Continuous Age Guard (While Loop + Try-Except)
# Instruction: Keep asking the user for their age until they type a valid
# numeric value. Use try-except to catch ValueError.
# ----------------------------------------------------------------------
print("\n--- Task 2: Robust Input Loop ---")

# Your code here:


# ----------------------------------------------------------------------
# 🎯 TASK 3: Explicit Custom Exceptions (The Raise Guard)
# Instruction: Complete the condition check. If input price is negative,
# use 'raise ValueError' to trigger an exception manually with an alert string.
# ----------------------------------------------------------------------
print("\n--- Task 3: Price Validator System ---")


def validate_product_price(price):
    try:
        if price < 0:
            # Your code here (Raise exception):
            pass
        else:
            print(f"Price approved: INR {price}")
    except ValueError as error_msg:
        print(f"Validation Rejected ❌: {error_msg}")


# Test execution calls:
validate_product_price(499)
validate_product_price(-15)  # Should trigger exception error cleanly


print("\n=== End of Chapter 08 Practice Lab ===")
