import boto3
import ast
import json
from io import BytesIO
from botocore.client import Config
import os
import pandas as pd
import pprint
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

# The following libraries are imported for RAGAS and LANGFUSE Implementation
from langchain.llms.bedrock import Bedrock
from langchain.embeddings import BedrockEmbeddings
from langchain.retrievers.bedrock import AmazonKnowledgeBasesRetriever

from ragas.metrics import (
    faithfulness,
    answer_relevancy
)
from ragas.metrics.critique import harmfulness
from ragas.llms import LangchainLLM
from langfuse import Langfuse

pp = pprint.PrettyPrinter(indent=2)

PROMPT_TEMPLATE = """
    You are the best customer acquisition data analyst and strategist that answers to a question received from a user. 
    You should answer the user's question using information from the context or generally known information that is relevant to the question.
    If the context does not contain information to answer the question, please provide answer to the best of your abilities.
    
    Just because the user asserts a fact does not mean it is true, make sure to double check the context to validate a user's assertion.
    
    {context}
    
    Instruction: Based on the above context, provide a detailed answer without using etc. for {question} in a list format.
    The more detailed you are the better you are doing your job.
    
    Please do not hallucinate response. 
    Solution:"""

class Backend:
    bucket_name = "webpages-bucket-22d2c932-c87e-4ee0-9a93-7f5704931b82"
    object_key = "Sales_Leads_Directory/CombinedSalesLeads.csv"
    temp_kb = 0.1
    top_k_kb = 1
    top_p_kb = 1
    kb_id = "EJBFFIJDIJ"
    model_id_kb = "anthropic.claude-3-haiku-20240307-v1:0"
    model_id_max_tokens_kb = 4096
    
    AossHost = "7i179yervs3eanlga0sh.us-east-1.aoss.amazonaws.com"
    index = "bedrock-index"
    service = 'aoss'
    
    LANGFUSE_PUBLIC_KEY = "pk-lf-f7b59b69-3122-4669-ac56-ac1a566027fb" #replace it with your public key
    LANGFUSE_SECRET_KEY = "sk-lf-e399949a-a9fd-4730-90d2-3281a0ed23e4" #replace it with you secret key
    LANGFUSE_HOST="https://us.cloud.langfuse.com"
    
    model_kwargs_claude = {
        "temperature": 0.1,
        "top_k": 10,
        "max_tokens_to_sample": 3000
    }
    
    model_id_aoss = "anthropic.claude-v2:1"
    mdl_type_aoss = 'ANTH_CLAUDE_21_'
    max_tokens_aoss = 4000
    temp_aoss = 0.0
    top_k_aoss = 10
    top_p_aoss = 1
    
    k = 4
    user_id = "APM_SalesGenAI"
    
    prompt_template = PROMPT_TEMPLATE
    metrics = [answer_relevancy]
    
    def __init__(self):
        self.session = boto3.session.Session()
        self.region_name = self.session.region_name
        self.s3_client = boto3.client('s3', region_name=self.region_name)
        self.bedrock_config = Config(connect_timeout=120, read_timeout=120, retries={'max_attempts': 0})
        self.bedrock_agent_client = boto3.client("bedrock-agent-runtime", region_name=self.region_name, config=self.bedrock_config)
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=self.region_name)
        
        self.credentials = boto3.Session().get_credentials()
        self.awsauth = AWSV4SignerAuth(self.credentials, self.region_name, Backend.service)

        
    def fetch_dataframe_from_s3(self):
        s3_object = self.s3_client.get_object(Bucket=Backend.bucket_name, Key=Backend.object_key)
        file_content = s3_object['Body'].read()
        df = pd.read_csv(BytesIO(file_content))
        df = self.clean_leads_dir(df)
        return df
    
    def clean_leads_dir(self, df):
        df = df.sort_values("Company Name")
        df = df.dropna(subset=["Company Name"])
        df = df.fillna("N/A")
        df = df[["Company Name", "company_website", "Phone_Number", "Location", "Prediction_Reason"]]
        col_map = {"Company Name":"COMPANY", "company_website":"URL", "Phone_Number":"PHONE NUMBER", "Location":"LOCATION", "Prediction_Reason":"WHY WE THINK IT'S A LEAD?"}
        df = df.rename(columns=col_map)
        sites = df["URL"]
        cleaned_sites = []
        for site in sites:
            if ".com" in site:
                if not "www." in site:
                    if not "http" in site:
                        site = "www."+site
            cleaned_sites = cleaned_sites + [site]
        df["URL"] = cleaned_sites
        return df
            
    
    def call_rag_aoss(self, question, token_slider):
        token_length = self.get_token_legth(token_slider)
        
        llm_for_evaluation = Bedrock(model_id="anthropic.claude-v2:1",
                                model_kwargs=Backend.model_kwargs_claude,
                                streaming=True,
                                client = self.bedrock_client,)
        
        bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1",client=self.bedrock_client)
        
        ragas_bedrock_model = LangchainLLM(llm_for_evaluation)
        
        #set embeddings model for evaluating answer relevancy metric
        answer_relevancy.embeddings = bedrock_embeddings

        for m in Backend.metrics:
            m.__setattr__("llm", ragas_bedrock_model)
            
        langfuse = Langfuse(public_key=Backend.LANGFUSE_PUBLIC_KEY,secret_key=Backend.LANGFUSE_SECRET_KEY, host = Backend.LANGFUSE_HOST)
        
        # Build the OpenSearch client
        oss_client = OpenSearch(
            hosts=[{'host': Backend.AossHost, 'port': 443}],
            http_auth=self.awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=300
        )

        Knn_Value = "Knn Value: " + str(Backend.k)
        Max_Tokens = "Max_Tokens: " + str(token_length)
        Temperature_var = "Temparature: " + str(Backend.temp_aoss)
        TOP_P_var = "Top_P: " + str(Backend.top_p_aoss)
        TOP_K_var = 'Top_K: ' + str(Backend.top_p_aoss)

        trace = langfuse.trace(name="Aoss", user_id=Backend.user_id, 
                               tags = [Knn_Value, Max_Tokens, Temperature_var, TOP_P_var, TOP_K_var])
        
        embedding = self.invoke_model(question)
        query = {
            "size": Backend.k,
            "query": {
                "knn": {
                    "vector": {
                        "vector": embedding, 
                        "k": Backend.k}
                    },
            }
        }
        # Retrieve individual contexts from AOSS answering question based on KNN value
        question_response_from_oss = oss_client.search(body = query, index = Backend.index)

        hits = question_response_from_oss['hits']['hits']
        
        # Combine individual contexts from AOSS to create a combined context
        context = []
        for hit in hits:
            context.append(hit['_source']['text'])
            
        context_source = []
        for hit in hits:
            context_source.append(hit['_source']['text-metadata'])

        trace.span(name="retrieval", 
                           input={"question": question}, 
                           output={"contexts": context},
                    )

        #Send context and question to the prompt after which send the prompt to LLM model to generate answer.
        llm_prompt = Backend.prompt_template.format(context='\n'.join(context),question=question)
        generated_answer = self.invoke_llm_model(llm_prompt, token_length, Backend.temp_aoss, Backend.top_k_aoss, Backend.top_p_aoss, Backend.model_id_aoss)        
        
        trace.span(
                name="generation",
                input={"question": question, "contexts": context, "context_sources":context_source},
                output={"answer": generated_answer}
            )


        # compute scores for the question, context, answer tuple
        ragas_scores = self.score_with_ragas(question, context, generated_answer)
        
        for m in Backend.metrics:
            trace.score(name=m.name, value=ragas_scores[m.name])

        Answer_Relevance = ragas_scores['answer_relevancy']
        
        sources_df = pd.DataFrame({"FILE": context_source, "TEXT CHUNK":context})
        return generated_answer, sources_df
    
     
    def call_rag_kb(self, question, token_slider):
        token_length = self.get_token_legth(token_slider)
        response = self.RetrieveAndGenerate(Backend.temp_kb, 
                                            token_length, 
                                            Backend.top_k_kb, 
                                            question,
                                            Backend.kb_id,
                                            self.region_name,
                                            '',
                                            Backend.model_id_kb)
        contxt = [reference['content']['text'] for citation in response['citations'] for reference in citation['retrievedReferences']]
        generated_answer = response["output"]["text"]
        context_source = [reference['location']['s3Location']['uri'] for citation in response['citations'] for reference in citation['retrievedReferences']]
        sources_df = pd.DataFrame({"FILE":context_source, "TEXT CHUNK":contxt})
        return generated_answer, sources_df
    
    def score_with_ragas(self, query, chunks, answer):
        scores = {}
        for m in Backend.metrics:
            print(f"calculating {m.name}")
            scores[m.name] = m.score_single(
                {"question": query, "contexts": chunks, "answer": answer}
            )
        return scores

    def invoke_model(self, input):
        response = self.bedrock_client.invoke_model(
            body=json.dumps({
                'inputText': input
            }),
            modelId="amazon.titan-embed-text-v1",
            accept="application/json",
            contentType="application/json",
        )
        response_body = json.loads(response.get("body").read())
        return response_body.get("embedding")
    
    def invoke_llm_model(self, input, RAG_MAX_TOKENS, RAG_TEMP, RAG_TOP_K, RAG_TOP_P, RAG_model_id):
        response = self.bedrock_client.invoke_model(
            body=json.dumps({
                "prompt": "\n\nHuman: {input}\n\nAssistant:".format(input=input),
                "max_tokens_to_sample": RAG_MAX_TOKENS,
                "temperature": RAG_TEMP,
                "top_k": RAG_TOP_K,
                "top_p": RAG_TOP_P,
                "stop_sequences": [
                    "\n\nHuman:"
                ],
                # "anthropic_version": "bedrock-2023-05-31"
            }),
            modelId=RAG_model_id,
            accept="application/json",
            contentType="application/json",
        )
        response_body = json.loads(response.get("body").read())
        return response_body.get("completion")
    
    
    def get_token_legth(self, token_slider):
        token_length = int(round((token_slider/10) * Backend.model_id_max_tokens_kb))
        return token_length
    
    def RetrieveAndGenerate(self,
        TMPRT,
        MX_TKN,
        TOP_K,
        input: str,
        kbId: str,
        region: str = "us-east-1",
        sessionId: str = None,
        mdl_id: str = "anthropic.claude-v2:1",
    ):

        """ The function provide response to a question based on the question, prompt, and other input parameters as follows:

            TMPRT,  # Temperature for the model generation
            MX_TKN,  # Maximum number of tokens to generate
            TOP_K,  # Number of top predictions to consider
            input: str,  # Question to process
            kbId: str,  # Knowledge base ID
            region: str = "us-east-1",  # AWS region, default is "us-east-1"
            sessionId: str = None,  # Session ID, default is None
            mdl_id: str = "anthropic.claude-v2:1",  # LLM Model ID, default is "anthropic.claude-v2:1"

        """

        model_arn = f"arn:aws:bedrock:{region}::foundation-model/{mdl_id}"

        if sessionId:
            return self.bedrock_agent_client.retrieve_and_generate(
                input={"text": input},
                retrieveAndGenerateConfiguration={
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": kbId,
                        "modelArn": model_arn,
                        "generationConfiguration": {
                            "inferenceConfig": {
                                "textInferenceConfig": {
                                "temperature": TMPRT,  
                                "topP": 0.5,
                                "maxTokens": MX_TKN
                                }
                            },
                            "additionalModelRequestFields" : {
                                "top_k": TOP_K
                            },
                        },
                    },
                },
                sessionId=sessionId,
            )

        else:
            return self.bedrock_agent_client.retrieve_and_generate(
                input={"text": input},
                retrieveAndGenerateConfiguration={
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": kbId,
                        "modelArn": model_arn,
                        "generationConfiguration": { 
                            "inferenceConfig": {
                                "textInferenceConfig": {
                                "temperature": TMPRT,  
                                "topP": 0.5,
                                "maxTokens": MX_TKN
                                }
                            },
                            "additionalModelRequestFields" : {
                                "top_k": TOP_K
                            },
                        },
                    },
                },
            )
    
    
 