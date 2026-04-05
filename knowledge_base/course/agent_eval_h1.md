<!-- source: scripts/course/AgentEval-H-1.pptx | docling extract -->

AgentEval

A Framework for Multi-Dimensional Utility Assessment

Based on AutoGen Framework

# Why Evaluation is Hard in LLM Systems

- Traditional NLP metrics fail to capture multi-step agent behavior.
- Key properties of LLM outputs:
- Probabilistic — the same prompt may produce different answers
- Context-dependent — output quality depends heavily on prompt wording
- Non-deterministic — no single guaranteed correct response
- Open-ended — many tasks have multiple valid answers
- Why This Breaks Classical Testing 

Traditional software assumes:

- deterministic outputs
- single correct answer
- repeatable execution
- LLM agents violate these assumptions.

# From LLMs to Autonomous Agents

<!-- image -->

Source : Microsoft AutoGen Project https://microsoft.github.io/autogen/

Example: AutoGen multi-agent architecture

Key Insight: As agent autonomy increases, hidden failure modes multiply and traditional output-based evaluation becomes insufficient. AgentEval was proposed to address this emerging evaluation gap.

# Typical Agent Execution Pipeline

- AI agents do not produce answers in a single step. Instead, they follow an iterative reasoning–action loop that may involve multiple interactions with tools.

Core Execution Stages

1. Task Reception: The agent receives the user’s goal or instruction.
2. Reasoning / Planning: The LLM determines the next best action.
3. Tool Selection: The agent chooses an external tool or API when needed.
4. Parameter Construction: The agent builds the tool input (e.g., JSON arguments).
5. Tool Execution: The external system is invoked.
6. Observation: The agent interprets the returned result.
7. Iteration or Termination: The agent either continues the loop or produces the final answer.
8. 

# Hidden Failure Modes in AI Agents

- AI agents operate through an iterative reasoning–action loop rather than producing answers in a single step.
- Because of this multi-step process, failures may occur silently at any stage of execution.

Where Failures Commonly Occur

1. Task Reception: Agent misunderstands the user’s goal
2. Reasoning / Planning: Agent chooses incorrect next step
3. Tool Selection: Wrong API/tool is invoked
4. Parameter Construction: Incorrect JSON or arguments
5. Tool Execution: API returns error (e.g., 404)
6. Observation: Agent misinterprets the result
7. Iteration or Termination: Final report does not match trace
8. 
9. AgentEval is designed to detect failures across this entire pipeline, not just the final answer.

# Real Failure Example: 404 Misinterpretation

The agent was tasked with testing the mock user API.

Test Results Observed

- /users/50 → valid response (HTTP 200)
- /users/-1 → error response (HTTP 404 Not Found)
- Despite receiving a 404 error, the agent reported:
- “Negative test passed.”
- This reveals a semantic reasoning failure: The agent equated “expected negative test” with “successful validation” without verifying correctness conditions.
- The failure is not in the output format — it is in the reasoning-to-report alignment. 
- AgentEval exposes these hidden reasoning errors by analyzing the full execution trace.
- 

<!-- image -->

Example Agent Interpretation

# Real Failure Example: 404 Misinterpretation

The agent was tasked with testing the mock user API.

Test Results Observed

- /users/50 → valid response (HTTP 200)
- /users/-1 → error response (HTTP 404 Not Found)
- Despite receiving a 404 error, the agent reported:
- “Negative test passed.”
- This reveals a semantic reasoning failure: The agent equated “expected negative test” with “successful validation” without verifying correctness conditions.
- The failure is not in the output format — it is in the reasoning-to-report alignment. 
- AgentEval exposes these hidden reasoning errors by analyzing the full execution trace.
- 

# Failure Localization in the Agent Execution Pipeline

Where did this 404 error get misinterpreted?

The failure occurred at:

- Stage 6: Observation Interpretation
- Stage 7: Final Reporting

- The agent:
- Correctly executed the tool (callApi)
- Correctly received 404
- Incorrectly interpreted the semantic meaning
- Incorrectly aggregated into the final report

# Why Output-Based Testing Fails for AI Agents

- Traditional testing validates:
- Output format
- Response structure
- Presence of expected fields
- Basic success/failure status
- In the 404 example:
- The final report had a correct JSON structure
-  Test counts were present
- Status labels were formatted properly
- Yet the reasoning was incorrect.
- What Was NOT Validated?
- Whether 404 was semantically handled correctly.
-  Whether schema validation actually occurred
-  Whether final results matched trace evidence
-  Whether each decision was logically justified 
- 

