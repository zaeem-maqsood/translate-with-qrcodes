import os
import json
import urllib.parse
from io import BytesIO

import qrcode
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.sites.models import Site
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from .models import Translation

from django.utils import timezone
from datetime import timedelta

# Global cache for the client and languages
_TRANSLATE_CLIENT = None
_LANGUAGES_CACHE = None

def get_translate_client():
    """
    Returns a cached Google Translate client.
    Initializes from GOOGLE_CREDENTIALS_JSON env var if available,
    otherwise falls back to the local file (for dev compatibility).
    """
    global _TRANSLATE_CLIENT
    if _TRANSLATE_CLIENT:
        return _TRANSLATE_CLIENT

    # Try getting credentials from environment variable (Best for Docker/Production)
    credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    
    if credentials_json:
        try:
            # Parse the JSON string from the environment variable
            info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(info)
            _TRANSLATE_CLIENT = translate.Client(credentials=credentials)
        except json.JSONDecodeError as e:
            print(f"Error decoding GOOGLE_CREDENTIALS_JSON: {e}")
            # Fallback or raise error depending on preference
    
    # Fallback to local file (Old method, good for local dev if file exists)
    if not _TRANSLATE_CLIENT:
        key_path = "qr_codes/cloud_key/key.json"
        if os.path.exists(key_path):
             credentials = service_account.Credentials.from_service_account_file(key_path)
             _TRANSLATE_CLIENT = translate.Client(credentials=credentials)
        else:
            # For debugging purposes, letting us know it failed
            print("Warning: Google Cloud credentials not found in env or local file.")
            return None

    return _TRANSLATE_CLIENT

def get_cached_languages():
    """
    Returns a list of supported languages, cached to avoid repeated API calls.
    """
    global _LANGUAGES_CACHE
    if _LANGUAGES_CACHE:
        return _LANGUAGES_CACHE
    
    client = get_translate_client()
    if client:
        _LANGUAGES_CACHE = client.get_languages()
        return _LANGUAGES_CACHE
    return []

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
    
    # Use cached languages
    languages = get_cached_languages()

    if request.method == "POST":
        client = get_translate_client()
        if not client:
             return render(request, "qr_codes/home.html", {
                 "languages": languages,
                 "error": "Service configuration error: Credentials missing.",
             })

        input_string = request.POST.get("textToTranslate")
        if isinstance(input_string, bytes):
            input_string = input_string.decode("utf-8")

        target_language = request.POST.get("targetLanguage")

        try:
            translated_string = client.translate(
                input_string, target_language=target_language
            )
            print(f"Translated string: {translated_string}")

            domain = request.get_host()
            scheme = request.scheme

            # Save translation to database
            translation = Translation.objects.create(
                source_text=input_string,
                translated_text=translated_string.get('translatedText', ''),
                source_language=translated_string.get('detectedSourceLanguage', 'en'),
                target_language=target_language
            )
            
            # Use the new UUID-based URL
            # Note: Using manual string construction as requested, but proper reversing is better usually.
            string_to_qr_code = f"{scheme}://{domain}/read/{translation.id}/"

            qr_code = create_qr_code(string_to_qr_code)
            
            # Return image directly without saving to disk
            response = HttpResponse(qr_code, content_type="image/png")
            response["Content-Disposition"] = "attachment; filename=qr_code.png"
            return response

        except Exception as e:
            print(f"Translation or QR generation error: {e}")
            return render(request, "qr_codes/home.html", {
                "languages": languages,
                "error": f"Error: {str(e)}",
            })

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
    # Use cached languages list
    languages = get_cached_languages()
    for language in languages:
        if language["language"] == code:
            return language["name"]
    return None


def read_qr_code_contents(request, pk):
    translation = get_object_or_404(Translation, pk=pk)

    # Check for expiration (e.g., 24 hours)
    if timezone.now() - translation.created_at > timedelta(hours=24):
        translation.delete()
        return render(request, "qr_codes/home.html", {"error": "This QR code has expired."})
    
    text = translation.translated_text
    target_language = translation.target_language
    source_language = translation.source_language

    # convert language codes to names
    target_language_name = get_language_name_from_code(target_language)
    source_language_name = get_language_name_from_code(source_language)

    return render(
        request,
        "qr_codes/read_qr_code.html",
        {
            "text": text,
            "target_language": target_language_name or target_language,
            "source_language": source_language_name or source_language,
        },
    )
