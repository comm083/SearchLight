import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration, AutoTokenizer, AutoModelForSeq2SeqLM

class ImageCaptioner:
    def __init__(self, device=None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"Initializing ImageCaptioner on {self.device}...")
        
        # Load BLIP model for image captioning
        self.caption_model_id = "Salesforce/blip-image-captioning-base"
        self.processor = BlipProcessor.from_pretrained(self.caption_model_id)
        self.model = BlipForConditionalGeneration.from_pretrained(self.caption_model_id).to(self.device)
        
        # Load Translation model (Multilingual NLLB-200)
        self.trans_model_id = "facebook/nllb-200-distilled-600M"
        self.trans_tokenizer = AutoTokenizer.from_pretrained(self.trans_model_id)
        self.trans_tokenizer.src_lang = "eng_Latn"
        self.trans_model = AutoModelForSeq2SeqLM.from_pretrained(self.trans_model_id).to(self.device)
        self.target_lang = "kor_Hang"

    def describe_image(self, image_path: str) -> str:
        """Generates a one-sentence Korean description of the image."""
        try:
            raw_image = Image.open(image_path).convert('RGB')
            
            # 1. Generate English Caption
            inputs = self.processor(raw_image, return_tensors="pt").to(self.device)
            out = self.model.generate(**inputs)
            en_caption = self.processor.decode(out[0], skip_special_tokens=True)
            
            # 2. Translate to Korean
            inputs = self.trans_tokenizer(en_caption, return_tensors="pt").to(self.device)
            translated_tokens = self.trans_model.generate(
                **inputs, 
                forced_bos_token_id=self.trans_tokenizer.convert_tokens_to_ids(self.target_lang), 
                max_length=128
            )
            ko_caption = self.trans_tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
            
            return ko_caption
        except Exception as e:
            print(f"Error describing image {image_path}: {e}")
            return "이미지를 분석할 수 없습니다."

if __name__ == "__main__":
    # Test code
    import os
    test_image = os.path.join("backend", "static", "images", "normal1.png")
    if os.path.exists(test_image):
        captioner = ImageCaptioner()
        result = captioner.describe_image(test_image)
        print(f"Image: {test_image}")
        print(f"Description: {result}")
    else:
        print(f"Test image not found at {test_image}")
