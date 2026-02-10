import pandas as pd
import ftfy
from emoji import demojize, emojize
import re
import unicodedata
from functools import partial
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator
import warnings

# Suppress langdetect warnings
warnings.filterwarnings("ignore", category=UserWarning, module='langdetect')

# Define comprehensive emoji Unicode ranges
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251" 
    "]+",
    flags=re.UNICODE
)

# Pattern to detect common encoding artifacts
ENCODING_ARTIFACT_PATTERN = re.compile(
    r'â\w+|ð\w+|Ã\w+|â€|â€|â\w+|â\w+|\x80|\x93|\x94|\x99|\x9c|\x9d'
)

def detect_language(text):
    """Detect language of a text with error handling"""
    try:
        return detect(text) if isinstance(text, str) and text.strip() else None
    except LangDetectException:
        return None

translation_cache = {}

def translate_to_english(text, source_lang='auto'):
    """Translate text to English with emoji preservation"""
    if not isinstance(text, str) or not text.strip():
        return text
        
    if text in translation_cache:
        return translation_cache[text]
        
    try:
        # Extract emojis before translation
        emojis = ''.join(EMOJI_PATTERN.findall(text))
        text_without_emojis = EMOJI_PATTERN.sub('', text)
        
        # Translate only the non-emoji text
        translated = GoogleTranslator(source=source_lang, target='en').translate(text_without_emojis)
        
        # Combine translated text with original emojis
        result = f"{translated if translated else text_without_emojis} {emojis}".strip()
        translation_cache[text] = result
        return result
    except Exception as e:
        print(f"Translation failed for text: {text[:50]}... Error: {e}")
        return None  # Return None to indicate failed translation

def fix_encoding_emojis(text):
    """
    Correct encoding artifacts and standardize emojis while preserving sentiment cues.
    Args:
        text (str): Raw review text
    Returns:
        str: Cleaned text with proper encoding and standardized emojis
    """
    if not isinstance(text, str) or pd.isna(text):
        return text
    
    # Fix encoding issues and normalize Unicode
    text = ftfy.fix_text(text)
    text = unicodedata.normalize('NFKC', text)
    
    # Standardize emojis while preserving their sentiment value
    text = emojize(demojize(text))
    
    # Remove any remaining encoding artifacts
    text = ENCODING_ARTIFACT_PATTERN.sub('', text)
    
    return text

def clean_text(text, preserve_case_for=None):
    """
    Clean review text while preserving sentiment signals and emojis.
    Args:
        text (str): Text to clean
        preserve_case_for (list): Words to preserve case for (e.g., negations)
    Returns:
        str: Cleaned text ready for sentiment analysis
    """
    if not isinstance(text, str) or pd.isna(text):
        return text
    
    # Fix any remaining encoding issues
    text = fix_encoding_emojis(text)
    
    # Extract emojis first
    emojis = ''.join(EMOJI_PATTERN.findall(text))
    text_without_emojis = EMOJI_PATTERN.sub('', text)
    
    # Preserve case for important sentiment words if specified
    if preserve_case_for:
        for word in preserve_case_for:
            text_without_emojis = re.sub(rf'\b{word}\b', word.upper(), text_without_emojis, flags=re.IGNORECASE)
    
    # Remove URLs and HTML tags
    text_without_emojis = re.sub(r'http\S+|www\S+|@\w+|<.*?>', '', text_without_emojis)
    
    # Keep sentiment-relevant punctuation
    text_without_emojis = re.sub(r'[^\w\s!?…]', ' ', text_without_emojis)
    
    # Handle common contractions
    contractions = {
        r"won't": "will not",
        r"can't": "cannot",
        r"n't": " not",
        r"'re": " are",
        r"'s": " is",
        r"'d": " would",
        r"'ll": " will",
        r"'t": " not",
        r"'ve": " have",
        r"'m": " am"
    }
    for pattern, replacement in contractions.items():
        text_without_emojis = re.sub(pattern, replacement, text_without_emojis)
    
    # Normalize whitespace and lowercase (except preserved words)
    text_without_emojis = ' '.join(text_without_emojis.split())
    if not preserve_case_for:
        text_without_emojis = text_without_emojis.lower()
    
    # Recombine with emojis
    result = f"{text_without_emojis} {emojis}".strip()
    
    # Remove any remaining encoding artifacts
    result = ENCODING_ARTIFACT_PATTERN.sub('', result)
    
    return result if result.strip() else None

