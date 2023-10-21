# Sketch-AI

This document provides instructions for the installation and usage of Sketch-AI, an OpenAI based Project.

## Installation Guide

### Step 1: Export your OpenAI API Key

To retrieve sketch drawings based on your description, export your OpenAI API key by following these steps:

1. Go to the base directory of your project repository.
2. Create a new file `.env`.
3. Enter your OpenAI API key in the new `.env` file as shown: `OPENAI_API_KEY=sk-your-key`

### Step 2: Establish a Virtual Environment

There are two commonly used options for setting up a virtual environment - Conda and venv. These help to avoid potential conflicts between global Python environment and project-level dependencies.

#### Option 1: Creating a Virtual Environment using Conda [RECOMMENDED]

To use Conda for establishing your virtual environment, follow these steps:

1. Download Miniconda installer [here](https://docs.conda.io/projects/miniconda/en/latest/index.html) and run it to install Conda.

2. After successful installation, open a terminal and run the following commands:

    ```bash
    # Creates a new Conda virtual environment named openai-env
    conda create -n openai-env python=3.10

    # Activates the Conda virtual environment named openai-env
    conda activate openai-env
    ```

#### Option 2: Creating a Virtual Environment using venv

If you prefer using venv, follow these steps:

Open a terminal and execute the given commands to set up a virtual environment using Python3 venv:

```bash
# Installs the 'venv' module
sudo apt install python3.10-venv

# Navigate to your project's root directory
cd sketch-ai

# Creates a new venv named openai-env
python3 -m venv openai-env

# Activates the venv named openai-env
source openai-env/bin/activate
```

### Step 3: Installing the Project Dependencies

The project relies on certain Python packages that are listed in the file `requirements.txt`.

Activate your virtual environment and install these packages using pip by executing the following commands:

```bash
cd sketch-ai
pip install -r requirements.txt
```

After executing these commands, your project setup is complete.

## Usage Guide

Once the setup is complete, you can start using the project.
Sample uses of the code are available in the script `rag_llama_index.py`.

This script consists of example implementations, please refer to this script for more detailed information.

Feel free to explore and experiment with the code. If you encounter any issues, please create a new issue in the repository.
