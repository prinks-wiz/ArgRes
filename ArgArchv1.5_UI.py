###### Imports 
import os
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from pydantic import BaseModel
from typing import List
import streamlit as st
from crewai import Agent, Task, Crew, Process
from crewai_tools import tool
import random
from time import sleep
import asyncio
# Replace with your Gemini API key
my_api_key = "AIzaSyB_lwJ9J-X1JHuJosy2d41F2OqrlGq3bJY"

os.environ["GOOGLE_API_KEY"] = my_api_key

genai.configure(api_key=my_api_key)


#### DATA LOADING
import json

def load_medqa_data(file_path):
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return data

# Example usage:
medqa_data = load_medqa_data('/Users/prinks/Downloads/MedQA-USMLE/questions/US/metamap_extracted_phrases/train/phrases_train.jsonl')
for entry in medqa_data[:5]:  # Display first 5 entries
    print(entry)


st.title("Clinical Decision Making using Multi Agent LLMs")
st.markdown("##### This multiagent system uses three core agents : Creator, Reasoner, Judge.")
st.text("#### Functionalities : Agent creation, Simple CoT based Reasoning accross three agents, Automated calling of tools")
st.header("Dataset Description")
st.text("For the current implementation run, we are using the MedQA dataset. You are free to choose any question from below, or select random")

st.markdown("### Questions")

flag = 0


if st.checkbox("Enable random question selection",key = 'random'):
        num = random.randint(1,len(medqa_data))
        selected_dict = medqa_data[num]
        st.write(f"The question is {selected_dict['question']}")
        flag = 1
else:
        choices = [medqa_data[32],medqa_data[15],medqa_data[17],medqa_data[33],medqa_data[5]]
        question_to_dict = {choice['question']: choice for choice in choices}
        selected_question = st.selectbox("Select a question:", list(question_to_dict.keys()),index = None, key="radio")

        # Retrieve the full dictionary based on the selected question
        selected_dict = question_to_dict[selected_question]
        if selected_question:
            flag = 1

