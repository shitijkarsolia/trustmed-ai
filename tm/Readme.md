==================================================
Project Spec: TrustMed AI (PoC)
==================================================

---
1. Project Overview
---

* Project Name: TrustMed AI (PoC)
* Objective: To build a working prototype of an AI-powered chatbot that answers medical queries. The system will use a Retrieval-Augmented Generation (RAG) pipeline to provide answers grounded in a trusted knowledge base, which includes both authoritative medical documents and real-world patient forum data.
* Technology Stack:
    * UI (Frontend): Chainlit (running locally)
    * Backend (Application): Python, Boto3 (AWS SDK)
    * Data Storage: Amazon S3
    * RAG Engine: Amazon Bedrock Knowledge Base
    * AI Models: Amazon Bedrock (e.g., Amazon Titan Embeddings, Anthropic Claude 3 Sonnet for generation)

---
2. Core Architecture
---

The architecture is a serverless RAG pipeline:

1.  Manual Setup: You will upload your authoritative and forum data (PDFs, TXT) to an Amazon S3 Bucket.
2.  Manual Setup: You will configure an Amazon Bedrock Knowledge Base to point to this S3 bucket. Bedrock will automatically handle chunking, embedding, and indexing the data into a managed vector store.
3.  Build Phase: Your local Chainlit application will serve as the chat UI.
4.  Runtime: When a user sends a message, Chainlit will use Boto3 to call the Bedrock Knowledge Base's `retrieve_and_generate` API.
5.  Runtime: Bedrock will execute the entire RAG flow on your behalf: embed the query, search the vector store, retrieve relevant chunks (from both forum and authoritative data), build a prompt, and pass it all to a generation model (like Claude 3) to synthesize a final, cited answer.

---
3. Module 0: Manual Environment & AWS Setup (Prerequisite)
---

Objective: To prepare your local machine and AWS account before any code is written.

Task 0.1: Install Local Dependencies
* On your local development machine, install Python (3.10+), the AWS CLI, and the required Python libraries: `pip install chainlit boto3`.

Task 0.2: Configure AWS CLI
* Run `aws configure` in your terminal. Provide your AWS Access Key, Secret Key, and default region (e.g., `us-east-1`). This is how your local Boto3 script will get permission to interact with AWS.

Task 0.3: Enable Bedrock Model Access
* Go to the Amazon Bedrock console. In the bottom-left, click on "Model access." Request access for the models you'll need. At a minimum, enable:
    * Amazon Titan Text Embeddings G1 - Text (for the knowledge base)
    * Anthropic Claude 3 Sonnet (for generating the answers)
* This is a critical step; your API calls will fail until access is "Granted".

---
4. Module 1: Manual Data Collection & S3 Ingestion
---

Objective: To create the "knowledge" for your RAG system.

Task 1.1: Create S3 Bucket
* Go to the Amazon S3 console. Create a new, private bucket (e.g., `trustmed-poc-data-12345`). Block all public access. This bucket will hold all your documents.

Task 1.2: Collect Authoritative Data
* Go to trusted sites (Mayo Clinic, CDC, MedlinePlus). Search for topics related to Type II Diabetes and Heart Disease. Save 5-10 articles as PDFs or copy-paste their text into `.txt` files.

Task 1.3: Collect Forum Data
* Go to the specified forums (r/Diabetes, r/AskDocs, PatientsLikeMe). Find 10-15 high-quality discussion threads related to the same topics. Copy-paste the entire thread (original post + comments) into `.txt` files. Give them descriptive names (e.g., `r_diabetes_tingling_fingers.txt`).

Task 1.4: Upload Data to S3
* Using the S3 console, upload all your collected `.pdf` and `.txt` files directly into the bucket you created in Task 1.1.

---
5. Module 2: Manual Bedrock Knowledge Base Configuration
---

Objective: To configure the automated RAG pipeline in AWS.

Task 2.1: Create Knowledge Base
* 1. Go to the Amazon Bedrock console and select "Knowledge Base" from the left menu.
* 2. Click "Create Knowledge Base."
* 3. Give it a name (e.g., `trustmed-kb`).
* 4. When prompted for an IAM role, let Bedrock create a new role for you.

Task 2.2: Configure Data Source
* 1. In the "Data source" step, point it to the S3 bucket you created (Task 1.1).
* 2. For "Chunking strategy," select the default ("Default chunking") for now.

Task 2.3: Configure Vector Store
* 1. In the "Embeddings" step, select the "Amazon Titan Text Embeddings G1 - Text" model.
* 2. In the "Vector store" step, select "Quick create a new vector store." This will automatically create and manage an Amazon OpenSearch Serverless collection for you.

Task 2.4: Review and Create
* Review all settings and create the Knowledge Base. This may take a few minutes.

Task 2.5: Sync Knowledge Base
* This is the most important step. After your KB is created, go to its "Data source" section and click the "Sync" button. This tells Bedrock to crawl your S3 bucket, run the chunking/embedding process, and load the vector store. Wait for the "Last sync status" to show "Completed."

