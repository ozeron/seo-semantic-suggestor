from collections import Counter

with open('out.md', 'r') as file:
    lines = file.read().split('\n\n')  # Split the file into chunks at each double newline

counter = Counter(lines)  # Count the occurrences of each chunk

# Print chunks that occur more than once
for chunk, count in counter.items():
    if count > 1:
        print(f'Chunk occurs {count} times:\n{chunk}\n')