- Core Problem
- Output-based testing validates syntactic correctness.
- Agent evaluation must validate semantic and procedural consistency
- An agent can generate a structurally correct report that is logically incorrect 
- 

# Trace-Based Evaluation: Verifying Behavior, Not Just Output

- Trace-based evaluation inspects the complete execution trajectory of an agent, not just its final output.

A trace includes:

- tool calls
- Parameters
-  API responses
-  validation steps
-  reasoning decisions
-  Final report generation

 

<!-- image -->

# Anatomy of the Execution Trace

- A trace is a structured log capturing the complete execution trajectory of an AI agent.
- Each action performed by the agent is recorded as a step. Includes:
- Step number
- Agent role (assistant, tool, system)
- Action type (reasoning step or tool call)
- This helps reconstruct the sequence of decisions.
- 

# Key Components Recorded in a Trace

Trace entries capture several elements:

Tool Invocation

- tool name
- Parameters
- API endpoint

Tool Response

- HTTP status code
- response body
-  error messages

Validation Evidence

- schema validation results
- flags such as valid=true/false

Final Report Data

-  total tests
-  success count
- error count
- 

# What AgentEval Checks

AgentEval inspects the trace and verifies agent behavior.

Key checks:

- Step Accuracy Did the agent follow the correct workflow order?
- Tool Accuracy Were the correct tools invoked with the correct parameters?
- Response Interpretation Did the agent interpret API responses correctly?
- Validation Execution Did schema validation actually occur?
- Final Report Consistency Does the report match the trace evidence?
- 

# What AgentEval Evaluates

- AgentEval evaluates the entire agent trajectory using multiple metrics.

Core Evaluation Metrics

1. Step Accuracy

→ Did the agent follow the expected workflow order?

1. Tool Accuracy → Were the correct tools invoked with proper parameters?
2. Schema Pass Rate → Did API responses match the expected JSON schema?
3. Failure Handling → Were error cases (e.g., HTTP 404) interpreted correctly?
4. Final Correctness → Does the final report match the actual execution trace?
5. 

# What AgentEval Flags in the 404 Case

- Correct interpretation:

404 indicates an error case.

- Failure scenario:

Agent incorrectly reports “Negative test passed.”

- AgentEval flags:

 incorrect response interpretation  mismatch between trace and final report

- 

# Hands-On Demonstration: Running AgentEval Locally

Run a local AgentEval example

Components:

- mock API server
- deterministic testing agent
- execution trace
- evaluation script

# To run the AgentEval demonstration, we first prepare the environment.

1. git clone https://github.com/codemits/AgentEval.git

        cd AgentEval  2. Install Ollama (Local LLM Runtime)     Download from:  https://ollama.com.

     In terminal :  Ollama run llama3

 3. Install Node.js and npm Download from: https://nodejs.org.

To run the demonstration, we need to replace the AgentEval\src folder and configure all files to use Ollama instead of the original OpenAI and Azure Key requirements. 

# Build your project

Open a terminal and run the following command:

PS C:\Users\hasan\OneDrive - Texas Tech University\Desktop\AgentEval&gt; npm run build

&gt;&gt;

&gt; agent-eval@1.0.0 build

&gt; tsc

<!-- image -->

# Running the Mock API

- Before running the agent, we start the mock API server.  Inside the AgentEval folder, run the terminal:                                 npm run start: mock  

        

<!-- image -->

# Test mock server

- Agebt call users/1 represent successful call 
- 
- 
- 
- 
- Agent calls users/-1, which represents an error call
- 

<!-- image -->

<!-- image -->

# Running the Testing Agent

The agent automatically performs the following tasks:

- generates test user IDs
-  sends requests to the API
- validates responses
- records the execution trace
- produces a final test report
- 

- Open a new terminal and run the command:   npm run agent

<!-- image -->

# Agent Execution Trace and Test Results

Step 1 — Test Case Generation

[1, 50, 100, -1, 999]  Step 2 — Valid API Request

Result: {"status":200,"data":{"id":50,"name":"User 50","email":"user50@example.com"}}

Step 3 — Invalid API Request

Result: {"status":404,"data":{"error":"User not found"}} Step 4 — Schema Validation

