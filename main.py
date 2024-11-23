from flask import Flask, render_template, request, send_file
import spacy
import re

app = Flask(__name__)

nlp_uk = spacy.load("uk_core_news_sm")
nlp_en = spacy.load("en_core_web_sm")


def detect_language(text):
    if re.search(r'[а-яА-ЯіїєґІЇЄҐ]', text):  # Кирилиця
        return 'uk'
    elif re.search(r'[a-zA-Z]', text):  # Латиниця
        return 'en'
    return None


def extract_features(text, lang):
    nlp = nlp_uk if lang == 'uk' else nlp_en
    doc = nlp(text)
    feature_type = "ADP"  

    features = []
    highlighted_text = ""

    for token in doc:
        if token.pos_ == feature_type and token.is_alpha:
            features.append(token.text)
            highlighted_text += f'<span style="color: red; font-weight: bold;">{token.text}</span> '
        else:
            highlighted_text += f"{token.text} "

    return features, highlighted_text.strip()


@app.route("/", methods=["GET", "POST"])
def index():
    features = []
    highlighted_text = ""
    input_text = ""
    lang = None
    error_message = ""

    if request.method == "POST":
        if "text" in request.form and request.form["text"].strip():
            input_text = request.form["text"]
        elif "file" in request.files and request.files["file"].filename:
            file = request.files["file"]
            try:
                input_text = file.read().decode("utf-8")
            except UnicodeDecodeError:
                error_message = "Неможливо прочитати файл. Використовуйте текстовий файл у форматі '.txt'."
                return render_template("index.html", error_message=error_message)

        if input_text:
            lang = detect_language(input_text)
            if lang:
                features, highlighted_text = extract_features(input_text, lang)
            else:
                error_message = "Неможливо визначити мову тексту. Введіть текст українською або англійською мовою."

    return render_template(
        "index.html",
        features=features,
        input_text=highlighted_text,
        original_text=input_text,
        lang=lang,
        error_message=error_message
    )


@app.route("/generate-report", methods=["POST"])
def generate_report():
    text = request.form["original_text"]
    features = request.form.getlist("features")
    lang = request.form["lang"]

    # Вибір типу характеристик для звіту
    feature_label = "Прийменники" 

    # Генерація звіту
    word_count = len(text.split())
    text_length = len(text)
    report_content = (
        f"Оригінальний текст:\n{text}\n\n"
        f"Статистика:\n"
        f"- Довжина тексту: {text_length} символів\n"
        f"- Кількість слів: {word_count}\n"
        f"- {feature_label}:\n"
        f"{chr(10).join(feature.lower() for feature in features) if features else 'Не знайдено'}\n"
    )

    report_path = "report.txt"
    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write(report_content)

    return send_file(report_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)

