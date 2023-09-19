#!/bin/bash
##
# Function to find the line that starts with "pragma solidity" and extract solidity version
extract_pragma_solidity_version() {
  while IFS= read -r line; do
    if [[ $line == "pragma solidity"* ]]; then
      version=${line#*^}  # Extract the part after the "^" symbol
      version=${version//;/}  # Remove the semicolon if present
      echo "$version"
      return
    fi
  done < "$1"
}

# Check if a folder path is provided as an argument
if [[ $# -eq 0 ]]; then
  echo "Please provide a folder path as an argument."
  exit 1
fi

folder="$1"

# Iterate through .sol files in the specified folder
for file in "$folder"/*.sol; do
  if [[ -f "$file" ]]; then
    echo "Processing file: $file"

    # Extract the Solidity version from the file
    version=$(extract_pragma_solidity_version "$file")

    # Print the version if found, or display a message if not found
    if [[ -n $version ]]; then
      echo "Solidity version found in $file: $version"
    else
      echo "No Solidity version found in $file."
    fi

    # Install the Solidity version using solc-select
    echo "Installing Solidity version $version..."
    solc-select install "$version"

    # Wait for the installation to complete
    wait

    echo "Solidity version $version has been installed."
    
    solc-select use $version 
    wait

    slither $file --print call-graph
    wait
    
  fi
done



