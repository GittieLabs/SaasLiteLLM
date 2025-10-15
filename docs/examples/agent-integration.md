# Agent Integration Examples

Learn how to integrate SaaS LiteLLM with popular AI agent frameworks like LangChain, AutoGen, and CrewAI.

## Overview

AI agent frameworks typically expect OpenAI-compatible APIs. SaaS LiteLLM provides this interface while adding:

- Job-based cost tracking
- Model group abstraction
- Credit management
- Team isolation

## Integration Strategy

All frameworks follow a similar pattern:

1. **Create job** at the start of agent task
2. **Resolve model group** to get actual model name
3. **Make LLM calls** through the job
4. **Complete job** when task is done

## LangChain Integration

### Basic LangChain Wrapper

```python
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
import requests
from typing import List, Optional, Dict, Any

class SaaSLangChainWrapper:
    """
    Wrapper for using SaaS LiteLLM with LangChain.

    This wrapper creates a job, resolves model groups, and makes calls
    through the SaaS API while presenting an OpenAI-compatible interface
    to LangChain.
    """

    def __init__(
        self,
        api_url: str,
        virtual_key: str,
        team_id: str,
        model_group: str = "ChatFast",
        job_type: str = "langchain_agent"
    ):
        self.api_url = api_url
        self.virtual_key = virtual_key
        self.team_id = team_id
        self.model_group = model_group
        self.job_type = job_type
        self.job_id = None
        self.resolved_model = None

        self.headers = {
            "Authorization": f"Bearer {virtual_key}",
            "Content-Type": "application/json"
        }

    def start_job(self, metadata: Dict[str, Any] = None):
        """Create a job for this LangChain session"""
        response = requests.post(
            f"{self.api_url}/jobs/create",
            headers=self.headers,
            json={
                "team_id": self.team_id,
                "job_type": self.job_type,
                "metadata": metadata or {}
            }
        )
        response.raise_for_status()
        self.job_id = response.json()["job_id"]

        # Resolve model group to actual model
        self._resolve_model_group()

    def _resolve_model_group(self):
        """Resolve model group to actual model name"""
        response = requests.get(
            f"{self.api_url}/model-groups/{self.model_group}/resolve",
            headers=self.headers,
            params={"team_id": self.team_id}
        )
        response.raise_for_status()
        result = response.json()

        if not result.get("team_has_access"):
            raise ValueError(
                f"Team does not have access to model group '{self.model_group}'"
            )

        self.resolved_model = result["primary_model"]

    def get_langchain_llm(self, temperature: float = 0.7, **kwargs):
        """
        Get a LangChain ChatOpenAI instance configured to use SaaS LiteLLM.

        Note: This creates a custom callback to intercept calls.
        """
        if not self.job_id:
            self.start_job()

        # Create custom ChatOpenAI with our job context
        llm = SaaSChatOpenAI(
            wrapper=self,
            temperature=temperature,
            model=self.resolved_model,
            **kwargs
        )

        return llm

    def make_call(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        purpose: Optional[str] = None
    ) -> str:
        """Make an LLM call through the job"""
        if not self.job_id:
            raise ValueError("No job started. Call start_job() first.")

        response = requests.post(
            f"{self.api_url}/jobs/{self.job_id}/llm-call",
            headers=self.headers,
            json={
                "model_group": self.model_group,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "purpose": purpose
            }
        )
        response.raise_for_status()
        result = response.json()
        return result["response"]["content"]

    def complete_job(self, status: str = "completed"):
        """Complete the job"""
        if not self.job_id:
            return

        response = requests.post(
            f"{self.api_url}/jobs/{self.job_id}/complete",
            headers=self.headers,
            json={"status": status}
        )
        response.raise_for_status()
        return response.json()

    def __enter__(self):
        self.start_job()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.complete_job(status="failed")
        else:
            self.complete_job(status="completed")


class SaaSChatOpenAI(ChatOpenAI):
    """
    Custom ChatOpenAI that routes calls through SaaS API.
    """

    def __init__(self, wrapper: SaaSLangChainWrapper, **kwargs):
        self.wrapper = wrapper
        # Don't actually use OpenAI - we'll override the call
        super().__init__(openai_api_key="not-used", **kwargs)

    def _call(self, messages: List, **kwargs) -> str:
        """Override to use SaaS API"""
        # Convert LangChain messages to API format
        api_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                api_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                api_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, AIMessage):
                api_messages.append({"role": "assistant", "content": msg.content})

        return self.wrapper.make_call(
            messages=api_messages,
            temperature=kwargs.get("temperature", 0.7),
            purpose="langchain_call"
        )


# Example Usage
def langchain_example():
    """Complete LangChain example with SaaS LiteLLM"""
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate

    # Create wrapper
    with SaaSLangChainWrapper(
        api_url="http://localhost:8003/api",
        virtual_key="sk-your-virtual-key",
        team_id="engineering-team",
        model_group="ChatFast"
    ) as wrapper:

        # Get LangChain LLM
        llm = wrapper.get_langchain_llm(temperature=0.7)

        # Create a simple chain
        prompt = PromptTemplate(
            input_variables=["product"],
            template="Write a short marketing description for {product}"
        )

        chain = LLMChain(llm=llm, prompt=prompt)

        # Run the chain
        result = chain.run(product="AI-powered resume parser")

        print(f"Result: {result}")

    print("Job completed and tracked!")


if __name__ == "__main__":
    langchain_example()
```

