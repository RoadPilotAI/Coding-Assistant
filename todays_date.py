import datetime

# Get the current date and time
now = datetime.datetime.now()

# Format the date and time as a string
formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")

# Print the formatted date and time
print("Today's date and time is:", formatted_time)
