# HowTo

## Install

### export openai api-key

1. create `.env` file
2. put your key inside `OPENAI_API_KEY=sk-....`


### start in verual env

```
sudo apt install python3.10-venv
python3 -m venv openai-env
```

### install requierements

```
pip install -r requirements.txt
```

## Use

see additional examples in ```chat_with_data.py```

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
