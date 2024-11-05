# ArgRes: Reasoning in LLMs for Clinical Decision Making

## Overview
ArgRes introduces a multi-agent system with an expert system-inspired architecture designed to enhance clinical decision-making. In this system, LLMs act as expert and judge agents. The Creator agent analyzes the task and generates expert agents based on keywords extracted using MeSH. The Reasoner Agent formulates arguments related to the posed question, efficiently utilizing Retrieval-Augmented Generation (RAG) to access relevant sources. These arguments are evaluated by Domain Expert Agents, and an Argument-Reasoning tuple is sent to the Judge agent. Using autoepistemic logic, the Judge evaluates the consistency of the arguments, iterating the process until a conclusion is reached.
 
## Motivation
Reasoning in LLMs has been a task sought after. While LLMs do not inherently possess the ability to reason, they can act as natural language interpreters that we could utilize to create reasoning machines. The critical problems with LLMs are their lack of contextual knowledge, inability to discern uncertainty in knowledge, and drawing logical and consistent conclusions. As a result, LLMs hallucinate, show bias, and are unable to handle complex tasks. This architecture aims to tackle these shortcomings, specifically toward a domain specific field such as Clinical Decision Making. 

## Methodology
**Creator Agent** : Takes user input of the clinical case (questions from MedQA or PubMedQA) and creates relevant Domain Expert Agents. 
   ** MeSH Keyword extraction :** The pipeline begins by parsing the clinical query to extract biomedical entities using BioNER. Extracted entities that match entry terms of suggested MeSH terms are mapped to those terms, ensuring consistent terminology and accurate topic representation via the MeSH RDF. This helps the         Creator in building a targeted prompt for the Expert agents. 
**Reasoner Agent :** Considers the clinical query present and arrives at an argument list that is required to take a decision regarding the input question. These arguments are independent assumptions of the possibilities. 
      **Retrieval Augmented Generation :** Using the BioASQ 9a dataset, PubMed articles are tagged with MeSH keywords. The keywords extracted in the previous step are used to filter articles to create embeddings. These embeddings facilitate accurate similarity-based retrieval, used by the reasoner agent to refine its arguments
**Domain Experts :** With zero-shot setting, these agents are set to be experts which evaluate each of the Reasoner’s arguments on the basis of their expertise. They return a tuple (Argument, Expert, Support, Reasoning) known as the Argument-Reasoning Tuple. 
**Judge Agent :** The Judge agent evaluates the Argument-Reasoning Tuple based on the qualification of the expert to make a claim and the soundness of reasoning. 
      If the Judge finds inconsistencies, or unsound reasons, the process is iterated through the reasoner again, till convergence.
      Autoepistemic Logic : Autoepistemic logic is a form of non-monotonic logic that allows a system to reason about its own knowledge and beliefs. Autoepistemic logic works particularly well for the Judge agent in this context because it enables the agent to evaluate the consistency and soundness of presented arguments and reasonings by reflecting on its own knowledge base.


## Dataset and metrics:
    The MedQA dataset is a comprehensive benchmark of clinical questions and answers from actual medical 
exams. It offers a strong tool for training and assessing our model's comprehension of intricate medical
questions, evaluation of pertinent data, and production of precise clinical reasoning outputs grounded in
in-depth medical knowledge.

Our criteria for evaluation of this system is on the following metrics
    Accuracy (ACC): Measures alignment of outputs with benchmark datasets like MedQA for reliable decision-making.
    Organization (ORG): Assesses the clarity and accessibility of clinical evidence.
    Succinctness (SCI): Ensures Reasoner outputs are brief and non-redundant.
    Consistency (CNS): Confirms mutual support and absence of contradictions in information.
    Free from Hallucination (FFH): Evaluates information verifiability based on established guidelines.
    
## Architecture
![MAS (1)](https://github.com/user-attachments/assets/d99e211e-a123-4ba3-9a39-98e97db724b8)

## Tech Stack
Multi Agent system - CrewAI, LangChain tools, LangChain

LLM - Gemini API (Free tier : gemini-pro, gemini-flash-1.5)

MeSH Keyword extraction - Spacy, Bio_Epidemiology_NER (For medical Named entity recognition), Entrez (BioPython library for accessing NCBI's E-utilities.)

Autoepistemic Logic - To fully integrate autoepistemic logic, we are writing our own module to aid the Judge agent in decision making


