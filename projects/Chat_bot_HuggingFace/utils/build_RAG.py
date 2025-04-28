from os import getenv
import torch
from langchain_huggingface import (
    HuggingFaceEmbeddings,
)  # Embedding model из huggingface с помощью langchain
from langchain_community.document_loaders import DirectoryLoader  # Загрузчик документов
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)  # Рекурсивный сплиттер текста

from langchain.storage import InMemoryStore  # Хранение в памяти
from langchain_community.vectorstores import FAISS  # Векторная база данных
from langchain_community.retrievers import BM25Retriever  # Ретривер BM25
from langchain.retrievers import EnsembleRetriever  # Ансамбль ретриверов

# from langchain_chroma import Chroma  # Векторная база данных Chroma
# Специальный ретривер для более точечного поиска больших документов
# from langchain.retrievers import ParentDocumentRetriever


class Build_RAG:

    def __init__(self, directory="./Memory_stores/documents"):
        # Получение устройства
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Определение модели эмбенддинга
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=getenv("EMBEDDING_MODEL_NAME"),
            multi_process=True,
            model_kwargs={"device": self.device},
            encode_kwargs={
                "normalize_embeddings": True
            },  # Для лучшего косинусного сходства
        )

        # Определение загрузчика директории
        self.loader = DirectoryLoader(
            directory,  # Директория
            glob="*.txt",  # Конкретный формат файлов (.txt файлы лучше считываются)
            use_multithreading=True,  # Включаем многопоточность
        )

        ### Это для родительского поиска
        # # Этот текстовый сплиттер используется для создания родительских документов
        # self.parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)

        # # Этот текстовый сплиттер используется для создания дочерних документов
        # # Он должен создавать документы меньше, чем родительского сплиттера
        # self.child_splitter = RecursiveCharacterTextSplitter(
        #     chunk_size=200, chunk_overlap=20
        # )

        # Уровень хранения для родительских документов
        # self.store = InMemoryStore()

    def get_retriever(self):

        # Загрузка документов
        documents = self.loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Количество токенов в одном сплите
            chunk_overlap=250,  # Нахлест
            length_function=len,  # Метод расчитывания длины
            is_separator_regex=False,  # При сплите разделители не используются как регулярки
        )

        # Разделение документов
        docs = text_splitter.split_documents(documents)

        # Определение ретриверов
        bm25_retriever = BM25Retriever.from_documents(docs)
        bm25_retriever.k = 1  # Количество выборок

        # Загрузка документов в векторную базу данных
        faiss_vectorstore = FAISS.from_documents(docs, self.embedding_model)

        # Создание ретривера FAISS
        faiss_retriever = faiss_vectorstore.as_retriever(
            search_type="similarity",  # Поиск по семантическому поиску
            search_kwargs={"k": 1},  # Количество выборок
        )

        # Определение ансамбля ретриверов
        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, faiss_retriever],  # Объединение ретриверов
            weights=[0.5, 0.5],
        )
        return ensemble_retriever


### Пробовал через родительские документы, но получилось не очень
# # Определение VectorStore, чтобы использовать для индексации детских кусков
# vectorstore = Chroma(
#     collection_name="split_parents",  # Название коллекции
#     embedding_function=self.embedding_model,  # Модель эмбенддинга
# )

# # Определение ретривера
# retriever = ParentDocumentRetriever(
#     vectorstore=vectorstore,  # Хранение сплитовых документов
#     docstore=self.store,  # Хранение целых документов
#     child_splitter=self.child_splitter,  # Разделитель для дочерних частей документов
#     parent_splitter=self.parent_splitter,  # Разделитель документов
#     search_kwargs={"k": 2},  # Количество поисковых частей
# )
# Добавление документов в VectorStore
# retriever.add_documents(documents)

# Возврат готового ретривера
# return retriever
