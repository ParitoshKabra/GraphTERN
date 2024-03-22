import sys
import re

def parse_evaluation_results(file_content):
    # Define regular expressions for extracting relevant information
    epoch_pattern = re.compile(r'Epoch: (.+)')
    refined_ade_pattern = re.compile(r'Refined_ADE: (\d+\.\d+)')
    refined_fde_pattern = re.compile(r'Refined_FDE: (\d+\.\d+)')

    # Initialize variables to store minimum values
    min_refined_fde = float('inf')
    min_refined_ade = None
    current_epoch = None

    # Split the content into lines
    lines = file_content.split('\n')

    for line in lines:
        epoch_match = epoch_pattern.search(line)
        refined_ade_match = refined_ade_pattern.search(line)
        refined_fde_match = refined_fde_pattern.search(line)

        if epoch_match:
            current_epoch = epoch_match.group(1)
        elif refined_fde_match:
            current_refined_fde = float(refined_fde_match.group(1))

            # Update minimum values if a lower Refined_FDE is found
            if current_refined_fde < min_refined_fde:
                min_refined_fde = current_refined_fde
                min_refined_ade = float(refined_ade_match.group(1))

    return min_refined_ade, min_refined_fde

if __name__ == "__main__":
    # Check if a file name is provided as a command-line argument
    if len(sys.argv) != 2:
        print("Usage: python parse_results.py <file_name>")
        sys.exit(1)

    # Read the file name from the command line
    file_name = sys.argv[1]

    try:
        # Read the content of the file
        with open(file_name, 'r') as file:
            file_content = file.read()

        # Call the function with the file content
        min_refined_ade, min_refined_fde = parse_evaluation_results(file_content)

        # Print the results
        print(f"Minimum Refined_ADE: {min_refined_ade}, Minimum Refined_FDE: {min_refined_fde}")

    except FileNotFoundError:
        print(f"Error: File '{file_name}' not found.")
        sys.exit(1)

