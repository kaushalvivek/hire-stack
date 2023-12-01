'''
This script does the following:
- read resume
- Reads job description
- Asks an LLM to generate a score for the resume, based on some predefined parameters
- creates a output matrix, which can be used to reach out to the candidates
'''
import os
import ast
import requests
import csv
from datetime import datetime
from tqdm import tqdm
from docx import Document
from PyPDF2 import PdfReader
from langchain.chains import LLMChain
from langchain.prompts.chat import(
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from src.models import *
from src.prompts import *
from src.config import EvaluationConfig
import src.utils as utils
from src.cache import EvaluationCache

class ResumeEvaluator:
    def __init__(self, use_cache=False):
        self.run_id = datetime.now().timestamp()
        self.logger = utils.setup_logging(f"files/log/{self.run_id}.log")
        self.config = EvaluationConfig()
        self.cache = None
        if use_cache:
            self.cache = EvaluationCache()

    
    def evaluate(self):
        print("evaluating candidates ...")
        evaluations = self._get_candidate_evaluations()
        print("all evaluations done, stack ranking ...")
        sorted_candidates = self._sort_candidate_evaluations(evaluations)
        self._write_results(sorted_candidates)
        print("evaluation done, results written.")

    def _get_candidate_evaluations(self):
        evaluations = []
        resume_files = utils.get_all_files_in(self.config.resume_folder)
        for resume_file in tqdm(resume_files, desc="Processing"):
            try:
                if self.cache:
                    eval = self.cache.evaluate_with_cache(resume_file, self._evaluate_candidate_resume)
                else:
                    eval = self._evaluate_candidate_resume(resume_file)
                evaluations.append(eval)
            except Exception as e:
                self.logger.error(e, resume_file)
        return evaluations

    def _evaluate_candidate_resume(self, resume_file):
        resume_content = read_resume(resume_file)
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
        llm = ChatOpenAI(model=self.config.model)
        chain = LLMChain(llm=llm, prompt=chat_prompt)
        parser = PydanticOutputParser(pydantic_object=CandidateEvaluation)
        output = chain.run(role=self.config.role, jd=open(self.config.jd_file,"r").read(), 
            resume=resume_content, attributes=self.config.criteria)
        parsed_output = parser.parse(output)
        return str(parsed_output.model_dump()).encode('utf-8')

    def _sort_candidate_evaluations(self, evaluations):
        parsed_evals = []
        for eval_str in evaluations:
            score = 0        
            # Decode to a regular string
            decoded_str = eval_str.decode('utf-8')
            eval = ast.literal_eval(decoded_str)
            for attribute in eval["attribute_scores"]:
                for criteria in self.config.criteria:
                    if attribute["attribute"] == criteria["name"]:
                        score += attribute["score"]*criteria["weight"]
            eval["weighted_score"] = score
            parsed_evals.append(eval)
        eval_sorted = sorted(parsed_evals, key=lambda x: x["weighted_score"], reverse=True)
        return eval_sorted

    def _write_results(self, sorted_candidates):
        with open(f"files/output/output-{self.run_id}.csv", mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=sorted_candidates[0].keys())
            writer.writeheader()
            for row in sorted_candidates:
                writer.writerow(row)   
     
    
def read_resume(file_path):
    content = ""
    # Check the file extension
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    # For PDF files
    if file_extension == '.pdf':
        reader = PdfReader(file_path)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                content += text

    # For DOC/DOCX files
    elif file_extension in ['.doc', '.docx']:
        doc = Document(file_path)
        for para in doc.paragraphs:
            content += para.text + '\n'

    elif file_extension == '.txt':
        with open(file_path, 'r') as file:
            lines = file.readlines()
            # Check if it's just a link
            if len(lines) == 1 and lines[0].startswith('http'):
                response = requests.get(lines[0])
                if response.status_code == 200:
                    temp_file_path = 'temp_file'
                    with open(temp_file_path, 'wb') as f:
                        f.write(response.content)
                    content = read_resume(temp_file_path)
                    os.remove(temp_file_path)
            else:
                content = ''.join(lines)
    
    return content
