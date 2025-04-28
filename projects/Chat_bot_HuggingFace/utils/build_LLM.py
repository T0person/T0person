from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline

# import os
# from langchain.chat_models import init_chat_model # Для Мистры
# from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline


class Build_LLM:
    def __init__(self):

        model_name = "./Mistral-Nemo-Instruct-2407"  # Местонахождение модели
        device = "cuda"

        # tokenizer = AutoTokenizer.from_pretrained(model_name, device=device)
        # model = AutoModelForCausalLM.from_pretrained(model_name, device_map=device)
        # pipe = pipeline(
        #     "text-generation", model=model, tokenizer=tokenizer, max_new_tokens=64
        # )
        # self.llm = HuggingFacePipeline(pipeline=pipe)

        self.llm = HuggingFacePipeline.from_model_id(
            model_id=model_name,
            task="text-generation",
            pipeline_kwargs=dict(
                do_sample=True,
                max_new_tokens=256,
                repetition_penalty=1.12,
                temperature=0.2,
                top_k=30,
                top_p=0.9,
                num_beams=2,
                early_stopping=True,
                return_full_text=False,
                device_map=device,
            ),
        )

    def get_model(self):
        return ChatHuggingFace(llm=self.llm)
