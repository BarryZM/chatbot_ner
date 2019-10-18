# -*- coding: utf-8 -*-
from ner_v2.detectors.base_detector import BaseDetector
from ner_v2.detectors.numeral.number.number_detection import NumberDetector
from language_utilities.constant import ENGLISH_LANG
import re
import phonenumbers


class PhoneDetector(BaseDetector):
    """
    This method is used to detect phone numbers present in text. The phone detector takes into
    consideration domestic as well as international phone numbers.

    Attributes:
         text(str): string provided to extract phone numbers detection
         phone (list): list of detected entity values
         original_phone_text (list): list to store substrings of the text detected as phone numbers
    """

    def __init__(self, entity_name, language=ENGLISH_LANG, locale=None):
        """
        Args:
            entity_name (str): A string by which the detected numbers would be replaced with
            on calling detect_entity()
            language (str, optional): language code of number text, defaults to 'en'
            locale(str, optional): locale of the country from which you are dialing. Ex: 'en-IN'
        """
        self._supported_languages = NumberDetector.get_supported_languages()
        super(PhoneDetector, self).__init__(language, locale)
        self.language = language
        self.locale = locale or 'en-IN'
        self.text = ''
        self.phone, self.original_phone_text = [], []
        self.country_code = self.get_country_code_from_locale()

    @property
    def supported_languages(self):
        """
        This method returns the list of languages supported by entity detectors
        Return:
             list: List of ISO 639 codes of languages supported by subclass/detector
        """
        return self._supported_languages

    def get_country_code_from_locale(self):
        """
        This method sets self.country_code from given locale
        """
        regex_pattern = re.compile('[-_](.*$)', re.U)
        match = regex_pattern.findall(self.locale)
        if match:
            return match[0].upper()
        else:
            return 'IN'

    def detect_entity(self, text, **kwargs):
        """Detects phone numbers in the text string

        Args:
            text: string to extract entities from
            **kwargs: it can be used to send specific arguments in future.

        Returns:

            self.phone (list): list consisting the detected phone numbers and their country calling codes
            self.original_phone_text (list): list containing their corresponding substrings in the original message.

        Examples:

        text = 'call +1 (408) 912-6172'
        p = PhoneDetector(entity_name='phone_number', language='en', locale='en-US')
        p.detect_entity(text=text)
        ([{'country_calling_code':'1', phone_number':'4089126172'} ],
         [u'+1 (408) 912-6172'])

        text = '+९१ ९८१९९८३१३२ पर कॉल करें और संदेश ९८२०३३४४१६ पर कॉल करें'
        p = PhoneDetector(entity_name='phone_number', language='hi', locale='en-IN')
        p.detect_entity(text=text)
        ([{'country_calling_code':'91', phone_number':'9819983132'}
        ,{ 'country_calling_code':'91', phone_number:'9820334416'} ],
        [u'+९१ ९८१९९८३१३२', u'+९१ ९८१९९८३१३२'])

        """
        self.text = text
        self.phone, self.original_phone_text = [], []
        for match in phonenumbers.PhoneNumberMatcher(self.text, self.country_code, leniency=0):
            if match.number.country_code == phonenumbers.country_code_for_region(self.country_code):
                self.phone.append(self.check_for_country_code(str(match.number.national_number)))
                self.original_phone_text.append(self.text[match.start:match.end])
            else:
                # This means our detector has detected some other country code.
                self.phone.append({"country_calling_code": str(match.number.country_code),
                                   "phone_number": str(match.number.national_number)})
                self.original_phone_text.append(self.text[match.start:match.end])

        self.check_for_alphas()
        return self.phone, self.original_phone_text

    def check_for_alphas(self):
        """
        checks if any leading or trailing alphabets in the detected phone numbers and removes those numbers
        """

        for phone, original in zip(self.phone, self.original_phone_text):
            if re.search(r'([a-zA-Z0-9]{original}|{original}[a-zA-Z0-9])'.format(original=original)):
                self.phone.remove(phone)
                self.original_phone_text.remove(original)

    def check_for_country_code(self, phone_num):
        """
        :param phone_num: the number which is to be checked for country code
        :return: dict with country_code if it's in phone_num or phone_number with current country code
        Examples:
            phone_num = '919123456789'
            countryCallingCode = 'IN'
            {countryCallingCode:"91",phone_number:"9123456789"}
        """
        phone_dict = {}

        if len(phone_num) > 10:
            check_country_regex = re.compile(r'^({country_code})\d{length}$'.
                                             format(country_code='911|1|011 91|91', length='{10}'), re.U)
            p = check_country_regex.findall(phone_num)
            if len(p) == 1:
                phone_dict['country_calling_code'] = p[0]
                country_code_sub_regex = re.compile(r'^{detected_code}'.format(detected_code=p[0]))
                phone_dict['phone_number'] = country_code_sub_regex.sub(string=phone_num, repl='')
            else:
                phone_dict['country_calling_code'] = str(phonenumbers.country_code_for_region(self.country_code))
                phone_dict['phone_number'] = phone_num
        else:
            phone_dict['country_calling_code'] = str(phonenumbers.country_code_for_region(self.country_code))
            phone_dict['phone_number'] = phone_num

        return phone_dict
