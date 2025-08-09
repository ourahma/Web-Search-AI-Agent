import streamlit as st
from dotenv import load_dotenv
from src.workflow import Workflow

load_dotenv()

@st.cache_resource()
def init_workflow():
    return Workflow()

workflow = init_workflow()

## app title
st.set_page_config(page_title="Developer Tools Research Agent",page_icon="🛠️",layout="wide")
st.title("🛠️ Developer Tools Research Agent")

## query input
query  = st.text_input("Enter your developer tools query : ",placeholder="e.g., Python Web Frameworks")

if st.button("Run Research"):
    if query.strip():
        with st.spinner(f"Researching tools for : {query}..."):
            result = workflow.run(query)

        st.markdown(f"📊 Results for : {query}")

        ## companies section
        if result.companies :
            for i,company in enumerate(result.companies, 1):
                with st.expander(f"{i}. 🏢 {company.name}"):
                    st.markdown(f"**🌐 Website:** {company.website}")
                    st.markdown(f"**💰 Pricing:** {company.pricing_model}")
                    st.markdown(f"**📖 Open Source:** {company.is_open_source}")

                    if company.tech_stack:
                        st.markdown(f"**🛠️ Tech Stack:** {', '.join(company.tech_stack[:5])}")

                    if company.language_support:
                        st.markdown(f"**💻 Language Support:** {', '.join(company.language_support[:5])}")

                    if company.api_available is not None:
                        api_status = "✅ Available" if company.api_available else "❌ Not Available"
                        st.markdown(f"**🔌 API:** {api_status}")

                    if company.integration_capabilities:
                        st.markdown(f"**🔗 Integrations:** {', '.join(company.integration_capabilities[:4])}")

                    if company.description and company.description != "Analysis failed":
                        st.markdown(f"**📝 Description:** {company.description}")

        else:
            st.warning("No companies found.")

        if result.analysis:
            st.markdown("## 💡Developer Recommendations ")
            st.info(result.analysis)
    else:
        st.warning("Please enter a query before running the research.")
