from django.shortcuts import render
from django.shortcuts import render
import qrcode
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from io import BytesIO
from django.contrib.sites.models import Site
import urllib.parse

# Create your views here.
from django.http import HttpResponse


def create_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")

    byte_arr = BytesIO()
    img.save(byte_arr)
    byte_arr.seek(0)

    return byte_arr


def hello_world(request):
    translated_string = None
    qr_code = None

    credentials = service_account.Credentials.from_service_account_file(
        "qr_codes/cloud_key/key.json"
    )
    translate_client = translate.Client(credentials=credentials)
    languages = translate_client.get_languages()
    print(f"Languages: {languages}")

    if request.method == "POST":
        input_string = request.POST.get("textToTranslate")
        if isinstance(input_string, bytes):
            input_string = input_string.decode("utf-8")
            print("input_string is bytes")

        target_language = request.POST.get("targetLanguage")

        translated_string = translate_client.translate(
            input_string, target_language=target_language
        )
        print(f"Translated string: {translated_string}")

        current_site = Site.objects.get_current()
        print(f"Current site: {current_site}")
        domain = current_site.domain

        string_to_qr_code = f"http://{domain}/read?text={urllib.parse.quote_plus(translated_string['translatedText'])}&lang={target_language}&source={translated_string['detectedSourceLanguage']}"

        print(string_to_qr_code)
        qr_code = create_qr_code(string_to_qr_code)
        print("QR Code saved as qr_code.png")

        qr_code_file_name = "qr_code.png"
        with open(qr_code_file_name, "wb") as f_out:
            f_out.write(qr_code.getbuffer())

        response = HttpResponse(qr_code, content_type="image/png")
        response["Content-Disposition"] = "attachment; filename=qr_code.png"
        return response

    return render(
        request,
        "qr_codes/home.html",
        {
            "languages": languages,
            "error": "",
            "translated_string": translated_string,
            "qr_code": qr_code,
        },
    )


def get_language_name_from_code(code):
    credentials = service_account.Credentials.from_service_account_file(
        "qr_codes/cloud_key/key.json"
    )
    translate_client = translate.Client(credentials=credentials)

    languages = translate_client.get_languages()
    for language in languages:
        if language["language"] == code:
            return language["name"]
    return None  # if the code is not found in the list


def read_qr_code_contents(request):
    print(request.GET)

    text = request.GET.get("text")
    target_language = request.GET.get("lang")
    source_language = request.GET.get("source")

    # convert language codes to names
    target_language_name = get_language_name_from_code(target_language)
    source_language_name = get_language_name_from_code(source_language)

    return render(
        request,
        "qr_codes/read_qr_code.html",
        {
            "text": text,
            "target_language": target_language_name,
            "source_language": source_language_name,
        },
    )