### LangChain Agent Example

```python
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferMemory

def langchain_agent_example():
    """
    Full agent with tools, memory, and SaaS LiteLLM tracking.
    """

    # Custom tools
    def search_database(query: str) -> str:
        """Simulate database search"""
        return f"Found 3 results for '{query}'"

    def calculate(expression: str) -> str:
        """Simple calculator"""
        try:
            result = eval(expression)
            return f"Result: {result}"
        except:
            return "Invalid expression"

    tools = [
        Tool(
            name="Database Search",
            func=search_database,
            description="Search the database for information"
        ),
        Tool(
            name="Calculator",
            func=calculate,
            description="Calculate mathematical expressions"
        )
    ]

    # Create SaaS LiteLLM wrapper
    with SaaSLangChainWrapper(
        api_url="http://localhost:8003/api",
        virtual_key="sk-your-virtual-key",
        team_id="engineering-team",
        model_group="ChatAdvanced",
        job_type="langchain_agent_with_tools"
    ) as wrapper:

        # Get LLM
        llm = wrapper.get_langchain_llm(temperature=0)

        # Create memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # Initialize agent
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            verbose=True
        )

        # Run tasks
        print("Task 1: Database search")
        response1 = agent.run("Search the database for 'Python developers'")
        print(f"Response: {response1}\n")

        print("Task 2: Calculation")
        response2 = agent.run("What is 15 * 23?")
        print(f"Response: {response2}\n")

        print("Task 3: Using memory")
        response3 = agent.run("What did I ask you to search for earlier?")
        print(f"Response: {response3}\n")

    print("Agent task completed and costs tracked!")
```

## AutoGen Integration

AutoGen is a framework for building multi-agent conversations.

### AutoGen Wrapper

