#!/usr/bin/env python3
"""
Wikipedia Translation Script - Hunyuan-MT-7B
Translates English Wikipedia summaries to Chinese using local LLM.
Optimized for Apple Silicon (M3 Max with MPS backend).
"""

import sqlite3
import time
import logging
from datetime import datetime

# Configuration
DB_PATH = 'birdid/data/bird_reference.sqlite'
LOG_FILE = 'translation.log'
MODEL_PATH = "tencent/Hunyuan-MT-7B"
CHECKPOINT_INTERVAL = 10  # Print progress every 10 birds

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# Lazy load model (only when needed)
_model = None
_tokenizer = None

def load_model():
    global _model, _tokenizer
    if _model is None:
        logging.info("Loading Hunyuan-MT-7B model (this may take a few minutes)...")
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        
        # For Apple Silicon, use MPS backend
        if torch.backends.mps.is_available():
            logging.info("Using MPS (Apple Silicon) backend")
            _model = AutoModelForCausalLM.from_pretrained(
                MODEL_PATH, 
                torch_dtype=torch.float16,  # Use float16 for M3 Max
                device_map="mps"
            )
        else:
            logging.info("MPS not available, using CPU")
            _model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)
        
        logging.info("Model loaded successfully!")
    return _model, _tokenizer

def translate(text):
    """Translate English text to Chinese using Hunyuan-MT-7B."""
    model, tokenizer = load_model()
    
    # Official prompt template from GitHub
    messages = [
        {"role": "user", "content": f"Translate the following segment into Chinese, without additional explanation.\n\n{text}"}
    ]
    
    tokenized = tokenizer.apply_chat_template(
        messages, 
        tokenize=True, 
        add_generation_prompt=False, 
        return_tensors="pt"
    ).to(model.device)
    
    outputs = model.generate(
        tokenized,
        max_new_tokens=1024,
        top_k=20,
        top_p=0.6,
        temperature=0.7,
        repetition_penalty=1.05,
        do_sample=True
    )
    
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract only the translated part (after the prompt)
    # The output typically contains the prompt + translation
    if "Chinese" in result and "explanation" in result:
        # Try to extract just the translation
        parts = result.split("\n\n")
        if len(parts) > 1:
            result = parts[-1].strip()
    
    return result

def translate_all():
    """Translate all English Wikipedia summaries to Chinese."""
    start_time = datetime.now()
    logging.info("=" * 60)
    logging.info(f"Starting TRANSLATION at {start_time}")
    logging.info("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if column exists, if not create it
    cursor.execute("PRAGMA table_info(BirdCountInfo)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'wikipedia_intro_zh_translated' not in columns:
        cursor.execute("ALTER TABLE BirdCountInfo ADD COLUMN wikipedia_intro_zh_translated TEXT")
        conn.commit()
        logging.info("Added column 'wikipedia_intro_zh_translated'")
    
    # Get records that have English but no Chinese translation
    cursor.execute("""
        SELECT id, english_name, wikipedia_intro_en 
        FROM BirdCountInfo 
        WHERE wikipedia_intro_en IS NOT NULL 
          AND wikipedia_intro_en != 'NOT_FOUND'
          AND (wikipedia_intro_zh_translated IS NULL OR wikipedia_intro_zh_translated = '')
        ORDER BY id ASC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        logging.info("All translations complete!")
        return
    
    logging.info(f"Records to translate: {len(rows)}")
    logging.info("-" * 60)
    
    success_count = 0
    
    for idx, row in enumerate(rows, 1):
        bid, en_name, en_text = row
        
        try:
            # Translate
            zh_text = translate(en_text)
            
            # Save to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE BirdCountInfo SET wikipedia_intro_zh_translated = ? WHERE id = ?", 
                (zh_text, bid)
            )
            conn.commit()
            conn.close()
            
            success_count += 1
            status = "✅"
            
        except Exception as e:
            logging.error(f"Error translating ID {bid}: {e}")
            status = "❌"
        
        # Progress report
        if idx % CHECKPOINT_INTERVAL == 0 or idx == len(rows):
            elapsed = datetime.now() - start_time
            rate = idx / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0
            eta_minutes = (len(rows) - idx) / rate if rate > 0 else 0
            logging.info(f"[{idx}/{len(rows)}] {status} ID {bid}: {en_name[:25]}... | Rate: {rate:.1f}/min | ETA: {eta_minutes:.0f}min")
    
    # Final report
    end_time = datetime.now()
    duration = end_time - start_time
    logging.info("=" * 60)
    logging.info(f"COMPLETED at {end_time}")
    logging.info(f"Duration: {duration}")
    logging.info(f"Successfully translated: {success_count}/{len(rows)}")
    logging.info("=" * 60)

def test_translation():
    """Test translation with a single example."""
    test_text = "The black-faced warbler is a species of bush warbler. It is found in Bhutan, China, India, Myanmar, Nepal, and Vietnam."
    print(f"English: {test_text}")
    print(f"Chinese: {translate(test_text)}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_translation()
    else:
        translate_all()
