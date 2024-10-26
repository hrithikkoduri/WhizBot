from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.vectorstores import DeepLake
import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import (
    create_history_aware_retriever,
    create_retrieval_chain,
)
from langchain_core.messages import HumanMessage, AIMessage



load_dotenv()
CALENDLY_LINK = os.getenv('CALENDLY_LINK', 'https://calendly.com/hrithikkoduri18/30min')
openai_api_key = os.getenv("OPENAI_API_KEY")

class Output:
    def __init__(self, db):
        
        self.db = db
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.retriever = self.db.as_retriever()
        self.retriever.search_kwargs['fetch_k'] = 100
        self.retriever.search_kwargs['k'] = 10
        self.chat_history = []

        self.prompt_search_query = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            ("user", "Given the above conversation, generate a search query to look up to get information relevant to the conversation"),
        ])
        
        self.retriever_chain = create_history_aware_retriever(self.llm, self.retriever, self.prompt_search_query)


        self.system_message = '''   
            You are an AI customer service assistant designed to help users understand and interact with our company’s services and products. Your primary role is to answer questions based on the information extracted from our knowledge base, which includes policies, product details, and customer support procedures.

            For the context of the conversation, you can use this {context}.

            If no question is asked, offer a brief overview of our company’s services and suggest possible questions related to our offerings, support, and general inquiries. If you don't know the answer, ask the user to be more specific. If the question is not related to our services, request a relevant question.

            When asked for specific policies or procedures, provide exact information as it appears in our knowledge base; do not generate or summarize details on your own.

            Your goals are to:

            - Answer questions related to our company’s services and products.
            - Provide relevant details, policies, and procedures as needed.
            - Offer guidance on navigating our services and accessing support.
            - Assist with common inquiries about service offerings, account management, and procedures.
            
            Behavior Guidelines:

            - Be helpful, friendly, and concise.
            - Provide accurate information and explanations when requested.
            - Focus solely on the information available in the knowledge base context.
            - If a question is anything not relevant simply ask questions relevant to the company.
            - Use simple language to ensure clarity, avoiding technical jargon unless necessary.
        
        '''

        self.prompt_get_answer = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            ("user", "Given the above conversation, generate an answer to the user's question.")
        ])

        self. document_chain= create_stuff_documents_chain(self.llm, self.prompt_get_answer)
        self.retrieval_chain = create_retrieval_chain(self.retriever_chain, self.document_chain)
        


    #def chat(self, question, chat_history):
    def chat(self, question):
        
        print("Entered chat function")
        print("-------------------")
        print("Question inside function:",question)
        print("-------------------")
        print("Chat History inside function:",self.chat_history)

        response = self.retrieval_chain.invoke(
            {"input": question, "chat_history": self.chat_history}
        )
        print("-------------------")
        print( "Context:",response['context'])
        print("-------------------")
        self.chat_history.append(HumanMessage(question))
        self.chat_history.append(AIMessage(response['answer']))

        self.chat_history = self.chat_history[-6:]

        json_response = {
            "response": response['answer'],
            "chat_history": self.chat_history
        }
        return json_response["response"]
    
    def update_chat_history(self, self_message):
        self.chat_history.append(AIMessage(self_message))
        self.chat_history = self.chat_history[-6:]
        print("-------------------")
        print("Chat History after broadcast message:",self.chat_history)

    def schedule_meeting(self):

        response = f"You can schedule a meeting with me using this link: {CALENDLY_LINK}\n\nPlease select a time that works best for you."
        self.update_chat_history(response)

        return response


def main():
    output = Output()
    question = "What kind of benefits do you offer?"
    response = output.chat(question)
    print("Response:",response['response'])
    print("Chat History:",response['chat_history'])

    print("-------------------")
    question = "How do I go about the installation process?"
    response = output.chat(question)
    print("Response:",response['response'])
    print("Chat History:",response['chat_history'])

    

if __name__ == "__main__":
    main()