```python
from typing import List, Dict, Any, Optional
import requests

class SaaSAutoGenWrapper:
    """
    Wrapper for using SaaS LiteLLM with Microsoft AutoGen.

    Provides job-based tracking for AutoGen multi-agent conversations.
    """

    def __init__(
        self,
        api_url: str,
        virtual_key: str,
        team_id: str,
        model_group: str = "ChatFast"
    ):
        self.api_url = api_url
        self.virtual_key = virtual_key
        self.team_id = team_id
        self.model_group = model_group
        self.job_id = None
        self.call_count = 0

        self.headers = {
            "Authorization": f"Bearer {virtual_key}",
            "Content-Type": "application/json"
        }

    def start_conversation_job(self, metadata: Dict[str, Any] = None):
        """Start a job for this AutoGen conversation"""
        response = requests.post(
            f"{self.api_url}/jobs/create",
            headers=self.headers,
            json={
                "team_id": self.team_id,
                "job_type": "autogen_conversation",
                "metadata": metadata or {}
            }
        )
        response.raise_for_status()
        self.job_id = response.json()["job_id"]
        return self.job_id

    def get_llm_config(self, temperature: float = 0.7) -> Dict[str, Any]:
        """
        Get LLM config for AutoGen agents.

        AutoGen expects a config dict with model and API settings.
        We intercept this to route through our job.
        """
        if not self.job_id:
            self.start_conversation_job()

        # Return custom config that AutoGen will use
        return {
            "model": self.model_group,
            "api_type": "saas_litellm",
            "api_base": self.api_url,
            "api_key": self.virtual_key,
            "temperature": temperature,
            # Custom field for our wrapper
            "_saas_job_id": self.job_id,
            "_saas_wrapper": self
        }

    def make_agent_call(
        self,
        messages: List[Dict[str, str]],
        agent_name: str,
        temperature: float = 0.7
    ) -> str:
        """Make a call on behalf of an AutoGen agent"""
        if not self.job_id:
            raise ValueError("No conversation job started")

        self.call_count += 1

        response = requests.post(
            f"{self.api_url}/jobs/{self.job_id}/llm-call",
            headers=self.headers,
            json={
                "model_group": self.model_group,
                "messages": messages,
                "temperature": temperature,
                "purpose": f"{agent_name}_message_{self.call_count}"
            }
        )
        response.raise_for_status()
        result = response.json()
        return result["response"]["content"]

    def complete_conversation(self, status: str = "completed"):
        """Complete the conversation job"""
        if not self.job_id:
            return

        response = requests.post(
            f"{self.api_url}/jobs/{self.job_id}/complete",
            headers=self.headers,
            json={"status": status}
        )
        response.raise_for_status()
        return response.json()


# AutoGen Agent Example
def autogen_example():
    """
    Multi-agent conversation with AutoGen and SaaS LiteLLM.

    Note: This is a simplified example. In production, you'd integrate
    more deeply with AutoGen's config system.
    """
    import autogen

    # Create SaaS wrapper
    wrapper = SaaSAutoGenWrapper(
        api_url="http://localhost:8003/api",
        virtual_key="sk-your-virtual-key",
        team_id="engineering-team",
        model_group="ChatAdvanced"
    )

    # Start conversation job
    job_id = wrapper.start_conversation_job(
        metadata={"conversation_type": "product_planning"}
    )
    print(f"Started AutoGen conversation job: {job_id}")

    # Get LLM config
    llm_config = wrapper.get_llm_config(temperature=0.7)

    # Create agents
    user_proxy = autogen.UserProxyAgent(
        name="User",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=5,
        code_execution_config={"use_docker": False}
    )

    product_manager = autogen.AssistantAgent(
        name="ProductManager",
        system_message="You are a product manager. Focus on user needs and features.",
        llm_config=llm_config
    )

    engineer = autogen.AssistantAgent(
        name="Engineer",
        system_message="You are a software engineer. Focus on technical feasibility.",
        llm_config=llm_config
    )

    # Simulate conversation
    # In real AutoGen integration, you'd override the LLM client to use our wrapper
    print("\nStarting multi-agent conversation...")

    # Manually track calls (simplified)
    messages = []

    # User initiates
    user_msg = "We need to build a new feature for parsing resumes. What should we consider?"
    messages.append({"role": "user", "content": user_msg})

    # Product Manager responds
    pm_response = wrapper.make_agent_call(
        messages=messages,
        agent_name="ProductManager",
        temperature=0.7
    )
    print(f"\nProductManager: {pm_response}")
    messages.append({"role": "assistant", "content": pm_response})

    # Engineer responds
    eng_response = wrapper.make_agent_call(
        messages=messages,
        agent_name="Engineer",
        temperature=0.5
    )
    print(f"\nEngineer: {eng_response}")

    # Complete conversation
    result = wrapper.complete_conversation()
    print(f"\n✓ Conversation completed")
    print(f"  Total calls: {result['costs']['total_calls']}")
    print(f"  Total tokens: {result['costs']['total_tokens']}")
    print(f"  Credits remaining: {result['costs']['credits_remaining']}")


if __name__ == "__main__":
    autogen_example()
```

## CrewAI Integration

CrewAI is a framework for orchestrating role-playing autonomous AI agents.

### CrewAI Wrapper

