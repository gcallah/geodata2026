#!/usr/bin/env python3

def calculate_fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)


def main():
    while True:
        n = int(input("Enter a positive integer: "))
        # check if the input is a positive integer
        if n < 0:
            print("Please enter a positive integer.")
        else:
            result = calculate_fibonacci(n)
            print(f"The {n}th Fibonacci number is: {result}")


if __name__ == "__main__":
    main()
