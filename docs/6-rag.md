# Retrieval-Augmented Generation (RAG) 
--8<-- "snippets/6-rag.js"

Retrieval-Augmented Generation (RAG) is a technique that provides additional context to LLMs to have additional information to carry out a solution to the prompt they receive.
In our AI Travel Advisor App, the RAG pipeline is built using LangChain. The retrieval step reaches out to Weaviate to query for documents relevant to the prompt in input.

!!! bug "Add arch diagram"

Let's try again using the same city as input: `Sydney`.
The answer returned should be quite puzzling, like the following:

![hallucination](./img/rag_response.png)

In this answer, the LLM is hallucinating an answer which is far from being correct!
Let's investigate what could be the reason of such a weird answer.

## Tracing to the rescue

Let's use again the Distributed Tracing App to inspect the request.

![RAG Trace](./img/rag_trace.png)

We can see that the request is more complex because there is a step to fetch documents from Weaviate, process them, augment the prompt and finally send the final crafted prompt to Ollama.
Selecting each span, we have at our disposal all the contextual information that describe that AI pipeline step.
Let's focus on the call to Ollama and select the `ChatOllama.chat` span.

In the detailed view, we can see the GenAI section. Let's start from the prompt message:

![RAG Trace Details](./img/rag_details.png)


We can see that the prompt sent to the LLM contains information about Sydney and Bali.
This is a clear indicator that our Knowledge Base inside Weaviate is not exahustive enough.
LangChain retrieves the top N documents closest to the topic searched. 
If we look into the application code, inside the `destinations` folder, we see only two small documents.
The lack of coverage of the topic triggered the fetching of additional documents that don't really relate to Sydney.

Furthermore, we can also observe that feeding the LLM with garbage information produces garbage responses.
The content of the Sydney or Bali documents provide innacurate facts. 
This is telling us that the LLM really made use of the information we provided to it.

Let's try again using a different city, like `Paris`.
Since we don't have wrong information around Paris, now the LLM should produce a valid answer!

![Correct RAG](./img/good_rag.png)

!!! bug "There is a bug with OpenLLMetry and Weaviate for which we don't have spans for it."

<div class="grid cards" markdown>
- [Let's interact with the AI:octicons-arrow-right-24:](6-rag.md)
</div>
