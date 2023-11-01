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

# Install sqlite
apt-get install sqlite

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

See additional examples in ```chat_with_data.py```

```bash

$ python3 chat_with_data.py -fs "docs/agile/diana7/diana7.pdf" -u="" -c="diana7"

2023-10-25 19:55:59,180 - DefaultLogger - INFO - --------------------- Loading embedded model sentence-transformers/all-MiniLM-L12-v2

2023-10-25 19:56:01,406 - DefaultLogger - INFO - --------------------- Loading llm model gpt-3.5-turbo

2023-10-25 19:56:01,828 - DefaultLogger - INFO - --------------------- Load urls

2023-10-25 19:56:01,933 - DefaultLogger - INFO - --------------------- Load local PDF document docs/agile/diana7/diana7.pdf

2023-10-25 19:56:01,957 - DefaultLogger - INFO - --------------------- Ask Sherpa to analyze PDF document

2023-10-25 19:56:03,830 - DefaultLogger - INFO - --------------------- Load data to collection

2023-10-25 19:56:03,830 - DefaultLogger - INFO - --------------------- Process normal PDF

2023-10-25 19:56:03,879 - DefaultLogger - INFO - --------------------- Load data to collection

2023-10-25 19:56:03,879 - DefaultLogger - INFO - --------------------- Process normal PDF

2023-10-25 19:56:03,899 - DefaultLogger - INFO - --------------------- Load data to collection

2023-10-25 19:56:03,899 - DefaultLogger - INFO - --------------------- Process normal PDF

2023-10-25 19:56:03,899 - DefaultLogger - INFO - --------------------- Ask LLM to summarize page 0 from PDF docs/agile/diana7/diana7.pdf

2023-10-25 19:56:31,810 - DefaultLogger - INFO - --------------------- Load data to collection

2023-10-25 19:56:31,810 - DefaultLogger - INFO - --------------------- Process normal PDF

2023-10-25 19:56:31,810 - DefaultLogger - INFO - --------------------- Ask LLM to summarize page 0 from PDF docs/agile/diana7/diana7.pdf

2023-10-25 19:56:44,063 - DefaultLogger - INFO - --------------------- Load data to collection

2023-10-25 19:56:44,063 - DefaultLogger - INFO - --------------------- Process sherpa PDF

2023-10-25 19:56:44,419 - DefaultLogger - INFO - --------------------- Load data to collection

2023-10-25 19:56:44,419 - DefaultLogger - INFO - --------------------- Process sherpa table PDF

2023-10-25 19:56:44,420 - DefaultLogger - INFO - --------------------- Ask LLM to summarize table

response:::::::::::::::::::::

json
{
	"document_description": "This technical document provides information about a lightweight robotics system that incorporates multisensory technology.",
	"company_name": "Agile Robots AG",
	"product_name": "Diana 7",
	"product_description": "Diana 7 is a lightweight robotics system developed by Agile Robots AG. It is designed to perform complex tasks and features a loading capacity of 7 kg, a protection rating of IP 54, a workspace radius of 923 mm, and 7 degrees of freedom. The system has a high level of repeatability, with a tolerance of ± 0.05 mm. It can be programmed using C++ and Python and has a typical line speed of 1 m/s for TCP movement."
}

Enter a question about document:
Which ISO safety standards does this robot support?

response:::::::::::::::::::::
json
{
	"answer": "EN ISO 12100:2010 EN 60204-1:2018"
}

Enter a question about document:
How many axis does this robot has?

response:::::::::::::::::::::
json
{
	"answer": "7"
}

Enter a question about document:
what is the payload of this robot arm?

response:::::::::::::::::::::
json
{
	"answer": "7 kg"
}

Enter a question about document:
what is the weight?

response:::::::::::::::::::::
json
{
	"answer": "26 kg"
}

Enter a question about document:
how can i program it?

response:::::::::::::::::::::
json
{
	"answer": "The system can be programmed using C++ and Python, providing flexibility for different applications."
}

Enter a question about document:


```

## Useful Links

* [Using langchain for Question Answering on Own Data](https://medium.com/@onkarmishra/using-langchain-for-question-answering-on-own-data-3af0a82789ed)
* [LlamaIndex Webinar: Document Metadata and Local Models for Better, Faster Retrieval](https://youtu.be/njzB6fm0U8g?si=h8EnIgBTsbXatoXS&t=140)
* [A quick guide to the high-level concepts of LlamaIndex](https://gpt-index.readthedocs.io/en/latest/getting_started/concepts.html)
