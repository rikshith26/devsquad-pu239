import cv2
import numpy as np
import spacy
import re

# Load Pre-trained Deep Learning NLP Model
# 'en_core_web_sm' is a small English pipeline trained on web text
try:
    nlp = spacy.load("en_core_web_sm")
    print("AI Model Loaded: en_core_web_sm")
except:
    print("Downloading AI Model...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# ---------- TEXT SIMILARITY (DEEP SEMANTIC) ----------
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

def text_similarity(text1, text2):
    t1 = preprocess_text(text1)
    t2 = preprocess_text(text2)
    
    if not t1 or not t2:
        return 0.0

    # Process text through the NLP pipeline
    doc1 = nlp(t1)
    doc2 = nlp(t2)
    
    # Calculate Semantic Similarity (Vector Cosine Distance)
    # This understands that "dog" and "puppy" are similar, unlike TF-IDF
    try:
        score = doc1.similarity(doc2)
        return round(float(score), 2)
    except:
        return 0.0

# ---------- COLOR SIMILARITY (HSV Histograms) ----------
def color_similarity(img1_path, img2_path):
    try:
        img1 = cv2.imread(img1_path)
        img2 = cv2.imread(img2_path)
        
        if img1 is None or img2 is None:
            return 0.0
            
        hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
        hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)
        
        hist1 = cv2.calcHist([hsv1], [0, 1], None, [180, 256], [0, 180, 0, 256])
        hist2 = cv2.calcHist([hsv2], [0, 1], None, [180, 256], [0, 180, 0, 256])
        
        cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)
        
        score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return max(0.0, min(float(score), 1.0))
        
    except Exception as e:
        print(f"Color Error: {e}")
        return 0.0

# ---------- STRUCTURAL SIMILARITY (ORB) ----------
def image_similarity(img1_path, img2_path):
    try:
        img1 = cv2.imread(img1_path, 0)
        img2 = cv2.imread(img2_path, 0)

        if img1 is None or img2 is None:
            return 0.0

        orb = cv2.ORB_create(nfeatures=5000)

        kp1, des1 = orb.detectAndCompute(img1, None)
        kp2, des2 = orb.detectAndCompute(img2, None)

        if des1 is None or des2 is None:
            return 0.0

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)

        if len(matches) == 0:
            return 0.0
            
        good_matches = [m for m in matches if m.distance < 50]
        match_count = len(good_matches)
        
        # Sigmoid-like scaling
        score = min(match_count / 30.0, 1.0)

        return round(score, 2)

    except Exception as e:
        print(f"ORB Error: {e}")
        return 0.0

# ---------- FINAL MATCH ----------
def final_match(lost, found):
    text_score = text_similarity(
        lost["description"],
        found["description"]
    )

    orb_score = image_similarity(
        lost["image_path"],
        found["image_path"]
    )
    
    color_score = color_similarity(
        lost["image_path"],
        found["image_path"]
    )

    # Weighted Average
    final_score = (text_score * 0.3) + (orb_score * 0.4) + (color_score * 0.3)

    return {
        "text_score": round(text_score * 100, 0),
        "image_score": round(orb_score * 100, 0),
        "color_score": round(color_score * 100, 0),
        "final_score": round(final_score, 2)
    }