```python
from typing import List, Dict, Any, Optional
import requests

class SaaSCrewAIWrapper:
    """
    Wrapper for using SaaS LiteLLM with CrewAI.

    Tracks crew tasks as jobs with individual agent calls tracked.
    """

    def __init__(
        self,
        api_url: str,
        virtual_key: str,
        team_id: str,
        model_group: str = "ChatAdvanced"
    ):
        self.api_url = api_url
        self.virtual_key = virtual_key
        self.team_id = team_id
        self.model_group = model_group
        self.current_job_id = None
        self.agent_call_counts = {}

        self.headers = {
            "Authorization": f"Bearer {virtual_key}",
            "Content-Type": "application/json"
        }

    def start_crew_task(self, task_name: str, metadata: Dict[str, Any] = None):
        """Start a job for a CrewAI task"""
        response = requests.post(
            f"{self.api_url}/jobs/create",
            headers=self.headers,
            json={
                "team_id": self.team_id,
                "job_type": "crewai_task",
                "metadata": {
                    "task_name": task_name,
                    **(metadata or {})
                }
            }
        )
        response.raise_for_status()
        self.current_job_id = response.json()["job_id"]
        return self.current_job_id

    def get_llm_config_for_agent(
        self,
        agent_role: str,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Get LLM config for a specific CrewAI agent"""
        return {
            "model_group": self.model_group,
            "temperature": temperature,
            "api_url": self.api_url,
            "job_id": self.current_job_id,
            "agent_role": agent_role,
            "wrapper": self
        }

    def make_agent_call(
        self,
        agent_role: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Make an LLM call for a specific agent"""
        if not self.current_job_id:
            raise ValueError("No task job started. Call start_crew_task() first.")

        # Track call count for this agent
        if agent_role not in self.agent_call_counts:
            self.agent_call_counts[agent_role] = 0
        self.agent_call_counts[agent_role] += 1

        call_num = self.agent_call_counts[agent_role]

        response = requests.post(
            f"{self.api_url}/jobs/{self.current_job_id}/llm-call",
            headers=self.headers,
            json={
                "model_group": self.model_group,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "purpose": f"{agent_role}_call_{call_num}"
            }
        )
        response.raise_for_status()
        result = response.json()
        return result["response"]["content"]

    def complete_task(self, status: str = "completed", error_message: str = None):
        """Complete the crew task"""
        if not self.current_job_id:
            return

        response = requests.post(
            f"{self.api_url}/jobs/{self.current_job_id}/complete",
            headers=self.headers,
            json={
                "status": status,
                "error_message": error_message
            }
        )
        response.raise_for_status()
        result = response.json()

        # Reset for next task
        self.current_job_id = None
        self.agent_call_counts = {}

        return result


# CrewAI Example
def crewai_example():
    """
    Example using SaaS LiteLLM with CrewAI crew.

    This shows how to track a multi-agent crew task through a single job.
    """
    from crewai import Agent, Task, Crew

    # Create wrapper
    wrapper = SaaSCrewAIWrapper(
        api_url="http://localhost:8003/api",
        virtual_key="sk-your-virtual-key",
        team_id="engineering-team",
        model_group="ChatAdvanced"
    )

    # Start task
    job_id = wrapper.start_crew_task(
        task_name="market_research",
        metadata={"project": "new_product_launch"}
    )
    print(f"Started CrewAI task job: {job_id}")

    # Define agents with SaaS LiteLLM integration
    researcher = Agent(
        role="Market Researcher",
        goal="Research market trends and customer needs",
        backstory="Expert in market analysis with 10 years experience",
        verbose=True,
        # Pass our wrapper config
        llm_config=wrapper.get_llm_config_for_agent("researcher", temperature=0.7)
    )

    analyst = Agent(
        role="Data Analyst",
        goal="Analyze research data and provide insights",
        backstory="Skilled data analyst with strong statistical background",
        verbose=True,
        llm_config=wrapper.get_llm_config_for_agent("analyst", temperature=0.5)
    )

    writer = Agent(
        role="Content Writer",
        goal="Write compelling reports based on analysis",
        backstory="Professional writer with expertise in business content",
        verbose=True,
        llm_config=wrapper.get_llm_config_for_agent("writer", temperature=0.8)
    )

    # Define tasks
    research_task = Task(
        description="Research the AI resume parsing market",
        agent=researcher
    )

    analysis_task = Task(
        description="Analyze the research findings and identify key opportunities",
        agent=analyst
    )

    writing_task = Task(
        description="Write a one-page executive summary",
        agent=writer
    )

    # Create crew
    crew = Crew(
        agents=[researcher, analyst, writer],
        tasks=[research_task, analysis_task, writing_task],
        verbose=True
    )

    # In real CrewAI integration, you'd override the LLM client
    # For this example, we'll simulate the calls
    print("\n=== Simulating Crew Execution ===\n")

    # Researcher
    research_result = wrapper.make_agent_call(
        agent_role="researcher",
        messages=[
            {
                "role": "system",
                "content": "You are a market researcher. Research the AI resume parsing market."
            },
            {
                "role": "user",
                "content": "What are the key trends in AI resume parsing?"
            }
        ],
        temperature=0.7
    )
    print(f"Researcher: {research_result[:200]}...\n")

    # Analyst
    analysis_result = wrapper.make_agent_call(
        agent_role="analyst",
        messages=[
            {
                "role": "system",
                "content": "You are a data analyst. Analyze market research."
            },
            {
                "role": "user",
                "content": f"Analyze this research: {research_result}"
            }
        ],
        temperature=0.5
    )
    print(f"Analyst: {analysis_result[:200]}...\n")

    # Writer
    writing_result = wrapper.make_agent_call(
        agent_role="writer",
        messages=[
            {
                "role": "system",
                "content": "You are a business writer. Write executive summaries."
            },
            {
                "role": "user",
                "content": f"Write an executive summary based on: {analysis_result}"
            }
        ],
        temperature=0.8
    )
    print(f"Writer: {writing_result[:200]}...\n")

    # Complete task
    result = wrapper.complete_task()

    print("=== Task Completed ===")
    print(f"Job ID: {result['job_id']}")
    print(f"Total calls: {result['costs']['total_calls']}")
    print(f"  - Researcher: {wrapper.agent_call_counts.get('researcher', 0)} calls")
    print(f"  - Analyst: {wrapper.agent_call_counts.get('analyst', 0)} calls")
    print(f"  - Writer: {wrapper.agent_call_counts.get('writer', 0)} calls")
    print(f"Total tokens: {result['costs']['total_tokens']}")
    print(f"Total cost: ${result['costs']['total_cost_usd']:.6f}")
    print(f"Credits remaining: {result['costs']['credits_remaining']}")


if __name__ == "__main__":
    crewai_example()
```

