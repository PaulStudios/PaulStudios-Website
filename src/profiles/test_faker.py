import io
import logging
import os
import random
import string
import unittest
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from functools import partial
from pathlib import Path
from typing import (
    Any,
    List,
    Optional,
    Set,
    Union,
)

from .fake import *


class TestFaker(unittest.TestCase):
    def setUp(self) -> None:
        self.faker = FAKER

    def tearDown(self):
        FILE_REGISTRY.clean_up()

    def test_uuid(self) -> None:
        uuid_value = self.faker.uuid()
        self.assertIsInstance(uuid_value, uuid.UUID)

    def test_uuids(self) -> None:
        uuids = self.faker.uuids()
        for uuid_value in uuids:
            self.assertIsInstance(uuid_value, uuid.UUID)

    def test_first_name(self) -> None:
        first_name: str = self.faker.first_name()
        self.assertIsInstance(first_name, str)
        self.assertTrue(len(first_name) > 0)
        self.assertIn(first_name, self.faker._first_names)

    def test_first_names(self) -> None:
        first_names: List[str] = self.faker.first_names()
        for first_name in first_names:
            self.assertIsInstance(first_name, str)
            self.assertTrue(len(first_name) > 0)
            self.assertIn(first_name, self.faker._first_names)

    def test_last_name(self) -> None:
        last_name: str = self.faker.last_name()
        self.assertIsInstance(last_name, str)
        self.assertTrue(len(last_name) > 0)
        self.assertIn(last_name, self.faker._last_names)

    def test_last_names(self) -> None:
        last_names: List[str] = self.faker.last_names()
        for last_name in last_names:
            self.assertIsInstance(last_name, str)
            self.assertTrue(len(last_name) > 0)
            self.assertIn(last_name, self.faker._last_names)

    def test_name(self) -> None:
        name: str = self.faker.name()
        self.assertIsInstance(name, str)
        self.assertTrue(len(name) > 0)
        parts = name.split(" ")
        first_name = parts[0]
        last_name = " ".join(parts[1:])
        self.assertIn(first_name, self.faker._first_names)
        self.assertIn(last_name, self.faker._last_names)

    def test_names(self) -> None:
        names: List[str] = self.faker.names()
        for name in names:
            self.assertIsInstance(name, str)
            self.assertTrue(len(name) > 0)
            parts = name.split(" ")
            first_name = parts[0]
            last_name = " ".join(parts[1:])
            self.assertIn(first_name, self.faker._first_names)
            self.assertIn(last_name, self.faker._last_names)

    def test_username(self) -> None:
        username: str = self.faker.username()
        self.assertIsInstance(username, str)

    def test_usernames(self) -> None:
        usernames: List[str] = self.faker.usernames()
        for username in usernames:
            self.assertIsInstance(username, str)

    def test_slug(self) -> None:
        slug: str = self.faker.slug()
        self.assertIsInstance(slug, str)

    def test_slugs(self) -> None:
        slugs: List[str] = self.faker.slugs()
        for slug in slugs:
            self.assertIsInstance(slug, str)

    def test_word(self) -> None:
        word: str = self.faker.word()
        self.assertIsInstance(word, str)
        self.assertTrue(len(word) > 0)

    def test_words(self) -> None:
        words: List[str] = self.faker.words(nb=3)
        self.assertIsInstance(words, list)
        self.assertEqual(len(words), 3)

    def test_sentence(self) -> None:
        sentence: str = self.faker.sentence()
        self.assertIsInstance(sentence, str)
        self.assertTrue(len(sentence.split()) >= 5)
        self.assertTrue(sentence.endswith("."))

    def test_sentences(self) -> None:
        sentences: List[str] = self.faker.sentences(nb=3)
        self.assertIsInstance(sentences, list)
        self.assertEqual(len(sentences), 3)

    def test_paragraph(self) -> None:
        paragraph: str = self.faker.paragraph()
        self.assertIsInstance(paragraph, str)
        self.assertTrue(len(paragraph.split(".")) >= 5)

    def test_paragraphs(self) -> None:
        paragraphs: List[str] = self.faker.paragraphs(nb=3)
        self.assertIsInstance(paragraphs, list)
        self.assertEqual(len(paragraphs), 3)

    def test_text(self) -> None:
        text: str = self.faker.text(nb_chars=100)
        self.assertIsInstance(text, str)
        self.assertTrue(len(text) <= 100)

    def test_texts(self) -> None:
        texts: List[str] = self.faker.texts(nb=3)
        self.assertIsInstance(texts, list)
        self.assertEqual(len(texts), 3)

    def test_file_name(self) -> None:
        extensions = [(None, "txt"), ("txt", "txt"), ("jpg", "jpg")]
        for extension, expected_extension in extensions:
            with self.subTest(
                extension=extension, expected_extension=expected_extension
            ):
                kwargs = {}
                if extension is not None:
                    kwargs["extension"] = extension
                file_name: str = self.faker.file_name(**kwargs)
                self.assertIsInstance(file_name, str)
                self.assertTrue(file_name.endswith(f".{expected_extension}"))

    def test_email(self) -> None:
        domains = [
            (None, "example.com"),
            ("example.com", "example.com"),
            ("gmail.com", "gmail.com"),
        ]
        for domain, expected_domain in domains:
            with self.subTest(domain=domain, expected_domain=expected_domain):
                kwargs = {"domain": domain}
                email: str = self.faker.email(**kwargs)
                self.assertIsInstance(email, str)
                self.assertTrue(email.endswith(f"@{expected_domain}"))

    def test_url(self) -> None:
        protocols = ("http", "https")
        tlds = ("com", "org", "net", "io")
        suffixes = (".html", ".php", ".go", "", "/")
        for protocol in protocols:
            for tld in tlds:
                for suffix in suffixes:
                    with self.subTest(
                        protocol=protocol, tld=tld, suffix=suffix
                    ):
                        url: str = self.faker.url(
                            protocols=(protocol,),
                            tlds=(tld,),
                            suffixes=(suffix,),
                        )
                        self.assertIsInstance(url, str)
                        self.assertTrue(url.startswith(f"{protocol}://"))
                        self.assertTrue(f".{tld}/" in url)
                        self.assertTrue(
                            url.endswith(suffix) or url.endswith(f"{suffix}/")
                        )

    def test_image_url(self) -> None:
        params = (
            (None, None, None, {"width": 800, "height": 600}),
            (640, 480, None, {"width": 640, "height": 480}),
            (
                None,
                None,
                "https://example.com/{width}x{height}",
                {"width": 800, "height": 600},
            ),
        )
        for width, height, service_url, expected in params:
            kwargs = {}
            if width:
                kwargs["width"] = width
            if height:
                kwargs["height"] = height
            if service_url:
                kwargs["service_url"] = service_url
            image_url = self.faker.image_url(**kwargs)
            self.assertIn(str(expected["width"]), image_url)
            self.assertIn(str(expected["height"]), image_url)
            self.assertTrue(image_url.startswith("https://"))

    def test_pyint(self) -> None:
        ranges = [
            (None, None, 0, 9999),
            (0, 5, 0, 5),
            (-5, 0, -5, 0),
        ]
        for min_val, max_val, expected_min_val, expected_max_val in ranges:
            with self.subTest(
                min_value=min_val,
                max_value=max_val,
                expected_min_value=expected_min_val,
                expected_max_value=expected_max_val,
            ):
                kwargs = {}
                if min_val is not None:
                    kwargs["min_value"] = min_val
                if max_val is not None:
                    kwargs["max_value"] = max_val
                val: int = self.faker.pyint(**kwargs)
                self.assertIsInstance(val, int)
                self.assertGreaterEqual(val, expected_min_val)
                self.assertLessEqual(val, expected_max_val)

    def test_pybool(self) -> None:
        value: bool = self.faker.pybool()
        self.assertIsInstance(value, bool)

    def test_pystr(self) -> None:
        ranges = [
            (None, 20),
            (0, 0),
            (1, 1),
            (5, 5),
            (10, 10),
            (100, 100),
        ]
        valid_characters = set(string.ascii_letters)  # ASCII letters

        for nb_chars, expected_nb_chars in ranges:
            with self.subTest(
                nb_chars=nb_chars,
                expected_nb_chars=expected_nb_chars,
            ):
                kwargs = {}
                if nb_chars is not None:
                    kwargs["nb_chars"] = nb_chars
                val: str = self.faker.pystr(**kwargs)

                # Check if the output is a string
                self.assertIsInstance(val, str)

                # Check if the string has the correct length
                self.assertEqual(len(val), expected_nb_chars)

                # Check if all characters are from the valid set
                self.assertTrue(all(c in valid_characters for c in val))

    def test_pyfloat(self) -> None:
        ranges = [
            (None, None, 0.0, 10.0),
            (0.0, 5.0, 0.0, 5.0),
            (-5.0, 0.0, -5.0, 0.0),
        ]
        for min_val, max_val, expected_min_val, expected_max_val in ranges:
            with self.subTest(
                min_value=min_val,
                max_value=max_val,
                expected_min_value=expected_min_val,
                expected_max_value=expected_max_val,
            ):
                kwargs = {}
                if min_val is not None:
                    kwargs["min_value"] = min_val
                if max_val is not None:
                    kwargs["max_value"] = max_val
                val: float = self.faker.pyfloat(**kwargs)
                self.assertIsInstance(val, float)
                self.assertGreaterEqual(val, expected_min_val)
                self.assertLessEqual(val, expected_max_val)

    def test_pydecimal(self):
        with self.subTest("With positive=True"):
            for __ in range(100):
                decimal_number = self.faker.pydecimal(
                    left_digits=3,
                    right_digits=2,
                    positive=True,
                )
                self.assertIsInstance(decimal_number, Decimal)
                self.assertTrue(1 <= decimal_number < 1000)
                # Check if right digits are 2
                self.assertTrue(decimal_number.as_tuple().exponent == -2)

        with self.subTest("With positive=False"):
            for __ in range(100):
                negative_decimal_number = self.faker.pydecimal(
                    left_digits=2,
                    right_digits=2,
                    positive=False,
                )
                self.assertTrue(-100 <= negative_decimal_number <= 100)

        with self.subTest("With right_digits=0"):
            for __ in range(100):
                decimal_number = self.faker.pydecimal(
                    left_digits=2,
                    right_digits=0,
                    positive=True,
                )
                self.assertIsInstance(decimal_number, Decimal)
                # Check if there is no fractional part
                self.assertEqual(decimal_number % 1, 0)
                # Check if it's a 3-digit number
                self.assertTrue(10 <= decimal_number < 100)

        with self.subTest("With left_digits=0"):
            for __ in range(100):
                decimal_number = self.faker.pydecimal(
                    left_digits=0, right_digits=2, positive=True
                )
                self.assertIsInstance(decimal_number, Decimal)
                self.assertTrue(0 <= decimal_number < 1)
                self.assertTrue(
                    10 <= decimal_number * 100 < 100
                )  # Check that the fractional part is correct

                # Test for zero left digits with negative numbers
                decimal_number_neg = self.faker.pydecimal(
                    left_digits=0, right_digits=2, positive=False
                )
                self.assertTrue(-1 < decimal_number_neg <= 0)

        with self.subTest("Fail on `left_digits` < 0"):
            with self.assertRaises(ValueError):
                self.faker.pydecimal(left_digits=-1)

        with self.subTest("Fail on `right_digits` < 0"):
            with self.assertRaises(ValueError):
                self.faker.pydecimal(right_digits=-1)

    def test_ipv4(self) -> None:
        # Test a large number of IPs to ensure randomness and correctness
        for _ in range(1000):
            ip = self.faker.ipv4()
            self.assertIsNotNone(ip)
            self.assertIsInstance(ip, str)

            parts = ip.split(".")
            self.assertEqual(len(parts), 4)

            for part in parts:
                self.assertTrue(part.isdigit())
                self.assertTrue(0 <= int(part) <= 255)

    def test_parse_date_string(self) -> None:
        # Test 'now' and 'today' special keywords
        self.assertAlmostEqual(
            self.faker._parse_date_string("now"),
            datetime.now(timezone.utc),
            delta=timedelta(seconds=1),
        )
        self.assertAlmostEqual(
            self.faker._parse_date_string("today"),
            datetime.now(timezone.utc),
            delta=timedelta(seconds=1),
        )

        # Test days, hours, and minutes
        self.assertAlmostEqual(
            self.faker._parse_date_string("1d"),
            datetime.now(timezone.utc) + timedelta(days=1),
            delta=timedelta(seconds=1),
        )
        self.assertAlmostEqual(
            self.faker._parse_date_string("-1H"),
            datetime.now(timezone.utc) - timedelta(hours=1),
            delta=timedelta(seconds=1),
        )
        self.assertAlmostEqual(
            self.faker._parse_date_string("30M"),
            datetime.now(timezone.utc) + timedelta(minutes=30),
            delta=timedelta(seconds=1),
        )

        # Test invalid format
        with self.assertRaises(ValueError):
            self.faker._parse_date_string("1y")

    def test_date(self) -> None:
        # Test the same date for start and end
        start_date = "now"
        end_date = "+0d"
        random_date = self.faker.date(start_date, end_date)
        self.assertIsInstance(random_date, date)
        self.assertEqual(random_date, datetime.now(timezone.utc).date())

        # Test date range
        start_date = "-2d"
        end_date = "+2d"
        random_date = self.faker.date(start_date, end_date)
        self.assertIsInstance(random_date, date)
        self.assertTrue(
            datetime.now(timezone.utc).date() - timedelta(days=2)
            <= random_date
            <= datetime.now(timezone.utc).date() + timedelta(days=2)
        )

    def test_date_time(self) -> None:
        # Test the same datetime for start and end
        start_date = "now"
        end_date = "+0d"
        random_datetime = self.faker.date_time(start_date, end_date)
        self.assertIsInstance(random_datetime, datetime)
        self.assertAlmostEqual(
            random_datetime,
            datetime.now(timezone.utc),
            delta=timedelta(seconds=1),
        )

        # Test datetime range
        start_date = "-2H"
        end_date = "+2H"
        random_datetime = self.faker.date_time(start_date, end_date)
        self.assertIsInstance(random_datetime, datetime)
        self.assertTrue(
            datetime.now(timezone.utc) - timedelta(hours=2)
            <= random_datetime
            <= datetime.now(timezone.utc) + timedelta(hours=2)
        )

    def test_text_pdf(self) -> None:
        with self.subTest("All params None, should fail"):
            with self.assertRaises(ValueError):
                self.faker.pdf(
                    nb_pages=None,
                    texts=None,
                    generator=TextPdfGenerator,
                )

        with self.subTest("Without params"):
            pdf = self.faker.pdf(generator=TextPdfGenerator)
            self.assertTrue(pdf)
            self.assertIsInstance(pdf, bytes)

        with self.subTest("With `texts` provided"):
            texts = self.faker.sentences()
            pdf = self.faker.pdf(texts=texts, generator=TextPdfGenerator)
            self.assertTrue(pdf)
            self.assertIsInstance(pdf, bytes)

        with self.subTest("With `metadata` provided"):
            metadata = MetaData()
            pdf = self.faker.pdf(
                generator=TextPdfGenerator,
                metadata=metadata,
            )
            self.assertTrue(pdf)
            self.assertIsInstance(pdf, bytes)

    def test_graphic_pdf(self) -> None:
        pdf = self.faker.pdf(generator=GraphicPdfGenerator)
        self.assertTrue(pdf)
        self.assertIsInstance(pdf, bytes)

    def test_png(self) -> None:
        png = self.faker.png()
        self.assertTrue(png)
        self.assertIsInstance(png, bytes)

    def test_svg(self) -> None:
        svg = self.faker.svg()
        self.assertTrue(svg)
        self.assertIsInstance(svg, bytes)

    def test_bmp(self) -> None:
        bmp = self.faker.bmp()
        self.assertTrue(bmp)
        self.assertIsInstance(bmp, bytes)

    def test_gif(self) -> None:
        gif = self.faker.gif()
        self.assertTrue(gif)
        self.assertIsInstance(gif, bytes)

    def test_image(self):
        for image_format in {"png", "svg", "bmp", "gif"}:
            with self.subTest(image_format=image_format):
                image = self.faker.image(
                    image_format=image_format,
                )
                self.assertTrue(image)
                self.assertIsInstance(image, bytes)
        for image_format in {"bin"}:
            with self.subTest(image_format=image_format):
                with self.assertRaises(ValueError):
                    self.faker.image(image_format=image_format)

    def test_docx(self) -> None:
        with self.subTest("All params None, should fail"):
            with self.assertRaises(ValueError):
                self.faker.docx(nb_pages=None, texts=None),  # noqa

        with self.subTest("Without params"):
            docx = self.faker.docx()
            self.assertTrue(docx)
            self.assertIsInstance(docx, bytes)

        with self.subTest("With `texts` provided"):
            texts = self.faker.sentences()
            docx = self.faker.docx(texts=texts)
            self.assertTrue(docx)
            self.assertIsInstance(docx, bytes)

    def test_pdf_file(self) -> None:
        file = self.faker.pdf_file()
        self.assertTrue(os.path.exists(file.data["filename"]))

    def test_png_file(self) -> None:
        file = self.faker.png_file()
        self.assertTrue(os.path.exists(file.data["filename"]))

    def test_svg_file(self) -> None:
        file = self.faker.svg_file()
        self.assertTrue(os.path.exists(file.data["filename"]))

    def test_bmp_file(self) -> None:
        file = self.faker.bmp_file()
        self.assertTrue(os.path.exists(file.data["filename"]))

    def test_gif_file(self) -> None:
        file = self.faker.gif_file()
        self.assertTrue(os.path.exists(file.data["filename"]))

    def test_docx_file(self) -> None:
        file = self.faker.docx_file()
        self.assertTrue(os.path.exists(file.data["filename"]))

    def test_txt_file(self) -> None:
        with self.subTest("Without arguments"):
            file = self.faker.txt_file()
            self.assertTrue(os.path.exists(file.data["filename"]))

        with self.subTest("nb_chars=None"):
            file = self.faker.txt_file(nb_chars=None)
            self.assertTrue(os.path.exists(file.data["filename"]))

    def test_generic_file(self) -> None:
        with self.subTest("Without text content"):
            file = self.faker.generic_file(
                content=self.faker.text(),
                extension="txt",
            )
            self.assertTrue(os.path.exists(file.data["filename"]))

        with self.subTest("With bytes content"):
            file = self.faker.generic_file(
                content=self.faker.text().encode(),
                extension="txt",
            )
            self.assertTrue(os.path.exists(file.data["filename"]))

    def test_storage(self) -> None:
        storage = FileSystemStorage()
        with self.assertRaises(Exception):
            storage.generate_filename(extension=None)  # type: ignore

    def test_storage_integration(self) -> None:
        file = self.faker.txt_file()
        file_2 = self.faker.txt_file(basename="file_2")
        file_3 = self.faker.txt_file(basename="file_3")
        storage: FileSystemStorage = file.data["storage"]

        with self.subTest("Test os.path.exists"):
            self.assertTrue(os.path.exists(file.data["filename"]))

        with self.subTest("Test storage.exists on StringValue"):
            self.assertTrue(storage.exists(file))
        with self.subTest("Test storage.exists on rel path"):
            self.assertTrue(storage.exists(str(file)))
        with self.subTest("Test storage.exists on abs path"):
            self.assertTrue(storage.exists(file.data["filename"]))

        with self.subTest("Test storage.abspath using relative path"):
            self.assertEqual(storage.abspath(str(file)), file.data["filename"])
        with self.subTest("Test storage.abspath using absolute path"):
            self.assertEqual(
                storage.abspath(file.data["filename"]), file.data["filename"]
            )

        with self.subTest("Test storage.unlink on absolute path"):
            storage.unlink(file.data["filename"])
        self.assertFalse(storage.exists(str(file)))
        self.assertFalse(storage.exists(file.data["filename"]))

        with self.subTest("Test storage.unlink on relative path"):
            storage.unlink(str(file_2))
            self.assertFalse(storage.exists(file_2.data["filename"]))

        with self.subTest("Test storage.unlink on relative path"):
            storage.unlink(str(file_3))
            self.assertFalse(storage.exists(file_3.data["filename"]))

    def test_authorship_data(self):
        """Test `AuthorshipData`."""
        authorship_data = AuthorshipData()
        with self.subTest("Testing UnicodeDecodeError case"):
            # Creating a text file with non-UTF-8 characters.
            # Using a character that is not compatible with UTF-8 but is with
            # Latin-1. For example, the byte sequence for a character not
            # representable in UTF-8.
            file = self.faker.generic_file(
                content=b"\xff\xff",
                extension="txt",
                basename="non_utf8_file",
            )
            val = authorship_data._find_authorship_info(file.data["filename"])
            self.assertFalse(val)

    def test_metadata(self) -> None:
        """Test MetaData."""
        with self.subTest("Test str"):
            metadata = MetaData()
            content = self.faker.word()
            metadata.add_content(content)
            self.assertEqual(metadata.content, content)
        with self.subTest("Test list"):
            metadata = MetaData()
            content = self.faker.words()
            metadata.add_content(content)
            self.assertEqual(metadata.content, "\n".join(content))

    def test_faker_init(self) -> None:
        faker = Faker(alias="default")
        self.assertNotEqual(faker.alias, "default")

    def test_get_by_alias(self) -> None:
        faker = Faker.get_by_alias("default")
        self.assertIs(faker, self.faker)

    def test_factory_method(self) -> None:
        """Test FactoryMethod."""
        with self.subTest("sentence"):
            sentence_factory_method = FactoryMethod("sentence")
            generated_sentence = sentence_factory_method()
            self.assertIsInstance(generated_sentence, str)
        with self.subTest("pyint"):
            pyint_factory_method = FactoryMethod("pyint")
            generated_int = pyint_factory_method()
            self.assertIsInstance(generated_int, int)

    def test_factory_methods(self) -> None:
        # Assuming 'Faker' is the class with methods decorated by @provider
        faker = Faker()
        factory = Factory(faker)

        # Iterate through methods of Faker
        for attr_name in dir(faker):
            attr_value = getattr(faker, attr_name)
            if callable(attr_value) and getattr(
                attr_value, "is_provider", False
            ):
                # Check if Factory has the method
                self.assertTrue(hasattr(factory, attr_name))

    def test_sub_factory(self) -> None:
        """Test FACTORY and SubFactory."""

        # *************************
        # ********* Models ********
        # *************************

        class MockPydanticField:
            """Mock field simulating a Pydantic model field."""

            def __init__(self, type, default_factory):
                self.type = type
                self.default_factory = default_factory

        class MockPydanticModel:
            """Mock class simulating a Pydantic model."""

            # Adjusting __fields__ to mimic Pydantic's structure
            __fields__ = {
                "id": MockPydanticField(int, lambda: 1),
                "name": MockPydanticField(str, lambda: "default"),
                "is_active": MockPydanticField(bool, lambda: True),
                "created_at": MockPydanticField(datetime, datetime.now),
                "optional_field": MockPydanticField(
                    Optional[str], lambda: None
                ),
            }

            class Config:
                arbitrary_types_allowed = True

            id: int
            name: str
            is_active: bool
            created_at: datetime
            optional_field: Optional[str] = None

            def __init__(self, **kwargs):
                for name, value in kwargs.items():
                    setattr(self, name, value)

        class DjangoQuerySet(list):
            """Mimicking Django QuerySet class."""

            def __init__(self, instance: Union["Article", "User"]) -> None:
                super().__init__()
                self.instance = instance

            def first(self) -> Union["Article", "User"]:
                return self.instance

        class DjangoManager:
            """Mimicking Django Manager class."""

            def __init__(self, instance: Union["Article", "User"]) -> None:
                self.instance = instance

            def filter(self, *args, **kwargs) -> "DjangoQuerySet":
                return DjangoQuerySet(instance=self.instance)

        @dataclass(frozen=True)
        class Group:
            id: int
            name: str

        @dataclass
        class User:
            """User model."""

            id: int
            username: str
            first_name: str
            last_name: str
            email: str
            date_joined: datetime = field(default_factory=datetime.utcnow)
            last_login: Optional[datetime] = None
            password: Optional[str] = None
            is_superuser: bool = False
            is_staff: bool = False
            is_active: bool = True
            groups: Set[Group] = field(default_factory=set)

            def save(self, *args, **kwargs):
                """Mimicking Django's Mode save method."""
                self.save_called = True  # noqa

            def set_password(self, password: str) -> None:
                self.password = xor_transform(password)

            @classmethod
            @property
            def objects(cls):
                """Mimicking Django's Manager behaviour."""
                return DjangoManager(
                    instance=fill_dataclass(cls),  # type: ignore
                )

        @dataclass
        class Article:
            id: int
            title: str
            slug: str
            content: str
            headline: str
            category: str
            author: User
            image: Optional[
                str
            ] = None  # Use str to represent the image path or URL
            pub_date: date = field(default_factory=date.today)
            safe_for_work: bool = False
            minutes_to_read: int = 5

            def save(self, *args, **kwargs):
                """Mimicking Django's Mode save method."""
                self.save_called = True  # noqa

            @classmethod
            @property
            def objects(cls):
                """Mimicking Django's Manager behaviour."""
                return DjangoManager(
                    instance=fill_dataclass(cls),  # type: ignore
                )

        with self.subTest("fill_pydantic_model on dataclass"):
            with self.assertRaises(ValueError):
                _article = fill_pydantic_model(Article)

        with self.subTest("fill_pydantic_model"):
            _obj = fill_pydantic_model(MockPydanticModel)

        with self.subTest("fill_dataclass"):
            _article = fill_dataclass(Article)

        # ****************************
        # *********** Other **********
        # ****************************

        base_dir = Path(__file__).resolve().parent.parent
        media_root = base_dir / "media"

        storage = FileSystemStorage(root_path=media_root, rel_path="tmp")

        # ****************************
        # ******* ModelFactory *******
        # ****************************

        def set_password(user: Any, password: str) -> None:
            user.set_password(password)

        def add_to_group(user: Any, name: str) -> None:
            group = GroupFactory(name=name)
            user.groups.add(group)

        categories = (
            "art",
            "technology",
            "literature",
        )

        class GroupFactory(ModelFactory):
            id = FACTORY.pyint()  # type: ignore
            name = FACTORY.word()  # type: ignore

            class Meta:
                model = Group
                get_or_create = ("name",)

        class UserFactory(ModelFactory):
            id = FACTORY.pyint()  # type: ignore
            username = FACTORY.username()  # type: ignore
            first_name = FACTORY.first_name()  # type: ignore
            last_name = FACTORY.last_name()  # type: ignore
            email = FACTORY.email()  # type: ignore
            last_login = FACTORY.date_time()  # type: ignore
            is_superuser = False
            is_staff = False
            is_active = FACTORY.pybool()  # type: ignore
            date_joined = FACTORY.date_time()  # type: ignore
            password = PreSave(set_password, password="test1234")
            group = PostSave(add_to_group, name="TestGroup1234")

            class Meta:
                model = User

            @trait
            def is_admin_user(self, instance: User) -> None:
                instance.is_superuser = True
                instance.is_staff = True
                instance.is_active = True

            @pre_save
            def _pre_save_method(self, instance):
                instance.pre_save_called = True

            @post_save
            def _post_save_method(self, instance):
                instance.post_save_called = True

        class ArticleFactory(ModelFactory):
            id = FACTORY.pyint()  # type: ignore
            title = FACTORY.sentence()  # type: ignore
            slug = FACTORY.slug()  # type: ignore
            content = FACTORY.text()  # type: ignore
            headline = LazyAttribute(lambda o: o.content[:25])
            category = LazyFunction(partial(random.choice, categories))
            image = FACTORY.png_file(storage=storage)  # type: ignore
            pub_date = FACTORY.date()  # type: ignore
            safe_for_work = FACTORY.pybool()  # type: ignore
            minutes_to_read = FACTORY.pyint(  # type: ignore
                min_value=1, max_value=10
            )
            author = SubFactory(UserFactory)

            class Meta:
                model = Article

        with self.subTest("ModelFactory"):
            _article = ArticleFactory()

            # Testing SubFactory
            self.assertIsInstance(_article.author, User)
            self.assertIsInstance(_article.author.id, int)
            self.assertIsInstance(
                _article.author.is_staff,
                bool,
            )
            self.assertIsInstance(
                _article.author.date_joined,
                datetime,
            )

            # Testing LazyFunction
            self.assertIn(_article.category, categories)

            # Testing LazyAttribute
            self.assertIn(_article.headline, _article.content)

            # Testing Factory
            self.assertIsInstance(_article.id, int)
            self.assertIsInstance(_article.slug, str)

            # Testing hooks
            _user = _article.author
            self.assertTrue(
                hasattr(_user, "pre_save_called") and _user.pre_save_called
            )
            self.assertTrue(
                hasattr(_user, "post_save_called") and _user.post_save_called
            )

            # Testing get_or_create for Article model
            _article = ArticleFactory(id=1)
            self.assertIsInstance(_article, Article)
            self.assertEqual(_article.id, 1)

            # Testing traits
            _admin_user = UserFactory(is_admin_user=True)
            self.assertTrue(
                _admin_user.is_staff
                and _admin_user.is_superuser
                and _admin_user.is_active
            )

            # Testing PreSave
            self.assertEqual(xor_transform(str(_user.password)), "test1234")
            _user = UserFactory(
                password=PreSave(set_password, password="1234test")
            )
            self.assertEqual(xor_transform(str(_user.password)), "1234test")

            # Testing PostSave
            self.assertEqual(list(_user.groups)[0].name, "TestGroup1234")
            _user = UserFactory(
                group=PostSave(add_to_group, name="1234TestGroup")
            )
            self.assertEqual(list(_user.groups)[0].name, "1234TestGroup")

        # **********************************
        # ******* DjangoModelFactory *******
        # **********************************

        class DjangoUserFactory(DjangoModelFactory):
            id = FACTORY.pyint()  # type: ignore
            username = FACTORY.username()  # type: ignore
            first_name = FACTORY.first_name()  # type: ignore
            last_name = FACTORY.last_name()  # type: ignore
            email = FACTORY.email()  # type: ignore
            last_login = FACTORY.date_time()  # type: ignore
            is_superuser = False
            is_staff = False
            is_active = FACTORY.pybool()  # type: ignore
            date_joined = FACTORY.date_time()  # type: ignore
            password = PreSave(set_password, password="jest1234")
            group = PostSave(add_to_group, name="JestGroup1234")

            class Meta:
                model = User
                get_or_create = ("username",)

            @trait
            def is_admin_user(self, instance: User) -> None:
                instance.is_superuser = True
                instance.is_staff = True
                instance.is_active = True

            @pre_save
            def _pre_save_method(self, instance):
                instance.pre_save_called = True

            @post_save
            def _post_save_method(self, instance):
                instance.post_save_called = True

        class DjangoArticleFactory(DjangoModelFactory):
            id = FACTORY.pyint()  # type: ignore
            title = FACTORY.sentence()  # type: ignore
            slug = FACTORY.slug()  # type: ignore
            content = FACTORY.text()  # type: ignore
            headline = LazyAttribute(lambda o: o.content[:25])
            category = LazyFunction(partial(random.choice, categories))
            image = FACTORY.png_file(storage=storage)  # type: ignore
            pub_date = FACTORY.date()  # type: ignore
            safe_for_work = FACTORY.pybool()  # type: ignore
            minutes_to_read = FACTORY.pyint(  # type: ignore
                min_value=1,
                max_value=10,
            )
            author = SubFactory(DjangoUserFactory)

            class Meta:
                model = Article

            @pre_save
            def _pre_save_method(self, instance):
                instance.pre_save_called = True

            @post_save
            def _post_save_method(self, instance):
                instance.post_save_called = True

        with self.subTest("DjangoModelFactory"):
            _django_article = DjangoArticleFactory(author__username="admin")

            # Testing SubFactory
            self.assertIsInstance(_django_article.author, User)
            self.assertIsInstance(
                _django_article.author.id,  # type: ignore
                int,
            )
            self.assertIsInstance(
                _django_article.author.is_staff,  # type: ignore
                bool,
            )
            self.assertIsInstance(
                _django_article.author.date_joined,  # type: ignore
                datetime,
            )
            # Since we're mimicking Django's behaviour, the following line would
            # fail on test, however would pass when testing against real Django
            # model (as done in the examples).
            # self.assertEqual(django_article.author.username, "admin")

            # Testing Factory
            self.assertIsInstance(_django_article.id, int)
            self.assertIsInstance(_django_article.slug, str)

            # Testing hooks
            self.assertTrue(
                hasattr(_django_article, "pre_save_called")
                and _django_article.pre_save_called
            )
            self.assertTrue(
                hasattr(_django_article, "post_save_called")
                and _django_article.post_save_called
            )

            # Testing batch creation
            _django_articles = DjangoArticleFactory.create_batch(5)
            self.assertEqual(len(_django_articles), 5)
            self.assertIsInstance(_django_articles[0], Article)

            # Testing get_or_create for Article model
            _django_article = DjangoArticleFactory(id=1)
            self.assertIsInstance(_django_article, Article)

            # Testing traits
            _django_admin_user = DjangoUserFactory(is_admin_user=True)
            self.assertTrue(
                _django_admin_user.is_staff
                and _django_admin_user.is_superuser
                and _django_admin_user.is_active
            )

            # Testing PreSave
            _django_user = DjangoUserFactory()
            self.assertEqual(
                xor_transform(str(_django_user.password)),
                "jest1234",
            )
            _django_user = DjangoUserFactory(
                password=PreSave(set_password, password="1234jest")
            )
            self.assertEqual(
                xor_transform(str(_django_user.password)),
                "1234jest",
            )

            # Testing PostSave
            self.assertEqual(
                list(_django_user.groups)[0].name,  # type: ignore
                "JestGroup1234",
            )
            _django_user = DjangoUserFactory(
                group=PostSave(add_to_group, name="1234JestGroup")
            )
            self.assertEqual(
                list(_django_user.groups)[0].name,  # type: ignore
                "1234JestGroup",
            )

        # **********************************
        # ****** TortoiseModelFactory ******
        # **********************************

        class TortoiseQuerySet(list):
            """Mimicking Tortoise QuerySet class."""

            return_instance_on_query_first: bool = False

            def __init__(
                    self,
                    instance: Union["TortoiseArticle", "TortoiseUser"],
            ) -> None:
                super().__init__()
                self.instance = instance

            async def first(
                    self,
            ) -> Optional[Union["TortoiseArticle", "TortoiseUser"]]:
                if not self.return_instance_on_query_first:
                    return None
                return self.instance

        @dataclass(frozen=True)
        class TortoiseGroup:
            id: int
            name: str

            @classmethod
            def filter(cls, *args, **kwargs) -> "TortoiseQuerySet":
                return TortoiseQuerySet(instance=fill_dataclass(cls))

            async def save(self, *args, **kwargs):
                """Mimicking Django's Mode save method."""

        @dataclass
        class TortoiseUser:
            """User model."""

            id: int
            username: str
            first_name: str
            last_name: str
            email: str
            date_joined: datetime = field(default_factory=datetime.utcnow)
            last_login: Optional[datetime] = None
            password: Optional[str] = None
            is_superuser: bool = False
            is_staff: bool = False
            is_active: bool = True
            groups: Set[TortoiseGroup] = field(default_factory=set)

            def set_password(self, password: str) -> None:
                self.password = xor_transform(password)

            @classmethod
            def filter(cls, *args, **kwargs) -> "TortoiseQuerySet":
                return TortoiseQuerySet(instance=fill_dataclass(cls))

            async def save(self, *args, **kwargs):
                """Mimicking Django's Mode save method."""
                self.save_called = True  # noqa

        @dataclass
        class TortoiseArticle:
            id: int
            title: str
            slug: str
            content: str
            headline: str
            category: str
            author: TortoiseUser
            image: Optional[
                str
            ] = None  # Use str to represent the image path or URL
            pub_date: date = field(default_factory=date.today)
            safe_for_work: bool = False
            minutes_to_read: int = 5

            @classmethod
            def filter(cls, *args, **kwargs) -> "TortoiseQuerySet":
                return TortoiseQuerySet(instance=fill_dataclass(cls))

            async def save(self, *args, **kwargs):
                """Mimicking Django's Mode save method."""
                self.save_called = True  # noqa

        def add_to_tortoise_group(user: Any, name: str) -> None:
            group = TortoiseGroupFactory(name=name)
            user.groups.add(group)

        class TortoiseGroupFactory(TortoiseModelFactory):
            id = FACTORY.pyint()  # type: ignore
            name = FACTORY.word()  # type: ignore

            class Meta:
                model = TortoiseGroup
                get_or_create = ("name",)

        class TortoiseUserFactory(TortoiseModelFactory):
            id = FACTORY.pyint()  # type: ignore
            username = FACTORY.username()  # type: ignore
            first_name = FACTORY.first_name()  # type: ignore
            last_name = FACTORY.last_name()  # type: ignore
            email = FACTORY.email()  # type: ignore
            last_login = FACTORY.date_time()  # type: ignore
            is_superuser = False
            is_staff = False
            is_active = FACTORY.pybool()  # type: ignore
            date_joined = FACTORY.date_time()  # type: ignore
            password = PreSave(set_password, password="tost1234")
            group = PostSave(add_to_tortoise_group, name="TostGroup1234")

            class Meta:
                model = TortoiseUser
                get_or_create = ("username",)

            @trait
            def is_admin_user(self, instance: TortoiseUser) -> None:
                instance.is_superuser = True
                instance.is_staff = True
                instance.is_active = True

            @pre_save
            def _pre_save_method(self, instance):
                instance.pre_save_called = True

            @post_save
            def _post_save_method(self, instance):
                instance.post_save_called = True

        class TortoiseArticleFactory(TortoiseModelFactory):
            id = FACTORY.pyint()  # type: ignore
            title = FACTORY.sentence()  # type: ignore
            slug = FACTORY.slug()  # type: ignore
            content = FACTORY.text()  # type: ignore
            headline = LazyAttribute(lambda o: o.content[:25])
            category = LazyFunction(partial(random.choice, categories))
            image = FACTORY.png_file(storage=storage)  # type: ignore
            pub_date = FACTORY.date()  # type: ignore
            safe_for_work = FACTORY.pybool()  # type: ignore
            minutes_to_read = FACTORY.pyint(  # type: ignore
                min_value=1,
                max_value=10,
            )
            author = SubFactory(TortoiseUserFactory)

            class Meta:
                model = TortoiseArticle

            @pre_save
            def _pre_save_method(self, instance):
                instance.pre_save_called = True

            @post_save
            def _post_save_method(self, instance):
                instance.post_save_called = True

        with self.subTest("TortoiseModelFactory"):
            _tortoise_article = TortoiseArticleFactory(author__username="admin")

            # Testing SubFactory
            self.assertIsInstance(_tortoise_article.author, TortoiseUser)
            self.assertIsInstance(
                _tortoise_article.author.id,  # type: ignore
                int,
            )
            self.assertIsInstance(
                _tortoise_article.author.is_staff,  # type: ignore
                bool,
            )
            self.assertIsInstance(
                _tortoise_article.author.date_joined,  # type: ignore
                datetime,
            )
            # Since we're mimicking Tortoise's behaviour, the following line
            # would fail on test, however would pass when testing against
            # real Tortoise model (as done in the examples).
            # self.assertEqual(tortoise_article.author.username, "admin")

            # Testing Factory
            self.assertIsInstance(_tortoise_article.id, int)
            self.assertIsInstance(_tortoise_article.slug, str)

            # Testing hooks
            self.assertTrue(
                hasattr(_tortoise_article, "pre_save_called")
                and _tortoise_article.pre_save_called
            )
            self.assertTrue(
                hasattr(_tortoise_article, "post_save_called")
                and _tortoise_article.post_save_called
            )

            # Testing batch creation
            _tortoise_articles = TortoiseArticleFactory.create_batch(5)
            self.assertEqual(len(_tortoise_articles), 5)
            self.assertIsInstance(_tortoise_articles[0], TortoiseArticle)

            # Testing get_or_create for Article model
            _tortoise_article = TortoiseArticleFactory(id=1)
            self.assertIsInstance(_tortoise_article, TortoiseArticle)

            # Testing traits
            _tortoise_admin_user = TortoiseUserFactory(is_admin_user=True)
            self.assertTrue(
                _tortoise_admin_user.is_staff
                and _tortoise_admin_user.is_superuser
                and _tortoise_admin_user.is_active
            )

            # Testing PreSave
            _tortoise_user = TortoiseUserFactory()
            self.assertEqual(
                xor_transform(str(_tortoise_user.password)),
                "tost1234",
            )
            _tortoise_user = TortoiseUserFactory(
                password=PreSave(set_password, password="1234tost")
            )
            self.assertEqual(
                xor_transform(str(_tortoise_user.password)),
                "1234tost",
            )

            # Testing PostSave
            self.assertEqual(
                list(_tortoise_user.groups)[0].name,  # type: ignore
                "TostGroup1234",
            )
            _tortoise_user = TortoiseUserFactory(
                group=PostSave(add_to_tortoise_group, name="1234TostGroup")
            )
            self.assertEqual(
                list(_tortoise_user.groups)[0].name,  # type: ignore
                "1234TostGroup",
            )

            # **********************************
            # ** Repeat for another condition **
            TortoiseQuerySet.return_instance_on_query_first = True

            _tortoise_article = TortoiseArticleFactory(author__username="admin")
            _tortoise_user = TortoiseUserFactory(username="admin")

            # Testing SubFactory
            self.assertIsInstance(_tortoise_article.author, TortoiseUser)
            self.assertIsInstance(_tortoise_article, TortoiseArticle)
            self.assertIsInstance(_tortoise_user, TortoiseUser)
            self.assertIsInstance(
                _tortoise_article.author.id,  # type: ignore
                int,
            )
            self.assertIsInstance(
                _tortoise_article.author.is_staff,  # type: ignore
                bool,
            )
            self.assertIsInstance(
                _tortoise_article.author.date_joined,  # type: ignore
                datetime,
            )
            # Since we're mimicking Tortoise's behaviour, the following line
            # would fail on test, however would pass when testing against
            # real Tortoise model (as done in the examples).
            # self.assertEqual(_tortoise_article.author.username, "admin")

            # Testing Factory
            self.assertIsInstance(_tortoise_article.id, int)
            self.assertIsInstance(_tortoise_article.slug, str)
            self.assertIsInstance(_tortoise_user.id, int)
            self.assertIsInstance(_tortoise_user.username, str)

            # Testing hooks
            # self.assertFalse(
            #     hasattr(_tortoise_article, "pre_save_called")
            # )
            # self.assertFalse(
            #     hasattr(_tortoise_article, "post_save_called")
            # )

            # Testing batch creation
            _tortoise_articles = TortoiseArticleFactory.create_batch(5)
            self.assertEqual(len(_tortoise_articles), 5)
            self.assertIsInstance(_tortoise_articles[0], TortoiseArticle)

            # Testing traits
            _tortoise_admin_user = TortoiseUserFactory(is_admin_user=True)
            self.assertTrue(
                _tortoise_admin_user.is_staff
                and _tortoise_admin_user.is_superuser
                and _tortoise_admin_user.is_active
            )

        # **********************************
        # ***** SQLAlchemyModelFactory *****
        # **********************************

        class SQLAlchemySession:
            return_instance_on_query_first: bool = False

            def __init__(self) -> None:
                self.model = None
                self.instance = None

            def query(self, model) -> "SQLAlchemySession":
                self.model = model
                return self

            def filter_by(self, **kwargs) -> "SQLAlchemySession":
                return self

            def add(self, instance) -> None:
                self.instance = instance

            def commit(self) -> None:
                pass

            def first(self):
                if not self.return_instance_on_query_first:
                    return None

                return fill_dataclass(self.model)  # type: ignore

        def get_sqlalchemy_session():
            return SQLAlchemySession()

        @dataclass(frozen=True)
        class SQLAlchemyGroup:
            id: int
            name: str

        @dataclass
        class SQLAlchemyUser:
            """User model."""

            id: int
            username: str
            first_name: str
            last_name: str
            email: str
            date_joined: datetime = field(default_factory=datetime.utcnow)
            last_login: Optional[datetime] = None
            password: Optional[str] = None
            is_superuser: bool = False
            is_staff: bool = False
            is_active: bool = True
            groups: Set[SQLAlchemyGroup] = field(default_factory=set)

            def set_password(self, password: str) -> None:
                self.password = xor_transform(password)

        @dataclass
        class SQLAlchemyArticle:
            id: int
            title: str
            slug: str
            content: str
            headline: str
            category: str
            author: SQLAlchemyUser
            image: Optional[
                str
            ] = None  # Use str to represent the image path or URL
            pub_date: date = field(default_factory=date.today)
            safe_for_work: bool = False
            minutes_to_read: int = 5

        def add_to_sqlalchemy_group(user: Any, name: str) -> None:
            group = SQLAlchemyGroupFactory(name=name)
            user.groups.add(group)

        class SQLAlchemyGroupFactory(SQLAlchemyModelFactory):
            id = FACTORY.pyint()  # type: ignore
            name = FACTORY.word()  # type: ignore

            class Meta:
                model = SQLAlchemyGroup
                get_or_create = ("name",)

            class MetaSQLAlchemy:
                get_session = get_sqlalchemy_session

        class SQLAlchemyUserFactory(SQLAlchemyModelFactory):
            id = FACTORY.pyint()  # type: ignore
            username = FACTORY.username()  # type: ignore
            first_name = FACTORY.first_name()  # type: ignore
            last_name = FACTORY.last_name()  # type: ignore
            email = FACTORY.email()  # type: ignore
            last_login = FACTORY.date_time()  # type: ignore
            is_superuser = False
            is_staff = False
            is_active = FACTORY.pybool()  # type: ignore
            date_joined = FACTORY.date_time()  # type: ignore
            password = PreSave(set_password, password="sest1234")
            group = PostSave(add_to_sqlalchemy_group, name="SestGroup1234")

            class Meta:
                model = SQLAlchemyUser
                get_or_create = ("username",)

            class MetaSQLAlchemy:
                get_session = get_sqlalchemy_session

            @trait
            def is_admin_user(self, instance: SQLAlchemyUser) -> None:
                instance.is_superuser = True
                instance.is_staff = True
                instance.is_active = True

            @pre_save
            def _pre_save_method(self, instance):
                instance.pre_save_called = True

            @post_save
            def _post_save_method(self, instance):
                instance.post_save_called = True

        class SQLAlchemyArticleFactory(SQLAlchemyModelFactory):
            id = FACTORY.pyint()  # type: ignore
            title = FACTORY.sentence()  # type: ignore
            slug = FACTORY.slug()  # type: ignore
            content = FACTORY.text()  # type: ignore
            headline = LazyAttribute(lambda o: o.content[:25])
            category = LazyFunction(partial(random.choice, categories))
            image = FACTORY.png_file(storage=storage)  # type: ignore
            pub_date = FACTORY.date()  # type: ignore
            safe_for_work = FACTORY.pybool()  # type: ignore
            minutes_to_read = FACTORY.pyint(  # type: ignore
                min_value=1,
                max_value=10,
            )
            author = SubFactory(SQLAlchemyUserFactory)

            class Meta:
                model = SQLAlchemyArticle

            class MetaSQLAlchemy:
                get_session = get_sqlalchemy_session

            @pre_save
            def _pre_save_method(self, instance):
                instance.pre_save_called = True

            @post_save
            def _post_save_method(self, instance):
                instance.post_save_called = True

        with self.subTest("SQLAlchemyModelFactory"):
            _sqlalchemy_article = SQLAlchemyArticleFactory(
                author__username="admin"
            )

            # Testing SubFactory
            self.assertIsInstance(_sqlalchemy_article.author, SQLAlchemyUser)
            self.assertIsInstance(
                _sqlalchemy_article.author.id,  # type: ignore
                int,
            )
            self.assertIsInstance(
                _sqlalchemy_article.author.is_staff,  # type: ignore
                bool,
            )
            self.assertIsInstance(
                _sqlalchemy_article.author.date_joined,  # type: ignore
                datetime,
            )
            # Since we're mimicking SQLAlchemy's behaviour, the following line
            # would fail on test, however would pass when testing against real
            # SQLAlchemy model (as done in the examples).
            # self.assertEqual(sqlalchemy_article.author.username, "admin")

            # Testing Factory
            self.assertIsInstance(_sqlalchemy_article.id, int)
            self.assertIsInstance(_sqlalchemy_article.slug, str)

            # Testing hooks
            self.assertTrue(
                hasattr(_sqlalchemy_article, "pre_save_called")
                and _sqlalchemy_article.pre_save_called
            )
            self.assertTrue(
                hasattr(_sqlalchemy_article, "post_save_called")
                and _sqlalchemy_article.post_save_called
            )

            # Testing batch creation
            _sqlalchemy_articles = SQLAlchemyArticleFactory.create_batch(5)
            self.assertEqual(len(_sqlalchemy_articles), 5)
            self.assertIsInstance(_sqlalchemy_articles[0], SQLAlchemyArticle)

            # Testing traits
            _sqlalchemy_admin_user = SQLAlchemyUserFactory(is_admin_user=True)
            self.assertTrue(
                _sqlalchemy_admin_user.is_staff
                and _sqlalchemy_admin_user.is_superuser
                and _sqlalchemy_admin_user.is_active
            )

            # Testing PreSave
            _sqlalchemy_user = SQLAlchemyUserFactory()
            self.assertEqual(
                xor_transform(str(_sqlalchemy_user.password)), "sest1234"
            )
            _sqlalchemy_user = SQLAlchemyUserFactory(
                password=PreSave(set_password, password="1234sest")
            )
            self.assertEqual(
                xor_transform(str(_sqlalchemy_user.password)), "1234sest"
            )

            # Testing PostSave
            self.assertEqual(
                list(_sqlalchemy_user.groups)[0].name,  # type: ignore
                "SestGroup1234",
            )
            _sqlalchemy_user = SQLAlchemyUserFactory(
                group=PostSave(add_to_sqlalchemy_group, name="1234SestGroup")
            )
            self.assertEqual(
                list(_sqlalchemy_user.groups)[0].name,  # type: ignore
                "1234SestGroup",
            )

            # Repeat SQLAlchemy tests for another condition
            SQLAlchemySession.return_instance_on_query_first = True

            _sqlalchemy_article = SQLAlchemyArticleFactory(
                author__username="admin"
            )
            _sqlalchemy_user = SQLAlchemyUserFactory(username="admin")

            # Testing SubFactory
            self.assertIsInstance(_sqlalchemy_article.author, SQLAlchemyUser)
            self.assertIsInstance(_sqlalchemy_article, SQLAlchemyArticle)
            self.assertIsInstance(_sqlalchemy_user, SQLAlchemyUser)
            self.assertIsInstance(
                _sqlalchemy_article.author.id,  # type: ignore
                int,
            )
            self.assertIsInstance(
                _sqlalchemy_article.author.is_staff,  # type: ignore
                bool,
            )
            self.assertIsInstance(
                _sqlalchemy_article.author.date_joined,  # type: ignore
                datetime,
            )
            # Since we're mimicking SQLAlchemy's behaviour, the following line
            # would fail on test, however would pass when testing against real
            # SQLAlchemy model (as done in the examples).
            # self.assertEqual(sqlalchemy_article.author.username, "admin")

            # Testing Factory
            self.assertIsInstance(_sqlalchemy_article.id, int)
            self.assertIsInstance(_sqlalchemy_article.slug, str)
            self.assertIsInstance(_sqlalchemy_user.id, int)
            self.assertIsInstance(_sqlalchemy_user.username, str)

            # Testing hooks
            self.assertFalse(hasattr(_sqlalchemy_article, "pre_save_called"))
            self.assertFalse(hasattr(_sqlalchemy_article, "post_save_called"))

            # Testing batch creation
            _sqlalchemy_articles = SQLAlchemyArticleFactory.create_batch(5)
            self.assertEqual(len(_sqlalchemy_articles), 5)
            self.assertIsInstance(_sqlalchemy_articles[0], SQLAlchemyArticle)

    def test_registry_integration(self) -> None:
        """Test `add`."""
        # Create a TXT file.
        txt_file_1 = FAKER.txt_file()

        with self.subTest("Check if `add` works"):
            # Check if `add` works (the file is in the registry)
            self.assertIn(txt_file_1, FILE_REGISTRY._registry)

        with self.subTest("Check if `search` works"):
            # Check if `search` works
            res = FILE_REGISTRY.search(str(txt_file_1))
            self.assertIsNotNone(res)
            self.assertEqual(res, txt_file_1)

        with self.subTest("Check if `remove` by `StringValue` works"):
            # Check if `remove` by `StringValue`.
            FILE_REGISTRY.remove(txt_file_1)
            self.assertNotIn(txt_file_1, FILE_REGISTRY._registry)

        with self.subTest("Check if `remove` by `str` works"):
            # Create another TXT file and check if `remove` by `str` works.
            txt_file_2 = FAKER.txt_file()
            self.assertIn(txt_file_2, FILE_REGISTRY._registry)
            FILE_REGISTRY.remove(str(txt_file_2))
            self.assertNotIn(txt_file_2, FILE_REGISTRY._registry)

        with self.subTest("Check if `clean_up` works"):
            # Check if `clean_up` works
            txt_file_3 = FAKER.txt_file()
            txt_file_4 = FAKER.txt_file()
            txt_file_5 = FAKER.txt_file()
            self.assertIn(txt_file_3, FILE_REGISTRY._registry)
            self.assertIn(txt_file_4, FILE_REGISTRY._registry)
            self.assertIn(txt_file_5, FILE_REGISTRY._registry)

            FILE_REGISTRY.clean_up()
            self.assertNotIn(txt_file_3, FILE_REGISTRY._registry)
            self.assertNotIn(txt_file_4, FILE_REGISTRY._registry)
            self.assertNotIn(txt_file_5, FILE_REGISTRY._registry)

    def test_remove_by_string_not_found(self):
        res = FILE_REGISTRY.remove("i_do_not_exist.ext")
        self.assertFalse(res)

    def test_remove_exceptions(self):
        txt_file = FAKER.txt_file()
        txt_file.data["storage"].unlink(txt_file)

        res = FILE_REGISTRY.remove(txt_file)
        self.assertFalse(res)

