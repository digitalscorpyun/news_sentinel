# Function to add a task
def add_task(task_file, task):
    with open(task_file, "a") as file:
        file.write(f"{task},Incomplete\n")
    print(f"Task '{task}' added.")

# Function to view tasks
def view_tasks(task_file):
    print("Your tasks:")
    with open(task_file, "r") as file:
        for line in file:
            task, status = line.strip().split(",")
            print(f"- {task} [{status}]")

# Function to mark a task as completed
def complete_task(task_file, task_to_complete):
    tasks = []
    with open(task_file, "r") as file:
        for line in file:
            task, status = line.strip().split(",")
            if task == task_to_complete:
                tasks.append(f"{task},Complete\n")
            else:
                tasks.append(line)

    with open(task_file, "w") as file:
        file.writelines(tasks)

    print(f"Task '{task_to_complete}' marked as completed.")

# Main program logic
task_file = "tasks.txt"

while True:
    print("\nTask Tracker")
    print("1. Add Task")
    print("2. View Tasks")
    print("3. Complete Task")
    print("4. Exit")

    choice = input("Choose an option: ")

    if choice == "1":
        task = input("Enter the task: ")
        add_task(task_file, task)
    elif choice == "2":
        view_tasks(task_file)
    elif choice == "3":
        task_to_complete = input("Enter the task to mark as completed: ")
        complete_task(task_file, task_to_complete)
    elif choice == "4":
        print("Goodbye!")
        break
    else:
        print("Invalid choice. Please try again.")
