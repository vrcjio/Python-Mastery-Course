# ----------------------------------------------------------------------
# Course: Python Mastery
# Chapter 07: Object-Oriented Programming (OOPs) - Lab Practice
# ----------------------------------------------------------------------

print("=== Chapter 07: Practice Lab Starting ===")

# ----------------------------------------------------------------------
# 🎯 TASK 1: Smartphone Class Construction
# Instruction: Define a class 'Smartphone' with properties: brand, model,
# and price. Initialize them inside __init__ using 'self'.
# Create a method 'show_details()' to display them cleanly.
# ----------------------------------------------------------------------
print("\n--- Task 1: Smartphone Showroom ---")

# Define your class here:


# Test Instance Creation:
# phone1 = Smartphone("Samsung", "S24 Ultra", 120000)
# phone1.show_details()


# ----------------------------------------------------------------------
# 🎯 TASK 2: Inheritance & Polymorphism (E-commerce Engine)
# Instruction: Create a base class 'Product' and inherited class
# 'DigitalProduct' that overrides 'get_price()' to inject a discount.
# ----------------------------------------------------------------------
print("\n--- Task 2: Digital Discount Calculator ---")


class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price

    def get_price(self):
        return self.price


# Inherit and override here:
class DigitalProduct(Product):
    pass  # Remove pass and write your overridden get_price logic


# Test code execution:
# item = DigitalProduct("Python Premium Course", 1000)
# print(f"Product: {item.name} | Original: 1000 | Discount Price: {item.get_price()}")


# ----------------------------------------------------------------------
# 🎯 TASK 3: Encapsulation Guard
# Instruction: Turn the balance attribute private inside the class
# structure and implement a safe deposit() method.
# ----------------------------------------------------------------------
print("\n--- Task 3: Encapsulated Vault ---")


class SecureVault:
    def __init__(self, initial_cash):
        # FIX ME: Make this variable private using __ double underscore
        self.cash = initial_cash

    def view_cash(self):
        return self.cash


# Test execution:
# vault = SecureVault(50000)
# print(f"Vault Cash Verified: {vault.view_cash()}")


print("\n=== End of Chapter 07 Practice Lab ===")
