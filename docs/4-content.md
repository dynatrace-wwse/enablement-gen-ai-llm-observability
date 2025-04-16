# Content
--8<-- "snippets/4-content.js"

## What is LLM observability?
Large language model (LLM) observability provides visibility into all aspects of LLMs, including applications, prompts, data sources, and outputs. Complete observability is critical to ensure accuracy and reliability.

## The need for LLM observability
As large language models have evolved, many use cases have emerged. Common LLM implementations include chatbots, data analysis, data extraction, code creation, and content creation. These AI-powered models offer benefits such as speed, scope, and scale. LLMs can quickly handle complex queries using a variety of data types from multiple data sources.

However, synthesizing more data faster doesn't always mean better results. Models may function perfectly, but if the data sources aren't accurate, outputs will be inaccurate, as well. Furthermore, if the data is valid, but processes are flawed, results won't be reliable. Therefore, observability is necessary to ensure all aspects of LLM operation are correct and consistent.

## Key components of LLM observability
LLM observability has three key components:

## Output evaluation
Teams must regularly evaluate outputs for accuracy and reliability. Because many organizations use third-party LLMs, teams often accomplish this using a separate evaluation LLM that’s purpose-built for this function.

## Prompt analysis
Poorly constructed prompts are a common cause of low-quality results. Therefore, LLM observability regularly analyzes prompts to determine if queries produce desired results and if better prompt templates can improve them.

## Retrieval improvement
Data search and retrieval are critical for effective output. Here, the observability solution considers the retrieved data's context and accuracy, and it looks for ways to improve this process.


<div class="grid cards" markdown>
- [Let's continue:octicons-arrow-right-24:](cleanup.md)
</div>
