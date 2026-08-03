from typing import List

from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage, HumanMessage, ToolMessage
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from backend.src.custom_tools import get_db_tools
from backend.src.graph_manager import SchemaGraph
from backend.src.prompt_module import (
    answer_validation_prompt_module,
    generate_query_prompt_module,
    select_table_prompt_module,
)
from backend.src.rag_manager import SchemaRAG
from backend.utils.config import settings
from backend.utils.custom_exception import CustomException
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SQLAgentGenerator:
    """LangGraph-based SQL Agent using Google Gemini 3.5 Flash."""

    def __init__(self, model_name: str = "google_genai:gemini-3.5-flash"):
        self.model_name = model_name

        if not settings.gemini_api_key:
            raise CustomException("GEMINI_API_KEY is not set in environment")

        self.llm = self._setup_llm()
        self.db = self._setup_database()
        self.rag = SchemaRAG(self.db)
        self.graph_manager = SchemaGraph(self.db)
        self.tools = self._setup_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

        logger.info(f"SQL Agent Initialized with model: {self.model_name}")

    def _setup_llm(self):
        logger.info(f"Initializing Gemini model: {self.model_name}")
        return init_chat_model(self.model_name, temperature=0)

    def _setup_database(self) -> SQLDatabase:
        try:
            db_uri = settings.database_uri
            return SQLDatabase.from_uri(db_uri, sample_rows_in_table_info=0)
        except Exception as e:
            logger.error("Error setting up database")
            raise CustomException("Error setting up database", e)

    def _setup_tools(self) -> List:
        toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        standard_tools = toolkit.get_tools()
        custom_tools = get_db_tools(self.db, self.rag, self.graph_manager)
        return standard_tools + custom_tools

    def list_tables_node(self, state: MessagesState):
        return {"messages": []}

    def call_get_schema_node(self, state: MessagesState):
        system_prompt = select_table_prompt_module()
        system_message = {"role": "system", "content": system_prompt}

        tools = [self.tool_map["sql_db_find_relevant_tables"], self.tool_map["sql_db_schema"]]
        llm_with_tools = self.llm.bind_tools(tools)

        response = llm_with_tools.invoke([system_message] + state["messages"])
        return {"messages": [response]}

    def generate_query_node(self, state: MessagesState):
        org_id = state.get("user_context", {}).get("org_id", 16)
        base_prompt = generate_query_prompt_module(self.db, org_id=org_id)

        instruction = """
        \n\n### EXECUTION PLAN
        1. **RESEARCH PHASE:** If you don't know table names, use `sql_db_find_relevant_tables`.
        2. **CONNECTION PHASE:** If you don't know how to join tables, use `sql_db_find_table_connections`.
        3. **EXECUTION PHASE (CRITICAL):** Once you have the table names and join logic, you **MUST** run `sql_db_query`.
           - **DO NOT STOP** after finding the schema or join path.
           - You have not answered the user until you have run a SELECT query and received actual data rows.
        4. **SECURITY:** You MUST filter by the Organization ID provided in the system prompt.

        ### DATA RULES
        - Use `LIMIT 10` for all queries.
        - For Binary IDs (like patient_id), use `BIN_TO_UUID(col)` or `HEX(col)`.
        """

        system_message = {"role": "system", "content": base_prompt + instruction}

        tools_to_bind = [
            self.tool_map["sql_db_query"],
            self.tool_map["sql_db_query_distinct_values"],
            self.tool_map["sql_db_sample_rows"],
            self.tool_map["sql_db_find_relevant_tables"],
            self.tool_map["sql_db_find_table_connections"],
            self.tool_map["sql_db_get_foreign_keys"],
            self.tool_map["sql_db_get_column_info"],
            self.tool_map["sql_db_find_value_location"],
        ]
        llm_with_tools = self.llm.bind_tools(tools_to_bind)
        response = llm_with_tools.invoke([system_message] + state["messages"])

        return {"messages": [response]}

    def check_query_node(self, state: MessagesState):
        last_message = state["messages"][-1]
        if not last_message.tool_calls:
            content = last_message.content.strip()
            if any(content.upper().startswith(kw) for kw in ["SELECT", "INSERT", "UPDATE", "DELETE"]):
                logger.warning("Detected raw SQL text. Converting to tool_call...")
                if "LIMIT" not in content.upper():
                    content += " LIMIT 10"

                import os as _os

                manual_tool_call = {
                    "id": "manual_sql_fix_" + _os.urandom(4).hex(),
                    "name": "sql_db_query",
                    "args": {"query": content},
                    "type": "tool_call",
                }
                return {"messages": [AIMessage(content="", tool_calls=[manual_tool_call])]}
            return {"messages": []}

        tool_call = last_message.tool_calls[0]
        tool_name = tool_call["name"]

        REASONING_TOOLS = [
            "sql_db_query_distinct_values",
            "sql_db_sample_rows",
            "sql_db_find_relevant_tables",
            "sql_db_schema",
            "sql_db_get_foreign_keys",
            "sql_db_get_column_info",
            "sql_db_find_table_connections",
        ]
        if tool_name in REASONING_TOOLS:
            return {"messages": []}

        if tool_name == "sql_db_query":
            proposed_query = tool_call["args"].get("query", "")
            if "LIMIT" not in proposed_query.upper():
                proposed_query += " LIMIT 10"
                return {
                    "messages": [
                        AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "id": tool_call["id"],
                                    "name": "sql_db_query",
                                    "args": {"query": proposed_query},
                                    "type": "tool_call",
                                }
                            ],
                        )
                    ]
                }

        return {"messages": []}

    def validate_answer_node(self, state: MessagesState):
        last_message = state["messages"][-1]

        if isinstance(last_message, AIMessage) and not last_message.tool_calls:
            content_lower = last_message.content.lower()

            premature_exit_phrases = [
                "no matching records",
                "no data was found",
                "no medicaid patients",
                "no patients",
                "could not find",
            ]

            if any(phrase in content_lower for phrase in premature_exit_phrases):
                user_question = "Unknown"
                for msg in reversed(state["messages"]):
                    if isinstance(msg, HumanMessage) and not msg.content.startswith("SYSTEM"):
                        user_question = msg.content
                        break

                recent_tool_calls = []
                for msg in reversed(state["messages"][-10:]):
                    if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                        recent_tool_calls.extend([tc["name"] for tc in msg.tool_calls])

                if "sql_db_query" not in recent_tool_calls:
                    logger.warning("Agent terminated without executing sql_db_query. Forcing retry.")

                    return {
                        "messages": [
                            HumanMessage(
                                content=f"""SYSTEM FEEDBACK: You aborted without running a SELECT query.

    You used helper tools ({", ".join(set(recent_tool_calls))}) but never executed the actual data retrieval.

    MANDATORY NEXT STEP: Use sql_db_query to run the following query structure:

    For '{user_question}', build a query that:
    1. JOINs the necessary tables (patient, map_patient_metrics, lob, patient_score, etc.)
    2. Filters WHERE conditions match the user's criteria
    3. Orders and limits results appropriately
    4. Uses HEX() or BIN_TO_UUID() for any BINARY columns

    Execute the query NOW with sql_db_query."""
                            )
                        ]
                    }

        if isinstance(last_message, ToolMessage):
            if len(state["messages"]) >= 2:
                last_ai_msg = None
                for msg in reversed(state["messages"][:-1]):
                    if isinstance(msg, AIMessage):
                        last_ai_msg = msg
                        break

                if last_ai_msg and hasattr(last_ai_msg, "tool_calls") and last_ai_msg.tool_calls:
                    tool_name = last_ai_msg.tool_calls[0]["name"]
                    HELPER_TOOLS = [
                        "sql_db_find_relevant_tables",
                        "sql_db_find_table_connections",
                        "sql_db_schema",
                        "sql_db_get_foreign_keys",
                        "sql_db_get_column_info",
                        "sql_db_query_distinct_values",
                        "sql_db_sample_rows",
                    ]

                    if tool_name in HELPER_TOOLS:
                        return {
                            "messages": [
                                HumanMessage(
                                    content=f"SYSTEM FEEDBACK: Research tool '{tool_name}' complete. You have gathered information. NOW you MUST write and execute 'sql_db_query' to get the actual data rows that answer the user's question."
                                )
                            ]
                        }

        if not isinstance(last_message, ToolMessage) or last_message.name != "sql_db_query":
            return {"messages": []}

        sql_result = last_message.content

        if "b'\\" in sql_result or "bytearray" in str(sql_result).lower():
            logger.warning("Binary data detected in output. Triggering immediate retry.")
            return {
                "messages": [
                    HumanMessage(
                        content="SYSTEM FEEDBACK: Binary data detected (b'\\x00...'). Retry using HEX(column) or BIN_TO_UUID(column)."
                    )
                ]
            }

        user_question = "Unknown"
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage) and not msg.content.startswith("SYSTEM"):
                user_question = msg.content
                break

        generated_query = "Unknown"
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                if msg.tool_calls[0]["name"] == "sql_db_query":
                    generated_query = msg.tool_calls[0]["args"].get("query")
                    break

        validation_prompt = answer_validation_prompt_module().format(
            question=user_question, query=generated_query, result=sql_result
        )

        validation_response = self.llm.invoke(validation_prompt)

        if "STATUS: RETRY" in validation_response.content:
            logger.info("Validator Triggered Retry")
            retry_count = sum(
                1 for msg in state["messages"] if isinstance(msg, HumanMessage) and "FEEDBACK" in msg.content
            )

            if retry_count >= 3:
                return {
                    "messages": [
                        AIMessage(content="Maximum retries reached. I will try to answer with the data I have.")
                    ]
                }

            feedback_text = validation_response.content.split("FEEDBACK:")[-1].strip()
            return {"messages": [HumanMessage(content=f"Validator Feedback: {feedback_text}")]}

        return {"messages": [validation_response]}

    def generate_final_answer_node(self, state: MessagesState):
        user_question = "Unknown"
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage) and not msg.content.startswith("SYSTEM"):
                user_question = msg.content
                break

        sql_result = "No data found."
        for msg in reversed(state["messages"]):
            if isinstance(msg, ToolMessage) and msg.name == "sql_db_query":
                sql_result = msg.content
                break

        prompt = f"""
        User Question: {user_question}
        SQL Result: {sql_result}

        Provide a concise, natural language answer.
        - If the result is a list, summarize it.
        - If the result is empty, explain that no matching records were found.
        """
        final_response = self.llm.invoke(prompt)
        return {"messages": [final_response]}

    def should_continue(self, state: MessagesState) -> str:
        last_message = state["messages"][-1]
        if not last_message.tool_calls:
            return "end"
        return "check_query"

    def should_retry(self, state: MessagesState) -> str:
        last_message = state["messages"][-1]

        if isinstance(last_message, HumanMessage) and (
            "FEEDBACK" in last_message.content or "Validator" in last_message.content
        ):
            return "generate_query"

        if isinstance(last_message, AIMessage) and "STATUS: VALID" in last_message.content:
            return "generate_final_answer"

        return "generate_final_answer"

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(MessagesState)
        tools_node = ToolNode(self.tools)

        workflow.add_node("list_tables", self.list_tables_node)
        workflow.add_node("call_get_schema", self.call_get_schema_node)
        workflow.add_node("get_schema", tools_node)
        workflow.add_node("generate_query", self.generate_query_node)
        workflow.add_node("check_query", self.check_query_node)
        workflow.add_node("run_tools", tools_node)
        workflow.add_node("validate_answer", self.validate_answer_node)
        workflow.add_node("generate_final_answer", self.generate_final_answer_node)

        workflow.add_edge(START, "list_tables")
        workflow.add_edge("list_tables", "call_get_schema")
        workflow.add_edge("call_get_schema", "get_schema")
        workflow.add_edge("get_schema", "generate_query")

        workflow.add_conditional_edges(
            "generate_query", self.should_continue, {"check_query": "check_query", "end": END}
        )

        workflow.add_edge("check_query", "run_tools")
        workflow.add_edge("run_tools", "validate_answer")

        workflow.add_conditional_edges(
            "validate_answer",
            self.should_retry,
            {"generate_query": "generate_query", "generate_final_answer": "generate_final_answer"},
        )

        workflow.add_edge("generate_final_answer", END)

        return workflow.compile(checkpointer=self.checkpointer)

    def run(
        self,
        question: str,
        session_id: str = "default_session",
        config: RunnableConfig = None,
        org_id: int | None = None,
    ) -> str:
        config = config or {}
        config["configurable"] = {"thread_id": session_id}
        config["recursion_limit"] = 50

        logger.info(f"Session: {session_id} | Query: {question}")

        initial_state = {
            "messages": [{"role": "user", "content": question}],
            "user_context": {"org_id": org_id},
        }

        final_response_content = ""

        try:
            for step in self.graph.stream(initial_state, config=config, stream_mode="values"):
                last_msg = step["messages"][-1]
                last_msg.pretty_print()

                if isinstance(last_msg, AIMessage) and not last_msg.tool_calls and "STATUS:" not in last_msg.content:
                    final_response_content = last_msg.content
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            final_response_content = f"I encountered an error: {str(e)}"

        return final_response_content
