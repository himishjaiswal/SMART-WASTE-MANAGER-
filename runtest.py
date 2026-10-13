import subprocess

# the input for the C program, same format as test.txt
input_text = """FCFS
2
4
1 0 8 2
2 1 4 3
3 2 2 1
4 3 1 2
"""

# run scheduler.exe and give it the input
result = subprocess.run(["scheduler/scheduler.exe"],
                        input=input_text,
                        capture_output=True,
                        text=True)

print("Output from C program:")
print(result.stdout)