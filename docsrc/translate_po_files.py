# -*- coding: utf-8 -*-
"""
PO file translator script.
Uses polib and deep-translator (GoogleTranslator) to translate
untranslated msgids from Japanese to English.
Supports custom translator import from my_translator.py.
"""
from __future__ import absolute_import, print_function, unicode_literals
import os
import time
import sys
import polib

# Try to import a custom get_translator function from a local non-git module
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from my_translator import get_translator
    has_custom_translator = True
    print("Using custom translator factory from my_translator.py (High performance, no delays).")
except (ImportError, ModuleNotFoundError):
    from deep_translator import GoogleTranslator
    
    def get_translator(source='ja', target='en'):
        return GoogleTranslator(source=source, target=target)
        
    has_custom_translator = False
    print("Custom translator not found (my_translator.py). Falling back to Free Google Translator (with bot protection).")


def translate_text(translator_obj, text, is_custom=False):
    if not text or not text.strip():
        return ""
    
    # If the text is purely code, numbers, or symbols, don't translate it
    if text.strip().startswith(':ref:') or text.strip().startswith('.. toctree::'):
        return text
    
    # Use custom translator at high speed
    if is_custom:
        try:
            if hasattr(translator_obj, 'translate'):
                translated = translator_obj.translate(text)
            elif callable(translator_obj):
                translated = translator_obj(text)
            else:
                raise ValueError("Imported 'translator' is neither callable nor has a 'translate' method.")
            
            if translated:
                return translated
            return text
        except Exception as e:
            print("Error translating text with custom translator: {}".format(e), flush=True)
            return text

    # Fallback to free Google Translator with safety retries and delays
    for attempt in range(3):
        try:
            translated = translator_obj.translate(text)
            if translated:
                return translated
            return text
        except Exception as e:
            print("Error translating text with free translator (attempt {}): {}".format(attempt + 1, e), flush=True)
            time.sleep(1.0)
    return text


def translate_po_file(translator_obj, po_file_path, is_custom=False):
    # Show clean relative path from LC_MESSAGES for readability
    rel_path = os.path.relpath(po_file_path, os.path.join('docsrc', 'locale', 'en', 'LC_MESSAGES'))
    print("Processing: {}".format(rel_path), flush=True)
    try:
        po = polib.pofile(po_file_path)
    except Exception as e:
        print("Failed to load {}: {}".format(po_file_path, e), flush=True)
        return

    modified = False
    count = 0
    total_untranslated = sum(1 for entry in po if not entry.msgstr and not entry.obsolete)
    
    if total_untranslated == 0:
        print("  All entries already translated.", flush=True)
        return

    print("  Found {} untranslated entries.".format(total_untranslated), flush=True)

    for entry in po:
        if entry.obsolete:
            continue
        
        # If msgstr is empty, we need to translate
        if not entry.msgstr:
            original = entry.msgid
            if original:
                count += 1
                print("  [{}/{}] Translating: {}".format(count, total_untranslated, original.replace('\n', ' ')[:50]), flush=True)
                
                # Perform translation
                translated = translate_text(translator_obj, original, is_custom=is_custom)
                entry.msgstr = translated
                modified = True
                
                # Be gentle to the API to avoid rate limiting ONLY for the free translator
                if not is_custom:
                    time.sleep(0.2)

    if modified:
        try:
            po.save()
            print("  Successfully translated and saved {} entries.".format(count), flush=True)
        except Exception as e:
            print("  Failed to save {}: {}".format(po_file_path, e), flush=True)


def main():
    locale_messages_dir = os.path.join('docsrc', 'locale', 'en', 'LC_MESSAGES')
    if not os.path.exists(locale_messages_dir):
        print("Error: Locale directory not found at: {}".format(locale_messages_dir), flush=True)
        sys.exit(1)

    print("Initializing translator (ja -> en)...", flush=True)
    translator = get_translator(source='ja', target='en')

    # Find all .po files under LC_MESSAGES recursively
    po_files = []
    for root, dirs, files in os.walk(locale_messages_dir):
        for file in files:
            if file.endswith('.po'):
                po_files.append(os.path.join(root, file))

    print("Found {} .po files to process.".format(len(po_files)), flush=True)
    
    for idx, po_file in enumerate(po_files):
        print("\n[{}/{}] ".format(idx + 1, len(po_files)), end="", flush=True)
        translate_po_file(translator, po_file, is_custom=has_custom_translator)

    print("\nTranslation process finished!", flush=True)


if __name__ == '__main__':
    main()

