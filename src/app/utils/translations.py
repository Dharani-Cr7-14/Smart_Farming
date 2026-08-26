# Multilingual Translation Dictionary (EN / TA / HI)

LANG_DICT = {
    "en": {
        "home_title": "Smart Farming",
        "home_subtitle": "Smart Farming Decision Support System",
        "seed": "Seed Recommendation",
        "disease": "Disease Prediction",
        "select_soil": "--Select Soil Type--",
        "select_region": "--Select Region--",
        "soil_options": ["Loamy","Sandy","Clay","Red","Black"],
        "region_options": ["North","South","East","West","Central"],
        "charts_seed": [
            "Feature Importance",
            "Seed Variety Distribution",
            "Crop vs Seed Relationship",
            "Soil Type vs Seed Variety",
            "Expected Yield vs Seed Variety",
            "Soil Nutrient Radar",
            "Feature Correlation Heatmap"
        ],
        "charts_disease": [
            "Overall Leaf Health",
            "Disease Type Distribution",
            "Model Accuracy Gauge",
            "Top Predicted Diseases",
            "Seasonal Disease Trend"
        ]
    },
    "ta": {
        "home_title": "ஸ்மார்ட் விவசாயம்",
        "home_subtitle": "ஸ்மார்ட் விவசாய முடிவு ஆதரவு அமைப்பு",
        "seed": "விதை பரிந்துரை",
        "disease": "நோய் கணிப்பு",
        "select_soil": "--மண் வகை தேர்ந்தெடுக்கவும்--",
        "select_region": "--மண்டலத்தை தேர்ந்தெடுக்கவும்--",
        "soil_options": ["மணல்மண்","மணல்","களி","சிவப்பு","கருப்பு"],
        "region_options": ["வடக்கு","தெற்கு","கிழக்கு","மேற்கு","மத்திய"],
        "charts_seed": [
            "முக்கிய அம்சங்கள்",
            "விதை வகை பகிர்வு",
            "பயிர் vs விதை உறவு",
            "மண் வகை vs விதை",
            "எதிர்பார்க்கப்படும் பயிர் உற்பத்தி",
            "மண் ஊட்டச்சத்து ரேடார்",
            "அம்சங்களின் தொடர்பு ஹீட்மேப்"
        ],
        "charts_disease": [
            "இலையின் மொத்த ஆரோக்கியம்",
            "நோய் வகை பகிர்வு",
            "மாதிரி துல்லியக் குறியீடு",
            "முக்கிய கணிக்கப்பட்ட நோய்கள்",
            "பாலிடிக்க சீர்திருத்த பருவத் போக்கு"
        ]
    },
    "hi": {
        "home_title": "स्मार्ट फार्मिंग",
        "home_subtitle": "स्मार्ट कृषि निर्णय सहायता प्रणाली",
        "seed": "बीज सिफ़ारिश",
        "disease": "रोग भविष्यवाणी",
        "select_soil": "--मिट्टी का प्रकार चुनें--",
        "select_region": "--क्षेत्र चुनें--",
        "soil_options": ["दोमट", "रेतीली", "मृदा", "लाल", "काली"],
        "region_options": ["उत्तर", "दक्षिण", "पूर्व", "पश्चिम", "केंद्र"],
        "charts_seed": [
            "विशेषता महत्व",
            "बीज विविधता वितरण",
            "फसल vs बीज संबंध",
            "मिट्टी प्रकार vs बीज विविधता",
            "अपेक्षित उपज vs बीज विविधता",
            "मिट्टी पोषक तत्व राडार",
            "विशेषता सहसंबंध हीटमैप"
        ],
        "charts_disease": [
            "संपूर्ण पत्ते का स्वास्थ्य",
            "रोग प्रकार वितरण",
            "मॉडल सटीकता संकेतक",
            "शीर्ष भविष्यवाणी रोग",
            "मौसमी रोग प्रवृत्ति"
        ]
    }
}

def get_lang_dict(lang: str):
    """Retrieve UI translation mapping based on requested ISO code."""
    return LANG_DICT.get(lang, LANG_DICT["en"])
