from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain.chat_models import init_chat_model
from utils import Build_RAG  # Build_LLM
import os


@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Получить информацию, связанную с запросом."""
    retrieved_docs = retriever.invoke(query)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
        for doc in retrieved_docs
    )
    print(f"serialized: {serialized}")
    print(f"retrieved_docs: {retrieved_docs}")
    return serialized, retrieved_docs


if __name__ == "__main__":

    if not os.environ.get("MISTRAL_API_KEY"):
        print("Ошибка")
        exit()
        # os.environ["MISTRAL_API_KEY"] = getpass.getpass("Enter API key for Mistral AI: ")

    model = init_chat_model("mistral-large-latest", model_provider="mistralai")

    # model = Build_LLM()
    # chat_model = model.get_model()

    # Получение ретривера
    rag = Build_RAG()
    retriever = rag.get_retriever()

    memory = MemorySaver()

    agent_executor = create_react_agent(model, [retrieve], checkpointer=memory)
    # display(Image(agent_executor.get_graph().draw_mermaid_png()))

    config = {"configurable": {"thread_id": "def234"}}

    input_message = (
        "Что понимается под актуальными угрозами безопасности персональных данных?\n\n"
        "Как только ты получишь ответ, посмотри общие расширения этого метода."
    )

    for event in agent_executor.stream(
        {"messages": [{"role": "user", "content": input_message}]},
        stream_mode="values",
        config=config,
    ):
        print(event["messages"][-1].pretty_print())