Result: {"valid":false}

Step 5 — Final Report

Total tests: 2

Successful: 1

Errors: 1

# Running the Evaluation: npm run evaluate

<!-- image -->

- The evaluation module analyzes the trace and checks:
- step sequence correctness
-  tool usage accuracy
-  API parameter validity
-  schema validation
-  error interpretation
-  consistency between trace and final report
- 

# AgentEval: Evaluating LLM-Powered Applications 

- After observing the behavior of AI agents in the demonstration, the next question is:

How can we systematically evaluate LLM-powered applications?

- Microsoft Research introduced AgentEval, a framework designed to assess the utility of LLM-powered applications that assist users in completing tasks.
- AgentEval aims to simplify the evaluation process by:
-  Automatically generating evaluation criteria
-  Measuring performance across these criteria
- Enabling a comprehensive assessment of system utility
- AgentEval is implemented within the AutoGen framework.
- 

# Assessing Utility in LLM Applications

- Developers building AI systems need to understand:
- How well the system helps users complete tasks
-  What aspects of the system perform well
-  what aspects require improvement
- Traditional evaluation methods often rely on simple success metrics, such as whether the task was completed.
- However, this approach is insufficient because:
-  Success is not always clearly defined
- Multiple valid solutions may exist
-  Explanation quality also matters
- For example, when solving a math problem, evaluation should consider:

• Correctness of the solution • Clarity of the explanation • Concise reasoning

- AgentEval addresses this challenge by evaluating systems using multiple criteria.
- 

# Task Taxonomy in LLM Applications

<!-- image -->

# AgentEval Framework Overview

- AgentEval evaluates LLM-powered applications using three agents. Each agent performs a different role in the evaluation process.
- CriticAgent

Generates evaluation criteria.

- QuantifierAgent

Measures how well the system satisfies those criteria.

- VerifierAgent

Ensures the evaluation process is robust and meaningful.

- Together, these agents produce a multi-dimensional evaluation of system utility.
- 

# AgentEval Framework 

# CriticAgent: Generating Evaluation Criteria 

- The CriticAgent analyzes the task and generates evaluation criteria.
- Inputs include:
- task description
- successful example responses
- failed example responses
- Using these inputs, CriticAgent identifies important dimensions of system performance.
- For example, in a math tutoring application, the CriticAgent might generate criteria such as:

Accuracy Conciseness Relevance

- Developers are encouraged to review these criteria using domain knowledge.
- 

# Structure of Generated Criteria

- Each criterion generated by CriticAgent has three components.
1. Name

The evaluation dimension.

1. Description

Explanation of what the criterion measures.

1. Accepted Values

Possible evaluation scores.

Example:

- Criterion: Accuracy
- Accepted values:
- Correct
- Minor errors
- Major errors
-  Incorrect
- This structured format allows subjective judgments to be transformed into measurable evaluation metrics.
- 

# QuantifierAgent: Evaluating Performance

- After the criteria are generated, the QuantifierAgent evaluates the system output.
- Inputs:
- list of evaluation criteria
- Task description
- Execution trace or conversation
- Ground truth information
- The QuantifierAgent assigns values to each criterion.
- Example:

Accuracy → Correct Conciseness → Concise Relevance → Highly relevant

- This produces a multi-dimensional performance assessment.
- 

# Example Quantification Output 

- The output of the QuantifierAgent includes: 
- The actual success status of the task
- Estimated performance across each criterion
- Example output:
- Actual Success: True
- Estimated Performance:

Accuracy → Correct Conciseness → Concise Relevance → Highly relevant

- This allows developers to understand both overall success and quality of the solution.
- 

# VerifierAgent: Ensuring Reliable Evaluation

- The VerifierAgent improves the reliability of the evaluation process.
- Its role is to ensure that evaluation criteria remain:
- Robust
- Meaningful
- relevant to end users
- VerifierAgent performs two major checks:
- Criteria Stability
- Discriminative Power
- 

# Criteria Stability

- VerifierAgent evaluates whether the generated criteria are:
- Essential for evaluating the task
- Non-redundant
- Consistently measurable
- If some criteria overlap or are unnecessary, they are removed.
- The goal is to retain only robust evaluation criteria.
- 

# Discriminative Power

