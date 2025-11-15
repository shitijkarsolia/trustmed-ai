"""
TrustMed AI - Chainlit Demo Application
Basic demo showing Chainlit functionality before Bedrock integration
"""

import chainlit as cl
from chainlit import Message
import asyncio


@cl.on_chat_start
async def on_chat_start():
    """
    Called when a new chat session starts.
    This is where we can initialize the session and send a welcome message.
    """
    welcome_message = """
# Welcome to TrustMed AI! 🏥

This is a demo of the Chainlit interface. Once we integrate with AWS Bedrock, 
this chatbot will be able to answer medical queries using a RAG (Retrieval-Augmented Generation) pipeline.

**Try asking me:**
- 💊 "What is diabetes?"
- ❤️ "Tell me about heart disease"
- 💉 "How does medication work?"

*Note: Currently running in demo mode without Bedrock integration.*
    """
    
    await cl.Message(
        content=welcome_message,
        author="TrustMed AI"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """
    Called when a user sends a message.
    This is where we'll integrate Bedrock later.
    For now, this demonstrates basic Chainlit message handling.
    """
    user_input = message.content
    
    # Create a message object that we'll update with the response
    response_msg = cl.Message(content="")
    await response_msg.send()
    
    # Simulate processing time (like we'd have with Bedrock API calls)
    await asyncio.sleep(0.5)
    
    # For demo purposes, provide a simple echo response
    # In the real implementation, this will call Bedrock's retrieve_and_generate API
    demo_response = f"""
I received your message: **"{user_input}"**

---

## 🔧 Demo Mode Active

In the full implementation, this message would be:

1. **Sent to AWS Bedrock Knowledge Base** - Your query would be processed by Amazon Bedrock
2. **Processed through the RAG pipeline** - The system would retrieve relevant context
3. **Retrieved relevant medical information** - From both authoritative sources and patient forums
4. **Generated a comprehensive answer** - With proper citations and source references

---

### 🚀 Next Steps

- ✅ Integrate AWS Bedrock Knowledge Base
- ✅ Connect to S3 data sources  
- ✅ Enable source citations in responses

---

### 💡 Try asking about:

- **Medical conditions** - "What is diabetes?"
- **Treatment options** - "How is heart disease treated?"
- **Medication information** - "Tell me about metformin"
- **Symptoms** - "What are the symptoms of high blood pressure?"

*Remember: This is a demo. Full functionality will be available after Bedrock integration.*
    """
    
    response_msg.content = demo_response
    await response_msg.update()


@cl.on_stop
async def on_stop():
    """
    Called when the user stops the conversation.
    """
    await cl.Message(
        content="Session ended. Thank you for using TrustMed AI!",
        author="TrustMed AI"
    ).send()

