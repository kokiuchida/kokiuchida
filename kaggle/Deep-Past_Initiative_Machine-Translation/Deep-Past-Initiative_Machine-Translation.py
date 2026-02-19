import os
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, 
    AutoModelForSeq2SeqLM, 
    Seq2SeqTrainingArguments, 
    Seq2SeqTrainer,
    DataCollatorForSeq2Seq
)
from datasets import load_metric

# 1. 設定
MODEL_NAME = "facebook/mbart-large-50-many-to-many-mmt" # または google/byt5-small
SOURCE_LANG = "ja_XX"  # コンペのデータに合わせて変更
TARGET_LANG = "en_XX"
MAX_LENGTH = 128
BATCH_SIZE = 8

class TranslationDataset(Dataset):
    def __init__(self, df, tokenizer, src_col, trg_col, max_length):
        self.df = df
        self.tokenizer = tokenizer
        self.src_col = src_col
        self.trg_col = trg_col
        self.max_length = max_length

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        src_text = self.df.iloc[idx][self.src_col]
        trg_text = self.df.iloc[idx][self.trg_col]

        inputs = self.tokenizer(
            src_text, 
            max_length=self.max_length, 
            padding="max_length", 
            truncation=True, 
            return_tensors="pt"
        )
        labels = self.tokenizer(
            text_target=trg_text, 
            max_length=self.max_length, 
            padding="max_length", 
            truncation=True, 
            return_tensors="pt"
        )

        model_inputs = {k: v.squeeze(0) for k, v in inputs.items()}
        model_inputs["labels"] = labels["input_ids"].squeeze(0)
        return model_inputs

# 2. メイン処理
def train():
    # データの読み込み (Kaggleのパスに合わせて変更)
    train_df = pd.read_csv("/kaggle/input/deep-past-initiative-machine-translation/train.csv")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

    # データの準備
    train_dataset = TranslationDataset(train_df, tokenizer, "source_text", "target_text", MAX_LENGTH)
    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    # 3. 学習設定 (プロの設定)
    training_args = Seq2SeqTrainingArguments(
        output_dir="./results",
        evaluation_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        weight_decay=0.01,
        save_total_limit=3,
        num_train_epochs=5,
        predict_with_generate=True,
        fp16=True, # GPUメモリ節約と高速化
        push_to_hub=False,
        report_to="none"
    )

    # 評価指標 (BLEU scoreなど)
    metric = load_metric("bleu")

    def compute_metrics(eval_preds):
        preds, labels = eval_preds
        if isinstance(preds, tuple):
            preds = preds[0]
        decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
        
        # 簡易的な前処理
        decoded_preds = [pred.strip().split() for pred in decoded_preds]
        decoded_labels = [[label.strip().split()] for label in decoded_labels]
        
        result = metric.compute(predictions=decoded_preds, references=decoded_labels)
        return {"bleu": result["bleu"]}

    # 4. トレーナーの実行
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    trainer.train()

if __name__ == "__main__":
    train()
