import os
import pandas as pd
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.retrievers.bm25 import BM25Retriever
import Stemmer
import chromadb
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.readers.string_iterable import StringIterableReader
from llama_index.embeddings.langchain import LangchainEmbedding
from langchain_huggingface import HuggingFaceEmbeddings
from llama_index.vector_stores.chroma import ChromaVectorStore


# Объединение текста из документов для последующего разбиения на ноды и передачи в ретривер
async def file2str():
    # Укажите путь к папке с .txt файлами
    folder_path = "./source/documents"

    # Список всех файлов в папке
    txt_files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]

    # Переменная для хранения объединенного текста
    combined_text = ""

    # Функция для безопасного чтения файлов с разными кодировками
    async def safe_open(file_path):
        encodings = ["utf-8", "latin1", "windows-1251"]  # Пробуем несколько кодировок
        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                continue
        return ""  # Если не удалось открыть, возвращаем пустую строку

    # Чтение и объединение файлов
    for txt_file in txt_files:
        file_path = os.path.join(folder_path, txt_file)
        # Делаем await для получения содержимого файла
        file_content = await safe_open(file_path)
        combined_text += file_content + "\n\n"  # Добавляем два новых строки

    # Теперь combined_text содержит объединенный текст
    return combined_text


async def BM25():
    global query_engine  # Указываем, что используем глобальную переменную
    try:
        # Получаем объединенный текст
        combined_text = await file2str()

        # Если текст пустой, возвращаем ошибку или другое поведение
        if not combined_text:
            raise ValueError("Объединенный текст пустой!")

        # Создаем объект документа с объединенным текстом
        documents = [Document(text=combined_text)]

        # Разбиваем текст на предложения/чанки
        splitter = SentenceSplitter(chunk_size=1024)
        nodes = splitter.get_nodes_from_documents(documents)

        # Создаем хранилище документов
        docstore = SimpleDocumentStore()
        docstore.add_documents(nodes)

        # Создаем BM25-извлекатель
        bm25_retriever = BM25Retriever.from_defaults(
            docstore=docstore,
            similarity_top_k=5,
            stemmer=Stemmer.Stemmer("russian"),
            language="russian",
        )

        # Создаем движок запросов
        query_engine = RetrieverQueryEngine(bm25_retriever)

        return query_engine
    except Exception as e:
        # Обработка исключений
        print(f"Ошибка: {e}")
        query_engine = None


def chat_query_engine():
    df = pd.read_csv("chat_table.csv", index_col=0)

    df["text"] = df[df.columns[1:]].apply(lambda x: "\n\n".join(x.astype(str)), axis=1)

    # Initialize StringIterableReader
    reader = StringIterableReader()

    # Load data from an iterable of strings
    documents = reader.load_data(df["text"].tolist())

    # create client and a new collection
    chroma_client = chromadb.EphemeralClient()
    chroma_collection = chroma_client.create_collection("quickstart")

    # define embedding function
    embed_model = LangchainEmbedding(
        HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
    )

    # set up ChromaVectorStore and load in data
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_documents(
        documents, storage_context=storage_context, embed_model=embed_model
    )

    # Query Data
    query_engine = index.as_query_engine()
    return query_engine
