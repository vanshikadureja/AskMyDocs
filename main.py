import os
import fitz
import streamlit as st
from dotenv import load_dotenv

from openai import AzureOpenAI

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
)

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="AskMyDocs AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

html,body,[class*="css"]{
    font-family:Poppins,sans-serif;
}

.stApp{
background:linear-gradient(135deg,#eef2ff,#ffffff);
}

/* Hero */

.hero{
padding:40px;
border-radius:25px;
background:linear-gradient(135deg,#4F46E5,#7C3AED);
color:white;
text-align:center;
margin-bottom:25px;
box-shadow:0 15px 40px rgba(0,0,0,.18);
}

.hero h1{
font-size:52px;
margin-bottom:10px;
}

.hero p{
font-size:18px;
opacity:.95;
}

/* Upload Card */

.upload-box{
background:white;
padding:25px;
border-radius:20px;
box-shadow:0 8px 30px rgba(0,0,0,.08);
margin-bottom:20px;
}

/* Answer Card */

.answer{
background:white;
padding:25px;
border-radius:18px;
border-left:7px solid #4F46E5;
box-shadow:0 10px 25px rgba(0,0,0,.08);
}

/* Sidebar */

section[data-testid="stSidebar"]{
background:#111827;
}

section[data-testid="stSidebar"] *{
color:white;
}

/* Buttons */

.stButton>button{
width:100%;
height:55px;
border:none;
border-radius:14px;
background:linear-gradient(135deg,#4F46E5,#7C3AED);
color:white;
font-size:18px;
font-weight:600;
transition:.3s;
}

.stButton>button:hover{
transform:translateY(-2px);
box-shadow:0 8px 20px rgba(79,70,229,.35);
}

/* Input */

.stTextInput input{
border-radius:12px;
}

/* File Uploader */

section[data-testid="stFileUploader"]{
border:2px dashed #4F46E5;
padding:20px;
border-radius:18px;
background:#f8f9ff;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# LOAD ENV
# ---------------------------------------------------

load_dotenv()

search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
search_key = os.getenv("AZURE_SEARCH_KEY")
index_name = os.getenv("AZURE_SEARCH_INDEX")

openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

with st.sidebar:

    st.image(
        "https://img.icons8.com/fluency/96/artificial-intelligence.png",
        width=80,
    )

    st.title("AskMyDocs AI")

    st.markdown("---")

    st.markdown("### 🚀 Features")

    st.success("📄 PDF Upload")
    st.success("🔍 Azure AI Search")
    st.success("🤖 Azure OpenAI")
    st.success("⚡ Instant Answers")

    st.markdown("---")

    st.info(
        """
Built with

• Streamlit

• Azure AI Search

• Azure OpenAI

• PyMuPDF
"""
    )

# ---------------------------------------------------
# HERO
# ---------------------------------------------------

st.markdown("""
<div class="hero">

<h1>🤖 AskMyDocs AI</h1>

<p>
Upload your PDF • Search intelligently • Ask questions instantly
</p>

</div>
""", unsafe_allow_html=True)
# ---------------------------------------------------
# CREATE SEARCH INDEX
# ---------------------------------------------------

def create_index():

    index_client = SearchIndexClient(
        endpoint=search_endpoint,
        credential=AzureKeyCredential(search_key)
    )

    fields = [
        SimpleField(
            name="id",
            type="Edm.String",
            key=True
        ),
        SearchableField(
            name="content",
            type="Edm.String"
        )
    ]

    index = SearchIndex(
        name=index_name,
        fields=fields
    )

    index_client.create_or_update_index(index)


if "index_created" not in st.session_state:

    with st.spinner("⚙️ Preparing Azure AI Search..."):

        try:
            create_index()
        except Exception:
            pass

        st.session_state.index_created = True


# ---------------------------------------------------
# UPLOAD SECTION
# ---------------------------------------------------

st.markdown("## 📂 Upload Your Document")

st.markdown("""
<div class="upload-box">

<h3>📄 Drag & Drop your PDF</h3>

<p>
Upload any PDF and start chatting with your document using Azure AI.
</p>

</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "",
    type=["pdf"],
    label_visibility="collapsed"
)

# ---------------------------------------------------
# PROCESS PDF
# ---------------------------------------------------

if uploaded_file:

    with st.spinner("📖 Reading PDF..."):

        pdf = fitz.open(
            stream=uploaded_file.read(),
            filetype="pdf"
        )

        text = ""

        for page in pdf:
            text += page.get_text()

        pdf.close()

    # -----------------------------

    chunks = [
        text[i:i+1000]
        for i in range(0, len(text), 1000)
    ]

    # -----------------------------

    progress = st.progress(0)

    for i in range(100):
        progress.progress(i + 1)

    st.success("✅ Document processed successfully!")

    # -----------------------------

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "📄 Pages",
        len(fitz.open(stream=text.encode(), filetype="txt")) if False else "✓"
    )

    col2.metric(
        "📚 Chunks",
        len(chunks)
    )

    col3.metric(
        "📁 File",
        uploaded_file.name
    )

    st.divider()

    # ---------------------------------------------------

    search_client = SearchClient(
        endpoint=search_endpoint,
        index_name=index_name,
        credential=AzureKeyCredential(search_key)
    )

    documents = [
        {
            "id": str(i),
            "content": chunk
        }
        for i, chunk in enumerate(chunks)
    ]

    with st.spinner("☁️ Uploading to Azure AI Search..."):

        search_client.upload_documents(documents)

    st.success(
        f"🎉 Successfully indexed {len(chunks)} document chunks!"
    )

    st.markdown("---")

    st.markdown("## 💬 Chat with your PDF")

    question = st.text_input(
        "",
        placeholder="Ask anything about your document..."
    )

    ask = st.button(
        "🚀 Generate AI Answer",
        use_container_width=True
)
# ---------------------------------------------------
# ASK QUESTION
# ---------------------------------------------------

if ask:

    if question.strip() == "":

        st.warning("⚠️ Please enter a question.")

    else:

        with st.spinner("🔍 Searching document..."):

            results = search_client.search(
                search_text=question,
                top=3
            )

            context_list = []

            for item in results:
                context_list.append(item["content"])

            context = "\n\n".join(context_list)

        if context.strip() == "":

            st.error("❌ No relevant information found.")

        else:

            with st.spinner("🤖 Thinking..."):

                response = openai_client.chat.completions.create(

                    model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),

                    messages=[
                        {
                            "role": "system",
                            "content":
                            f"""
You are AskMyDocs AI.

Answer ONLY from the document below.

If the answer is not present,
reply:

'I couldn't find that information in the uploaded document.'

Document:

{context}
"""
                        },
                        {
                            "role": "user",
                            "content": question
                        }
                    ],

                    max_completion_tokens=500
                )

            answer = response.choices[0].message.content

            st.markdown("---")

            st.markdown("""
<h2 style='text-align:center;color:#4F46E5;'>
🤖 AI Response
</h2>
""", unsafe_allow_html=True)

            st.markdown(
                f"""
<div class="answer">

<h3>💡 Answer</h3>

<p style="font-size:18px;line-height:1.8;">

{answer}

</p>

</div>
""",
                unsafe_allow_html=True
            )

            st.markdown("")

            with st.expander("📚 Context Used"):

                st.write(context)

            st.download_button(

                "📥 Download Answer",

                data=answer,

                file_name="answer.txt",

                mime="text/plain",

                use_container_width=True

            )

            st.balloons()
# ============================================================
# FOOTER
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "⚡ Powered By",
        "Azure OpenAI"
    )

with col2:
    st.metric(
        "🔍 Search",
        "Azure AI Search"
    )

with col3:
    st.metric(
        "📄 Document AI",
        "Ready"
    )

st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
"""
<div style="

padding:25px;
border-radius:20px;
text-align:center;
background:linear-gradient(135deg,#4F46E5,#7C3AED);
color:white;
box-shadow:0 10px 30px rgba(0,0,0,.20);

">

<h2>🤖 AskMyDocs AI</h2>

<p style="font-size:17px;">

Chat intelligently with your documents using

<b>Azure AI Search</b> +
<b>Azure OpenAI</b>

</p>

<hr>

<p>

Built with ❤️ using

Streamlit • Azure AI • PyMuPDF

</p>

</div>

""",
unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

with st.expander("ℹ️ About This Project"):

    st.write("""

### 🚀 Features

✅ Upload PDF

✅ AI Search

✅ Azure OpenAI

✅ Fast Responses

✅ Secure Search

✅ Beautiful UI

""")

st.markdown("""

<center>

<small>

© 2026 AskMyDocs AI

Designed with ❤️ by Vanshika Dureja

</small>

</center>

""",
unsafe_allow_html=True)
