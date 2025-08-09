from typing import Dict, Any
from langgraph.graph import StateGraph,END
from langchain_together import ChatTogether
from langchain_core.messages import HumanMessage,SystemMessage

from .firecrawl import FireCrawlService
from .models import ResearchState,CompanyAnalysis,CompanyInfo
from .prompts import DeveloperToolsPrompts

class Workflow:
    def __init__(self):
        self.firecrawl = FireCrawlService()
        self.llm = ChatTogether(model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",temperature=0.1)
        self.prompts = DeveloperToolsPrompts()
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        graph = StateGraph(ResearchState)
        graph.add_node("extract_tools",self._extract_tools_step)
        graph.add_node("research",self.research_step)
        graph.add_node("analysis",self._analyze_step)
        graph.set_entry_point("extract_tools")

        ## set the ordering
        graph.add_edge("extract_tools","research")
        graph.add_edge("research","analysis")
        graph.add_edge("analysis",END)

        return graph.compile()


    def _extract_tools_step(self, state: ResearchState) -> Dict[str, Any]:
        print(f"Finding articles about : {state.query}")

        article_query = f"{state.query} tools comparison best alternatives"
        ## use the function from our Firecrawl class to search companies
        search_results = self.firecrawl.search_companies(query=article_query,num_results=4)
        all_content = ""
        for result in search_results.data:
            ## get the returned urls
            url = result.get("url","")
            ## scrap every url , that is going to be an article
            scrapped = self.firecrawl.scrap_company_pages(url)
            if scrapped:
                all_content += scrapped.markdown[:1500]+"\n\n"
        ## create the message to let the llm extract the tools from the articles
        messages = [
            SystemMessage(content=self.prompts.TOOL_EXTRACTION_PROMPT),
            HumanMessage(content=self.prompts.tool_extraction_user(state.query,all_content)),
        ]

        try:
            response = self.llm.invoke(messages)
            tool_name = [
                name.strip()
                for name in response.content.strip().split("\n")
                if name.strip()
            ]
            print(f"Expected tools {','.join(tool_name[:5])}")
            return {"extracted_tool":tool_name}
        except Exception as e:
            print('$'*100)
            print(e)
            return {"extracted_tool":[]}



    def _analyze_company_content(self, company_name:str,content:str)->  CompanyAnalysis:
        structured_llm = self.llm.with_structured_output(CompanyAnalysis)

        messages = [
            SystemMessage(content=self.prompts.TOOL_ANALYSIS_SYSTEM),
            HumanMessage(content=self.prompts.tool_analysis_user(company_name,content))
        ]
        try:
            analysis = structured_llm.invoke(messages)
            return analysis
        except Exception as e:
            print("$"*100)
            print(e)
            return CompanyAnalysis(
                pricing_model="Unknown",
                is_open_source=None,
                tech_stack=[],
                description="Failed",
                api_available=None,
                language_support=[],
                integration_capabilities=[]
            )
    def research_step(self,state:ResearchState) -> Dict[str, Any]:
        extracted_tools = getattr(state, "_extract_tools_step", [])

        if not extracted_tools:
            print("No extracted tools found")
            search_results = self.firecrawl.search_companies(state.query, num_results=4)
            tool_names = [
                result.get("metadata",{}).get("title",'Unknown')
                for result in search_results.data
            ]
        else:
            tool_names = extracted_tools[:4]

        print(f"Researching specific tools {','.join(tool_names)}")
        companies = []
        for tool_name in tool_names:
            ## after finding the tool, look for info in their official sites
            tool_search_results = self.firecrawl.search_companies(tool_name + "official site",num_results=4)

            if tool_search_results:
                result = tool_search_results.data[0]
                url = result.get("url","")
                scrapped = self.firecrawl.scrap_company_pages(url)
                company = CompanyInfo(
                    name=tool_name,
                    description=result.get("markdown"),
                    website = url,
                    tech_stack=[],
                    competitors = []
                )
                ## scrapped the url for that website
                scrapped = self.firecrawl.scrap_company_pages(url)

                if scrapped:
                    content = scrapped.markdown
                    analysis = self._analyze_company_content(tool_name,content)

                    company.pricing_model = analysis.pricing_model
                    company.is_open_source = analysis.is_open_source
                    company.tech_stack = analysis.tech_stack
                    company.description = analysis.description
                    company.api_available = analysis.api_available
                    company.language_support = analysis.language_support
                    company.integration_capabilities = analysis.integration_capabilities

                companies.append(company)

        return {"companies":companies}

    def _analyze_step(self, state:ResearchState) -> Dict[str, Any]:
        print("Generating recommendations")

        company_data = ",".join([
            company.json() for company in state.companies
        ])

        messages =[
            SystemMessage(content=self.prompts.RECOMMENDATIONS_SYSTEM),
            HumanMessage(content=self.prompts.recommendations_user(state.query,company_data)),
        ]

        response = self.llm.invoke(messages)

        return {"analysis":response.content}

    def run(self,query:str) ->ResearchState:
        initial_state = ResearchState(query=query)
        final_state = self.workflow.invoke(initial_state)
        return ResearchState(**final_state)