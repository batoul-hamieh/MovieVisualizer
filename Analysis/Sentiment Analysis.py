import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk


nltk.download('vader_lexicon')

def classify_sentiment(score):
    if score >= 0.05:
        return 'Positive'
    elif score <= -0.05:
        return 'Negative'
    else:
        return 'Neutral'

def analyze_sentiments(input_csv, output_csv):
    df = pd.read_csv(input_csv)
    analyzer = SentimentIntensityAnalyzer()

    results = []

    for movie in df.columns:
        for review in df[movie].dropna():
            score = analyzer.polarity_scores(str(review))['compound']
            label = classify_sentiment(score)
            results.append({
                'movie': movie,
                'review': review,
                'sentiment_score': score,
                'sentiment_label': label
            })

    result_df = pd.DataFrame(results)
    result_df.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"Sentiment results saved to {output_csv}")


if _name_ == "_main_":
    analyze_sentiments(
        input_csv="C:/Users/User/Desktop/scrape/emptyscrapingsira3.csv",
        output_csv="C:/Users/User/Desktop/scrape/sentisira1.csv"
    )
