import json
import os
import random


class TranslationManager:
    def __init__(self, locale_dir: str, default_lang="en-US"):
        self.locale_dir = locale_dir
        self.default_lang = default_lang
        self.language = default_lang
        self.__loaded_languages = {}
        self.__file_mtimes = {}
        self.__load_language(self.default_lang)

    def __merge_dicts(self, a, b):
        for key, value in b.items():
            if key in a and isinstance(a[key], dict) and isinstance(value, dict):
                self.__merge_dicts(a[key], value)
            else:
                a[key] = value

    def __load_language(self, lang, force_reload=False):
        # Check if we already cached and files are unchanged
        if not force_reload and lang in self.__loaded_languages:
            if not self.__files_changed(lang):
                return self.__loaded_languages[lang]

        lang_path = os.path.join(self.locale_dir, lang)
        if not os.path.isdir(lang_path):
            return {}

        merged = {}
        file_mtimes = {}
        for file in os.listdir(lang_path):
            if file.endswith(".json"):
                full_path = os.path.join(lang_path, file)
                file_mtimes[full_path] = os.path.getmtime(full_path)
                with open(full_path, "r", encoding="utf-8") as f:
                    section = json.load(f)
                    self.__merge_dicts(merged, section)

        self.__loaded_languages[lang] = merged
        self.__file_mtimes[lang] = file_mtimes
        return merged

    def __files_changed(self, lang):
        """Check if any file in a cached language was modified since last load"""
        if lang not in self.__file_mtimes:
            return True
        for path, old_mtime in self.__file_mtimes[lang].items():
            try:
                if os.path.getmtime(path) != old_mtime:
                    return True
            except FileNotFoundError:
                return True
        return False

    def set_language(self, lang):
        self.__load_language(lang)
        self.language = lang

    @staticmethod
    def __get_nested(dictionary, key_path):
        keys = key_path.split(".")

        for key in keys:
            if isinstance(dictionary, dict):
                dictionary = dictionary.get(key)
            else:
                return None

        return dictionary

    @staticmethod
    def __get_random(value: dict, **kwargs):
        """
        If value is a dict with numeric string keys "1", "2", ..., "n" with no skips,
        pick a random one, format it if it's a string, and return it.
        """
        numbered_keys = [k for k in value.keys() if k.isdigit()]
        if numbered_keys:
            nums = sorted(int(k) for k in numbered_keys)
            # Check if sequential starting at 1
            if nums == list(range(1, len(nums) + 1)):
                choice_key = str(random.choice(nums))
                chosen_value = value[choice_key]
                if isinstance(chosen_value, str):
                    return chosen_value.format(**kwargs)
                return chosen_value
        return None

    def translate_random(self, key, lang: str = None, **kwargs):
        lang_dict = self.__load_language(self.language if lang is None else lang)
        fallback_dict = self.__load_language(self.default_lang)

        # Try in current language
        result = self.__get_nested(lang_dict, key)
        if result is None:
            result = self.__get_nested(fallback_dict, key)

        if result is None:
            return f"[{key}]"

        if not isinstance(result, dict):
            return f"[{key}]"

        # Random selection + formatting
        result = self.__get_random(result, **kwargs)

        if result is None:
            return f"[{key}]"

        # If it's still a string, format normally
        if isinstance(result, str):
            return result.format(**kwargs)

        return str(result)  # fallback if not a string

    def translate(self, key, lang: str = None, count=None, **kwargs):
        lang_dict = self.__load_language(self.language if lang is None else lang)
        fallback_dict = self.__load_language(self.default_lang)

        plural_key = key + "|plural" if count is not None and abs(count) != 1 else key

        # Try in current language
        result = self.__get_nested(lang_dict, plural_key)

        if result is None:
            result = self.__get_nested(fallback_dict, plural_key)

        if result is None:
            return f"[{key}]"

        if count is not None:
            kwargs["count"] = count

        return result.format(**kwargs)