## General Agent Wrapper Pattern

Here's a reusable pattern for any agent framework:

```python
from typing import Protocol, List, Dict, Any, Optional
import requests
from contextlib import contextmanager

class AgentLLMWrapper(Protocol):
    """Protocol for agent framework LLM wrappers"""

    def make_call(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Make an LLM call"""
        ...


class SaaSAgentBase:
    """
    Base class for integrating any agent framework with SaaS LiteLLM.

    Provides:
    - Job lifecycle management
    - Model group resolution
    - Call tracking
    - Error handling
    """

    def __init__(
        self,
        api_url: str,
        virtual_key: str,
        team_id: str,
        model_group: str,
        job_type: str = "agent_task"
    ):
        self.api_url = api_url
        self.virtual_key = virtual_key
        self.team_id = team_id
        self.model_group = model_group
        self.job_type = job_type
        self.job_id = None
        self.call_count = 0

        self.headers = {
            "Authorization": f"Bearer {virtual_key}",
            "Content-Type": "application/json"
        }

    def create_job(self, metadata: Dict[str, Any] = None) -> str:
        """Create a job for this agent task"""
        response = requests.post(
            f"{self.api_url}/jobs/create",
            headers=self.headers,
            json={
                "team_id": self.team_id,
                "job_type": self.job_type,
                "metadata": metadata or {}
            }
        )
        response.raise_for_status()
        self.job_id = response.json()["job_id"]
        return self.job_id

    def make_llm_call(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        purpose: Optional[str] = None
    ) -> str:
        """Make an LLM call through the job"""
        if not self.job_id:
            self.create_job()

        self.call_count += 1

        response = requests.post(
            f"{self.api_url}/jobs/{self.job_id}/llm-call",
            headers=self.headers,
            json={
                "model_group": self.model_group,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "purpose": purpose or f"call_{self.call_count}"
            }
        )
        response.raise_for_status()
        result = response.json()
        return result["response"]["content"]

    def complete_job(self, status: str = "completed", error: str = None) -> Dict[str, Any]:
        """Complete the job and get cost summary"""
        if not self.job_id:
            return {}

        response = requests.post(
            f"{self.api_url}/jobs/{self.job_id}/complete",
            headers=self.headers,
            json={
                "status": status,
                "error_message": error
            }
        )
        response.raise_for_status()
        return response.json()

    @contextmanager
    def task_context(self, metadata: Dict[str, Any] = None):
        """
        Context manager for agent tasks.

        Usage:
            with wrapper.task_context(metadata={"task": "analysis"}):
                # Make LLM calls
                result = wrapper.make_llm_call(messages)
        """
        try:
            self.create_job(metadata)
            yield self
            self.complete_job(status="completed")
        except Exception as e:
            self.complete_job(status="failed", error=str(e))
            raise


# Example usage with any framework
def generic_agent_example():
    """Example showing the general pattern"""

    wrapper = SaaSAgentBase(
        api_url="http://localhost:8003/api",
        virtual_key="sk-your-virtual-key",
        team_id="engineering-team",
        model_group="ChatAdvanced",
        job_type="custom_agent"
    )

    # Use context manager for automatic job management
    with wrapper.task_context(metadata={"agent_type": "research"}):

        # Step 1: Initial research
        research = wrapper.make_llm_call(
            messages=[
                {"role": "system", "content": "You are a research assistant."},
                {"role": "user", "content": "Research AI trends in 2024"}
            ],
            temperature=0.7,
            purpose="research_phase"
        )
        print(f"Research: {research[:100]}...")

        # Step 2: Analysis
        analysis = wrapper.make_llm_call(
            messages=[
                {"role": "system", "content": "You are a data analyst."},
                {"role": "user", "content": f"Analyze this: {research}"}
            ],
            temperature=0.5,
            purpose="analysis_phase"
        )
        print(f"Analysis: {analysis[:100]}...")

        # Step 3: Summary
        summary = wrapper.make_llm_call(
            messages=[
                {"role": "user", "content": f"Summarize: {analysis}"}
            ],
            temperature=0.3,
            purpose="summary_phase"
        )
        print(f"Summary: {summary}")

    print("Task completed automatically!")
```