if flag == 1 :
        question = selected_dict['question']
        options = selected_dict['options']
        answer = selected_dict['answer_idx']

        st.text("Starting the multiagent system....")
        sleep(2)
        ###PYDANTIC MODELS
        from pydantic import BaseModel
        from typing import List
        class TaskResponse(BaseModel):
            Role : str
            Argument : str
            Support : bool
            Reason : str

        class AllResponse(BaseModel):
            TaskResponses : List[TaskResponse]

        class CreatorResponse(BaseModel):
            experts : List[str]

        class ReasonerResponse(BaseModel):
            Agruements : List[str]


        #### ============================================================AGENTS 
        ## HELPER FUNCTIONS
        def domain_expert_creation(domain_experts_str:str)->list:
            '''This tool is to be used by the Creator Agent to create 5 domain expert agents from the list of domain experts given'''
            domain_experts=eval(domain_experts_str)
            created_agents = []
        
            for domain in domain_experts['Domains']:
                expert = Agent(
                    role=f"{domain} Expert",
                    goal=f"You are a medical expert in the domain of {domain}. You must assess the question and the arguments, and make a decision",
                    backstory=f"From your area of specializationm in {domain}, you will scrutinize and diagnose the symptoms presented by patients in regard to the arguments given. You must decide whether you are in support of the argument or not, and provide a reasoning for your decision based on only your expertise.",
                    verbose=True,
                    memory=True,
                    llm=ChatGoogleGenerativeAI(model="gemini-pro"),
                )
                created_agents.append(expert)
            return created_agents,domain_experts
        def task_mapping(domain_expert_agents, reasoner_output):
            temp = eval(reasoner_output)
            reasoner_task = temp["Arguments"]
            domain_expert_to_tasks = []
            for expert in domain_expert_agents:
                domain_expert_to_tasks.append((expert,Task(description=f'Assess each argument in this list {reasoner_task}\n, with regard to the question "{question} and the following options {options} one of which is correct"\n. Now decide if the argument is true or false. Provide reasoning to your decision which explains why you took that decision as you would to a patient being an expert in your field. If the argument is outside your field, state as such and do not comment on the argument. ',
                                                expected_output='Role specifies your own role is of string type . Argument is the one given to you and is of string type. support is either 0 or 1 based on if you support it or not. Reason is your explanation for your support and is of string type.Your output must be a pydantic output of the format : {"Responses":[{"Role":"_your_role_", "Argument":"_given_argument","Support":0/1,"Reasoning":"res1"},{"Role":"_your_role_", "Argument":"_given_argument","Support":0/1,"Reasoning":"res2"},.......,{"Role":"_your_role_", "Arguemnt":"_given_arguemnt","Support":0/1,"Reasoning":"resN"}]} and nothing else',
                                                prompt_context='Your output will be used further in python code. So avoid syntax errors such as unterminated strings and parenthesis',agent = expert)
                                                ))
                
            return domain_expert_to_tasks

        def expert_task_execution(domain_expert_tasks):
            arg_res = []
            for agent,task in domain_expert_tasks:
                output = agent.execute_task(task)
                arg_res.append(output)
            return arg_res
        ##==================Creator 
        st.markdown("#### CREATOR AGENT STARTING")
        creator_backstory  = f'''You have to identify 5 domain experts needed to make a decision on the {question} presented to you.'''
        creator_agent = Agent(
            role='Creator Agent',
            goal='Identify domains and domain expert agents',
            verbose=True,
            memory=True,
            llm=ChatGoogleGenerativeAI(model="gemini-pro"),
            backstory= creator_backstory)

        creator_task = Task(
            description='Identify domains from the question and list domains.',
            expected_output = 'a pydantic  output for a list of domain experts as follows : {"Domains" : ["expert1", "expert2","expert3", "expert4","expert5"]} and no other text' ,
            output_pydantic=CreatorResponse,
            agent=creator_agent,
            
        )


        ##----------pipeline Creator
        creator_output= creator_agent.execute_task(creator_task)
        domain_expert_agents,domain_expert_fields = domain_expert_creation(creator_output)
        st.text(creator_output)
        #------------pipline end
        #==============================REASONER AGENT 
        st.markdown("#### REASONER AGENT STARTING")
        Reasoner_backstory = f'You are adept at understanding the given medical scenario presented and must arrive at possible medical arguments for the question. You  must comprehend the question well enough to arrive at a diverse set of perspectives as would be given by experts {domain_expert_fields}, but need not classify which expert arrives at what reasoning. No more than 10 arguments must be presented. This is your question {question} and options {options}'
        reasoner_agent = Agent(
            role='Reasoner Agent',
            goal='Generate possible reasonings to answer the question in the form of a python list.',
            verbose=True,
            memory=True,
            llm=ChatGoogleGenerativeAI(model="gemini-pro"),
            backstory=Reasoner_backstory,
        )

        reasoner_task = Task(
            description = 'Understand the question presented and arrive at various arguments from different perspectives',
            expected_output='A pydantic list of all the arguments arrived at in the pydantic format with no apostrophes : {"Arguments": ["arg1", "arg2",.....,"argN"]} and nothing else',
            prompt_context='Your output will be used further in python code. So avoid syntax errors such as unterminated strings and parenthesis',
            agent = reasoner_agent
            
        )

        #-----------pipeline Reasoner
        reasoner_output= reasoner_agent.execute_task(reasoner_task)
        st.text(reasoner_output)
        domain_expert_to_tasks = task_mapping(domain_expert_agents,reasoner_output)
        arg_res = expert_task_execution(domain_expert_to_tasks)

        #-------------pipeline end
        #----------Printing Domain Experts
        for i in range(len(arg_res)):
            arg_res[i] = eval(arg_res[i])
        st.markdown("#### Domain Experts Evaluation")
        ##The Domain Experts are ready 
        for response in arg_res:
            lst = response['Responses']
            role = lst[0]['Role']
            st.markdown(f"##### {role} says")
            for i in range(len(lst)):
                argument = lst[i]['Argument']
                support = lst[i]["Support"]
                sup = lambda x,support : x =="yes" if support=="1" else "no"
                reason = lst[i]["Reasoning"]
                st.write(f"Argument : {argument}")
                st.write(f"Supporting : {support}")
                st.write(f"Because : {reason}")




        #=================JUDGE AGENT
        st.markdown("#### JUDGE AGENT STARTING")
        judge_agent = Agent(
            role='Judge Agent',
            goal='Evaluate the experts feedback  and finalize the best reasoning',
            verbose=True,
            memory=True,
            llm=ChatGoogleGenerativeAI(model="gemini-pro"),
            backstory="You make the final decision on the best reasoning and pick the correct option.You must evaluate on the following basis : The reasoning is sound and follows from the argument, and the expert making the reasoning is qualified to do do. If the expert is not wqualified, do not accept the argument and reasoning. If there are opposing views on an argument, either pick the expert who has greater qualification to that view and if that doesn't work, disqualify the argument reasoning from both. In case of multiple arguments being viable, choose the one that is voiched for by maximum experts. If there is a tie there as well, utilize commonsense reasoning to pick the most likely solution."
        )


        judge_task = Task(description=f"Analyze the list of arguments and reasoning given for a particular question and arrive at a conclusion.This is the question : \n {question}\n  here is your list of arguments and reasoning :\n {str(arg_res)} ",
                        expected_output=f"Conclusion to the question with apt reasoning for answer, attributing to which experts led to this choice. Pick an option out of {options} that fits best ")

        #----------------pipeline Judge
        conclusion = judge_agent.execute_task(judge_task)

        st.text(conclusion)
        st.markdown("#### Actual Answer")
        st.text(f"The correct answer is option {answer} among {options}")
        print(answer)
        print(options)
        print(conclusion)


        st.write("THANK YOU")
        #------------------------------------------------------------------------------------------------------------------------------------------
        #---------------------------------------------------------------------------------------------------------------------------------------------------
        #---------------------------------------------------------------------------------------------------------------------------------------------------d
else: 
     pass