def preprocess_reviews_df(df, sentiment_words=None, translate_threshold=0.3):
    """
    Preprocess all reviews in the DataFrame with language handling.
    Args:
        df (pd.DataFrame): Input DataFrame with movies as columns
        sentiment_words (list): Words to preserve case for
        translate_threshold (float): Threshold for reporting translation decisions
    Returns:
        pd.DataFrame: Processed DataFrame with cleaned reviews
    """
    # Create cleaning function with sentiment words preserved
    cleaner = partial(clean_text, preserve_case_for=sentiment_words)
    
    # First pass: basic cleaning
    df = df.applymap(fix_encoding_emojis)
    
    # Language handling - now always translates non-English reviews
    for movie_col in df.columns:
        reviews = df[movie_col].dropna()
        if len(reviews) == 0:
            continue
            
        # Detect languages
        languages = reviews.apply(detect_language)
        non_english_pct = (languages != 'en').mean()
        
        if non_english_pct > 0:  # Always translate if non-English exists
            print(f"Translating {movie_col} ({non_english_pct:.1%} non-English)")
            df[movie_col] = df[movie_col].apply(
                lambda x: translate_to_english(x) if isinstance(x, str) and detect_language(x) != 'en' else x
            )
            
            # Remove reviews that couldn't be translated (returned None)
            df[movie_col] = df[movie_col].apply(
                lambda x: x if x is not None and (not isinstance(x, str) or detect_language(x) == 'en') else None
            )
    
    # Final cleaning pass
    df = df.applymap(cleaner)
    
    # Remove any rows that are now empty after cleaning
    df = df.dropna(how='all')
    
    return df

def validate_cleanliness(df):
    """
    Validate that no encoding artifacts remain and sentiment cues are preserved.
    Args:
        df (pd.DataFrame): Processed DataFrame to validate
    """
    # Check for residual encoding artifacts
    mojibake_pattern = re.compile(r'â\w+|ð\w+')
    emoji_preservation = 0
    non_english_count = 0
    
    for col in df.columns:
        # Get non-null reviews
        non_null_reviews = df[col].dropna()
        if len(non_null_reviews) == 0:
            continue  # Skip empty columns
            
        # Sample up to 5 reviews (or all if there are fewer than 5)
        sample_size = min(5, len(non_null_reviews))
        sample = non_null_reviews.sample(sample_size) if sample_size > 0 else []
        
        for text in sample:
            if mojibake_pattern.search(str(text)):
                print(f"Warning: Possible residual encoding artifact in {col}")
                print(f"Sample text: {text[:100]}...")
            
            # Emoji check
            emojis = EMOJI_PATTERN.findall(text)
            if emojis:
                emoji_preservation += len(emojis)
                print(f"Found emojis in {col}: {', '.join(set(emojis))}")
            
            # Language check
            lang = detect_language(text)
            if lang != 'en':
                non_english_count += 1
                print(f"Warning: Non-English text found in {col}: {text[:100]}... (Language: {lang})")
    
    print(f"\nValidation complete. Found {emoji_preservation} emojis preserved in total.")
    print(f"Found {non_english_count} non-English reviews remaining after processing.")

def main(input_csv, output_csv):
    """
    Main preprocessing pipeline.
    Args:
        input_csv (str): Path to input CSV file
        output_csv (str): Path to save processed CSV
    """
    # Words to preserve case for (negations and strong sentiment words)
    SENTIMENT_WORDS = ['not', 'no', 'never', 'nothing', 'without', 
                      'love', 'hate', 'awesome', 'terrible']
    
    # Load data
    print(f"Loading data from {input_csv}...")
    df = pd.read_csv(input_csv)
    
    # Preprocess reviews with language handling
    print("Preprocessing reviews with language detection...")
    df_clean = preprocess_reviews_df(df, sentiment_words=SENTIMENT_WORDS)
    
    # Validate results
    print("Validating cleaned data...")
    validate_cleanliness(df_clean)
    
    # Save results with explicit UTF-8 encoding
    df_clean.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Cleaned data saved to {output_csv}")
    
    # Print samples for manual verification
    print("\nSample cleaned reviews:")
    for col in df_clean.columns[:3]:  # Show first 3 movies
        sample = df_clean[col].dropna().sample(1).values[0] if len(df_clean[col].dropna()) > 0 else "[No reviews remaining]"
        print(f"\n{col}: {sample[:200]}{'...' if isinstance(sample, str) and len(sample) > 200 else ''}")

if __name__ == "__main__":
    INPUT_CSV = "RawReviews.csv"  # Input CSV with movies as columns
    OUTPUT_CSV = "CleanedReviews.csv"  # Output CSV
    
    main(INPUT_CSV, OUTPUT_CSV)    