## Best Practices for Agent Integration

### 1. Job Granularity

```python
# ✅ GOOD: One job per agent task/conversation
with wrapper.task_context():
    # All calls for this task
    result1 = wrapper.make_llm_call(...)
    result2 = wrapper.make_llm_call(...)
    result3 = wrapper.make_llm_call(...)

# ❌ BAD: Creating a new job for each call
for query in queries:
    wrapper.create_job()
    wrapper.make_llm_call(...)
    wrapper.complete_job()
```

### 2. Purpose Tracking

```python
# ✅ GOOD: Descriptive purposes for each call
wrapper.make_llm_call(
    messages=messages,
    purpose="initial_research"
)

wrapper.make_llm_call(
    messages=messages,
    purpose="follow_up_analysis"
)

# ❌ BAD: No purpose or generic purposes
wrapper.make_llm_call(messages=messages)
wrapper.make_llm_call(messages=messages, purpose="call")
```

### 3. Error Handling

```python
# ✅ GOOD: Proper error handling
try:
    wrapper.create_job(metadata={"task": "analysis"})
    result = wrapper.make_llm_call(messages)
    wrapper.complete_job(status="completed")
except Exception as e:
    wrapper.complete_job(status="failed", error=str(e))
    raise
```

### 4. Metadata Usage

```python
# ✅ GOOD: Rich metadata for tracking
wrapper.create_job(metadata={
    "agent_framework": "langchain",
    "agent_type": "conversational",
    "user_id": "user_123",
    "session_id": "session_456",
    "conversation_topic": "customer_support"
})
```

## Framework Comparison

| Framework | Best Use Case | Integration Complexity | Example |
|-----------|---------------|----------------------|---------|
| **LangChain** | Chains, RAG, general agents | Medium | Document analysis, Q&A |
| **AutoGen** | Multi-agent conversations | Medium | Team collaboration, debates |
| **CrewAI** | Role-based agent crews | High | Complex workflows, tasks |
| **Custom** | Specific business logic | Low | Custom agent implementations |

## Next Steps

1. **[Full Chain Example](full-chain.md)** - Complete workflow walkthrough
2. **[Streaming Examples](streaming-examples.md)** - Real-time agent responses
3. **[Structured Outputs](structured-outputs.md)** - Type-safe agent outputs
4. **[Error Handling](../integration/error-handling.md)** - Production error handling
5. **[Best Practices](../integration/best-practices.md)** - Production deployment guide