---
6. Module 3: Chainlit Application Core (Code)
---

Objective: To create the chatbot UI and connect it to the Bedrock backend.

Task 3.1: Create Chainlit Application Skeleton
* Objective: Create a single Python file (`app.py`) that serves as the entry point for your chat application.
* Requirements:
    * `chainlit` and `boto3` libraries installed.
    * A new file named `app.py`.
* Implementation Steps:
    1.  Import `chainlit as cl` and `boto3`.
    2.  Define global constants for your Knowledge Base ID and the Generation Model ARN. The user must find their KB ID in the Bedrock console.
    3.  Initialize a global `boto3` client for `bedrock-agent-runtime` in the correct region.
    4.  Create a `@cl.on_chat_start` function that sends a welcome message (e.g., "Welcome to TrustMed AI!").
    5.  Create a basic `@cl.on_message` function that receives the user's message.
* Acceptance Criteria (AC):
    * Running `chainlit run app.py -w` in the terminal successfully starts the server.
    * The chat UI opens in a browser, and the welcome message is displayed.

Task 3.2: Implement `retrieve_and_generate` Logic
* Objective: To take the user's message from Chainlit and get a response from the Bedrock Knowledge Base.
* Requirements:
    * Task 3.1 is complete.
    * The `KB_ID` and `MODEL_ARN` constants in `app.py` are correct.
* Implementation Steps:
    1.  Modify the `@cl.on_message` function.
    2.  First, send an empty `cl.Message` to the UI (e.g., `msg = cl.Message(content="")`) and `await msg.send()`. This will create the "thinking..." state.
    3.  Wrap the main logic in a `try...except` block to catch Boto3 errors.
    4.  Call the `bedrock-agent-runtime.retrieve_and_generate` method.
    5.  Pass the `message.content` as the `input`.
    6.  Set the `retrieveAndGenerateConfiguration` to use the `KB_ID` and `MODEL_ARN`.
    7.  Extract the `'text'` from the `['output']` field of the response.
    8.  Update the empty message's content with the response text: `msg.content = answer` and `await msg.update()`.
* Acceptance Criteria (AC):
    * User sends a message (e.g., "what is diabetes?").
    * The UI shows a "thinking" indicator.
    * An answer from the Bedrock KB is displayed in the chat.
    * If an error occurs (e.g., wrong KB ID), an error message is shown.

---
7. Module 4: UI Polish & Source Citations (Code)
---

Objective: To display the source citations from the RAG response, which is the core "trust" feature of the demo.

Task 4.1: Display Source Citations
* Objective: To parse the citations from the Bedrock response and display them in the Chainlit UI.
* Requirements:
    * Task 3.2 is complete.
* Implementation Steps:
    1.  Inside the `try` block of `@cl.on_message`, after receiving the `response` from `retrieve_and_generate`:
    2.  Extract the `citations` list from the `response`.
    3.  Initialize an empty `list` to hold `cl.Text` elements (e.g., `source_elements = []`).
    4.  Initialize a string to append to the answer (e.g., `citation_text = "\n\n**Sources:**\n"`).
    5.  Loop through the `citations` list. For each `citation`:
        * Access the `retrievedReferences` list (this contains the snippets).
        * Get the `s3Location.uri` for the source file.
        * Get the `content.text` for the snippet.
        * Format the `citation_text` string (e.g., `f"{i}. {s3_uri.split('/')[-1]}\n"`).
        * Create a `cl.Text(name=f"Source {i}", content=snippet, display="inline")` and append it to `source_elements`.
    6.  Update the final message: `msg.content = answer + citation_text` and `msg.elements = source_elements`.
* Acceptance Criteria (AC):
    * The chatbot's answer is displayed.
    * Below the answer, a "Sources:" list shows the filenames (e.g., `1. diabetes_mayo_clinic.pdf`).
    * The Chainlit UI shows clickable "Source 1" elements, which display the exact text snippet used for the answer.

---
8. Module 5: Backlog (Future Features)
---

These tasks are out of scope for the initial PoC but are documented here for future development.

Feature: UMLS Integration
* Objective: Improve retrieval by standardizing medical terms.
* Implementation: This would require replacing the simple Bedrock KB with a custom RAG pipeline. This involves using AWS Lambda to intercept S3 uploads, run a MetaMap container to extract UMLS CUIs, and store these as metadata in a custom Amazon OpenSearch index.

Feature: Knowledge Graph (GraphRAG)
* Objective: Answer complex, multi-hop questions about relationships (e.g., drug-diet interactions).
* Implementation: Requires an additional pipeline to extract (Subject, Predicate, Object) triples from documents (using an LLM) and load them into Amazon Neptune. The RAG query would then need to query *both* the vector store and the graph database.

Feature: Conversation History
* Objective: Allow the chatbot to remember previous turns in the conversation.
* Implementation: The `retrieve_and_generate` API has an optional `sessionId` parameter. This can be managed and passed from the Chainlit session to enable conversational context.