- VerifierAgent also tests whether the criteria can distinguish between good and poor system behavior.
- This is done by introducing adversarial examples, such as:
- Noisy or corrupted inputs
- Compromised data
- Misleading responses
- If the evaluation framework fails to detect these cases, the criteria must be refined.
- 

# Flexibility of AgentEval

- AgentEval is designed to work with many types of tasks.
- Examples include:
- Solving math problems
- Performing household tasks in simulated environments
- Generating text or suggestions
- Assisting users with complex workflows
- The framework supports both:
- Tasks with clearly defined success.
- Tasks where multiple acceptable solutions exist.
- 

# Human-in-the-Loop Evaluation

- AgentEval supports human participation in the evaluation process.
- Domain experts can:
-  Suggest relevant evaluation criteria
-  Verify the usefulness of the generated criteria

- This human-in-the-loop approach ensures that evaluation remains aligned with real-world expectations and domain knowledge.
- 

# Empirical Validation

- AgentEval was tested on two applications.
- Math Problem Solving
- Dataset:
- 12,500 challenging math problems with step-by-step solutions.
- AgentEval evaluated multiple models and successfully identified relevant evaluation criteria.
- ALFWorld Simulation
- ALFWorld is a simulated environment where agents perform household tasks.
- Examples include:
- navigating rooms
- interacting with objects
- completing instructions
- AgentEval evaluated agent performance in these multi-step interactions.
- 

# Using AgentEval

- AgentEval currently operates in two main stages.
1. Criteria Generation

Example function: generate\_criteria()

Inputs:

- task description
- successful example
- failed example
1. Criteria Quantification

Example function: quantify\_criteria()

- This stage evaluates execution traces using the generated criteria.
- 

# Advantages of AgentEval

- AgentEval provides several important benefits.
- enables automated evaluation of AI systems
- evaluates multiple performance dimensions
- reduces reliance on manual human evaluation
- helps identify strengths and weaknesses of applications
- 
- It provides developers with insight into how well their AI systems assist users.
- 

# Limitations of AgentEval 

- Generated criteria may vary between runs
- Quantification results may change due to LLM randomness
-  The VerifierAgent component is still under development
- Researchers recommend performing multiple evaluation runs and including human expertise in the evaluation process.
- 

# Demonstration 2: AgentEval with AutoGen + Ollama

- In this demonstration, we run a simplified Microsoft-style AgentEval pipeline locally using:
- AutoGen agents
- Ollama local LLM
- Automatically generated evaluation criteria
- Three agents used
- TaskAgent — solves the task
- CriticAgent — generates evaluation criteria
- QuantifierAgent — evaluates the response
- 

# Create Virtual Environment 

Windows:

 python -m venv venv

venv\Scripts\activate

Mac / Linux

 python3 -m venv venv

source venv/bin/activate

# Requirements

- Python 3.10+
- Now install the required python packages inside virtual environment:
- autogen-agent
- chatautogen-extrequests 
- Commands

   pip install autogen-agentchat

   pip install autogen-ext

   pip install requests

# Install Ollama

- Ollama is used as the local LLM backend.   Download go to: https://ollama.com
- Download a Local Model In terminal : ollama pull llama3 
- Start Ollama

                              ollama run llama3 

Local model server runs at: http://localhost:11434

 

# Project Files

-  The demonstration uses three Python files:
- ollama\_llm.py              
- agenteval\_basic.py
- agenteval\_execute.py
- 
- ollama\_llm.py — helper for connecting to Ollama using requests 
- agenteval\_basic.py — initializes AutoGen agents with Ollama 
- agenteval\_execute.py — runs the full Task → Criteria → Evaluation pipeline
- 

# Run the Demo

In your code,  we want to run the math problem (or any task) defined inside agenteval\_execute.py. 

Open the agenteval\_execute.py in any editor and specify the task: 

task\_prompt = "Solve the equation: 3x + 5 = 20."

In one terminal run ollama

If you do not have a GPU set OLLAMA\_NO\_CUDA=1

ollama run llama3

In another  the terminal and inside the virtual environment, run the command:

 python agenteval\_execute.py     

# What the script does 

- TaskAgent solves the problem
- CriticAgent generates evaluation criteria
- QuantifierAgent evaluates the response
- This demonstrates a multi-agent evaluation pipeline.
- 

# Output 

- TASK OUTPUT 

<!-- image -->

# CRITERIA

# Evaluation output for math problem