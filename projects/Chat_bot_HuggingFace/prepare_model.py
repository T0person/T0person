import argparse
from os import getenv
from transformers import BitsAndBytesConfig  # Квантизация модели
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from huggingface_hub import login  # Логинация Huggingface


def save_model_HF(model_name: str, quantization_config: BitsAndBytesConfig):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, quantization_config=quantization_config
    )
    save_dir = model_name.split("/")[1]
    # Сохраняю модель
    model.save_pretrained(save_dir)
    tokenizer.save_pretrained(save_dir)


def quantizate_4bit():
    # Определяем параметры квантования, вес модели уменьшается в 4 раза
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,  # Используем 4-битное квантование
        bnb_4bit_compute_dtype=torch.bfloat16,  # Квантование будет производиться на этои типе (на новом оборудовании возможно увеличить точности и скорость)
        bnb_4bit_quant_type="nf4",  # тип данных 4-битные числа с плавающей запятой
        bnb_4bit_use_double_quant=True,  # Использование двойного квантования
    )
    return quantization_config


def quantizate_8bit():
    # Определяем параметры квантования, вес модели уменьшается в 2 раза
    quantization_config = BitsAndBytesConfig(
        load_in_8bit=True,  # Используем 8-битное квантование
    )
    return quantization_config


def main():
    # Определение парсера
    parser = argparse.ArgumentParser(
        description="Скрипт для квантизации моделей из HuggingFace. Квантизация 8bit - более точнее, но занимает больше памяти"
    )

    # Определение аргументов для парсинга
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        nargs=1,
        metavar="path",
        default="mistralai/Mistral-Nemo-Instruct-2407",
        help="Путь к модели с HuggingFace, по умолчанию:  mistralai/Mistral-Nemo-Instruct-2407",
    )

    parser.add_argument(
        "-t",
        "--token",
        type=str,
        nargs=1,
        metavar="str",
        default=getenv("HF_TOKEN"),
        help="HuggingFace токен в виде: 'hf_....', по умолчанию: существующий токен",
    )
    parser.add_argument(
        "-q",
        "--quant",
        type=bool,
        nargs=1,
        metavar="bool",
        default=False,
        help="Квантизация модели в 4bit, по умолчанию: 8bit",
    )
    # Получение аргументов
    args = parser.parse_args()

    # Логинация HuggingFace, не все модели доступны без логинации
    # Возможно на сайте необходимо получить дополнительное разрешение
    login(args.token)

    # 4-битное квантование
    if args.quant[0] == True:
        quantization_config = quantizate_4bit(model_name=args.model)

    # 8-битное квантование
    quantization_config = quantizate_8bit(model_name=args.model)

    save_model_HF(args.model, quantization_config)


if __name__ == "__main__":
    main()
