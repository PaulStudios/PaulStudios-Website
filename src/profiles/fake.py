"""
https://github.com/barseghyanartur/fake.py/
"""

import asyncio
import contextlib
import io
import logging
import os
import random
import re
import string
import unittest
import uuid
import zipfile
import zlib
from abc import abstractmethod
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from functools import partial
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir
from threading import Lock
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Set,
    TextIO,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)
from uuid import UUID

__title__ = "fake.py"
__version__ = "0.6.9"
__author__ = "Artur Barseghyan <artur.barseghyan@gmail.com>"
__copyright__ = "2023-2024 Artur Barseghyan"
__license__ = "MIT"
__all__ = (
    "AuthorshipData",
    "BaseStorage",
    "DjangoModelFactory",
    "DocxGenerator",
    "FACTORY",
    "FAKER",
    "FILE_REGISTRY",
    "Factory",
    "FactoryMethod",
    "Faker",
    "FileRegistry",
    "FileSystemStorage",
    "GraphicPdfGenerator",
    "LazyAttribute",
    "LazyFunction",
    "MetaData",
    "ModelFactory",
    "PROVIDER_REGISTRY",
    "PostSave",
    "PreSave",
    "SQLAlchemyModelFactory",
    "StringValue",
    "SubFactory",
    "TextPdfGenerator",
    "TortoiseModelFactory",
    "fill_dataclass",
    "fill_pydantic_model",
    "post_save",
    "pre_save",
    "provider",
    "run_async_in_thread",
    "trait",
    "xor_transform",
)

LOGGER = logging.getLogger(__name__)

# ************************************************
# ******************* Public *********************
# ************************************************

PDF_TEXT_TPL_PAGE_OBJECT = """{page_num} 0 obj
<</Type /Page
/Parent 3 0 R
/Resources 2 0 R
/Contents {content_obj_num} 0 R
>>
endobj
"""

PDF_TEXT_TPL_CONTENT_OBJECT = """{obj_num} 0 obj
<</Length {stream_length}>>
stream
{content}
endstream
endobj
"""

PDF_GRAPHIC_TPL_IMAGE_OBJECT = """{obj_num} 0 obj
<</Type /XObject
/Subtype /Image
/Width {width}
/Height {height}
/ColorSpace /DeviceRGB
/BitsPerComponent 8
/Filter /FlateDecode
/Length {stream_length}>>
stream
"""

PDF_GRAPHIC_TPL_PAGE_OBJECT = """{page_obj_num} 0 obj
<</Type /Page
/Parent 3 0 R
/Resources <</XObject <</Im{image_obj_num} {image_obj_num} 0 R>> >>
/Contents {content_obj_num} 0 R
>>
endobj
"""

PDF_GRAPHIC_TPL_CONTENT_OBJECT = """{content_obj_num} 0 obj
<</Length 44>>
stream
q
100 0 0 100 0 0 cm
/Im{image_obj_num} Do
Q
endstream
endobj
"""

PDF_GRAPHIC_TPL_PAGES_OBJECT = """3 0 obj
<</Type /Pages
/Kids [{pages_kids}]
/Count {num_pages}
>>
endobj
"""

PDF_GRAPHIC_TPL_CATALOG_OBJECT = """1 0 obj
<</Type /Catalog
/Pages 3 0 R
>>
endobj
"""

PDF_GRAPHIC_TPL_TRAILER_OBJECT = """trailer
<</Size 6
/Root 1 0 R>>
startxref
"""

SVG_TPL = """
<svg width="{width}px" height="{height}px" xmlns="http://www.w3.org/2000/svg">
<rect width="100%" height="100%" fill="rgb{color}" />
</svg>"""

DOCX_TPL_DOC_HEADER = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'  # noqa
    "<w:body>"
)

DOCX_TPL_DOC_FOOTER = "</w:body></w:document>"

DOC_TPL_DOC_STRUCTURE_RELS = (
    b"<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
    b"<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>"  # noqa
    b"<Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument' Target='word/document.xml'/>"  # noqa
    b"</Relationships>"
)

DOC_TPL_DOC_STRUCTURE_WORD_RELS = (
    b"<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
    b"<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>"  # noqa
    b"<Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles' Target='styles.xml'/>"  # noqa
    b"</Relationships>"
)

DOC_TPL_DOC_STRUCTURE_WORD_STYLES = (
    b"<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
    b"<w:styles xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>"  # noqa
    b"<w:style w:type='paragraph' w:default='1' w:styleId='Normal'>"
    b"<w:name w:val='Normal'/><w:qFormat/></w:style></w:styles>"
)

DOC_TPL_DOC_STRUCTURE_CONTENT_TYPES = (
    b"<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
    b"<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'>"  # noqa
    b"<Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/>"  # noqa
    b"<Default Extension='xml' ContentType='application/xml'/>"
    b"<Override PartName='/word/document.xml' ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'/>"  # noqa
    b"<Override PartName='/word/styles.xml' ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml'/>"  # noqa
    b"</Types>"
)


class MetaData:
    __slots__ = ("content",)

    def __init__(self):
        self.content: Optional[str] = None

    def add_content(self, content: Union[str, List[str]]) -> None:
        if isinstance(content, list):
            self.content = "\n".join(content)
        else:
            self.content = content


class StringValue(str):
    __slots__ = ("data",)

    data: Dict[str, Any]

    def __new__(cls, value, *args, **kwargs):
        obj = str.__new__(cls, value)
        obj.data = {}
        return obj


class FileRegistry:
    """Stores list `StringValue` instances.

    .. code-block:: python

        from fake import FAKER, FILE_REGISTRY

        txt_file_1 = FAKER.txt_file()
        txt_file_2 = FAKER.txt_file()
        ...
        txt_file_n = FAKER.txt_file()

        # The FileRegistry._registry would then contain this:
        {
            txt_file_1,
            txt_file_2,
            ...,
            txt_file_n,
        }

        # Clean up created files as follows:
        FILE_REGISTRY.clean_up()
    """

    def __init__(self) -> None:
        self._registry: Set[StringValue] = set()
        self._lock = Lock()

    def add(self, string_value: StringValue) -> None:
        with self._lock:
            self._registry.add(string_value)

    def remove(self, string_value: Union[StringValue, str]) -> bool:
        if not isinstance(string_value, StringValue):
            string_value = self.search(string_value)  # type: ignore

        if not string_value:
            return False

        with self._lock:
            # No error if the element doesn't exist
            self._registry.discard(string_value)  # type: ignore
            try:
                string_value.data["storage"].unlink(  # type: ignore
                    string_value.data["filename"]  # type: ignore
                )
                return True
            except Exception as e:
                LOGGER.error(
                    f"Failed to unlink file "
                    f"{string_value.data['filename']}: {e}"  # type: ignore
                )
            return False

    def search(self, value: str) -> Optional[StringValue]:
        with self._lock:
            for string_value in self._registry:
                if string_value == value:
                    return string_value
        return None

    def clean_up(self) -> None:
        with self._lock:
            while self._registry:
                file = self._registry.pop()
                try:
                    file.data["storage"].unlink(file.data["filename"])
                except Exception as err:
                    LOGGER.error(
                        f"Failed to unlink file {file.data['filename']}: {err}"
                    )


FILE_REGISTRY = FileRegistry()


class BaseStorage:
    """Base storage."""

    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    @abstractmethod
    def generate_filename(
        self: "BaseStorage",
        extension: str,
        prefix: Optional[str] = None,
        basename: Optional[str] = None,
    ) -> Any:
        """Generate filename."""

    @abstractmethod
    def write_text(
        self: "BaseStorage",
        filename: Any,
        data: str,
        encoding: Optional[str] = None,
    ) -> int:
        """Write text."""

    @abstractmethod
    def write_bytes(self: "BaseStorage", filename: Any, data: bytes) -> int:
        """Write bytes."""

    @abstractmethod
    def exists(self: "BaseStorage", filename: Any) -> bool:
        """Check if file exists."""

    @abstractmethod
    def relpath(self: "BaseStorage", filename: Any) -> str:
        """Return relative path."""

    @abstractmethod
    def abspath(self: "BaseStorage", filename: Any) -> str:
        """Return absolute path."""

    @abstractmethod
    def unlink(self: "BaseStorage", filename: Any) -> None:
        """Delete the file."""


class FileSystemStorage(BaseStorage):
    """File storage class using pathlib for path handling.

    Usage example:

    .. code-block:: python

        from fake import FAKER, FileSystemStorage

        storage = FileSystemStorage()
        docx_file = storage.generate_filename(prefix="zzz_", extension="docx")
        storage.write_bytes(docx_file, FAKER.docx())

    Initialization with params:

    .. code-block:: python

        from fake import FAKER, FileSystemStorage

        storage = FileSystemStorage()
        docx_file = FAKER.docx_file(storage=storage)
    """

    def __init__(
        self: "FileSystemStorage",
        root_path: Optional[Union[str, Path]] = gettempdir(),
        rel_path: Optional[str] = "tmp",
        *args,
        **kwargs,
    ) -> None:
        """
        :param root_path: Path of your files root directory (e.g., Django's
            `settings.MEDIA_ROOT`).
        :param rel_path: Relative path (from root directory).
        """
        self.root_path = Path(root_path or "")
        self.rel_path = Path(rel_path or "")
        super().__init__(*args, **kwargs)

    def generate_filename(
        self: "FileSystemStorage",
        extension: str,
        prefix: Optional[str] = None,
        basename: Optional[str] = None,
    ) -> str:
        """Generate filename."""
        dir_path = self.root_path / self.rel_path
        dir_path.mkdir(parents=True, exist_ok=True)

        if not extension:
            raise Exception("Extension shall be given!")

        if basename:
            return str(dir_path / f"{basename}.{extension}")
        else:
            temp_file = NamedTemporaryFile(
                prefix=prefix,
                dir=str(dir_path),
                suffix=f".{extension}",
                delete=False,
            )
            return temp_file.name

    def write_text(
        self: "FileSystemStorage",
        filename: str,
        data: str,
        encoding: Optional[str] = None,
    ) -> int:
        """Write text."""
        path = Path(filename)
        path.write_text(data, encoding=encoding or "utf-8")
        return len(data)

    def write_bytes(
        self: "FileSystemStorage",
        filename: str,
        data: bytes,
    ) -> int:
        """Write bytes."""
        path = Path(filename)
        path.write_bytes(data)
        return len(data)

    def exists(self: "FileSystemStorage", filename: str) -> bool:
        """Check if file exists."""
        file_path = Path(filename)
        if file_path.is_absolute():
            return file_path.exists()
        return (self.root_path / file_path).exists()

    def relpath(self: "FileSystemStorage", filename: str) -> str:
        """Return relative path."""
        return str(Path(filename).relative_to(self.root_path))

    def abspath(self: "FileSystemStorage", filename: str) -> str:
        """Return absolute path."""
        file_path = Path(filename)
        if file_path.is_absolute():
            return str(file_path.resolve())
        return str((self.root_path / file_path).resolve())

    def unlink(self: "FileSystemStorage", filename: str) -> None:
        """Delete the file."""
        file_path = Path(filename)
        if file_path.is_absolute():
            file_path.unlink()
        else:
            (self.root_path / file_path).unlink()


class TextPdfGenerator:
    """Text PDF generatr.

    Usage example:

    .. code-block:: python

        from pathlib import Path
        from fake import FAKER, TextPdfGenerator

        Path("/tmp/text_example.pdf").write_bytes(
            FAKER.pdf(nb_pages=100, generator=TextPdfGenerator)
        )
    """

    nb_pages: int
    texts: List[str]

    def __init__(self, faker: "Faker") -> None:
        self.faker = faker

    def _add_page_object(self, page_num, content_obj_num):
        return PDF_TEXT_TPL_PAGE_OBJECT.format(
            page_num=page_num,
            content_obj_num=content_obj_num,
        )

    def _add_content_object(self, obj_num, page_text):
        content = f"BT /F1 24 Tf 100 700 Td ({page_text}) Tj ET"
        stream_length = len(content)
        return PDF_TEXT_TPL_CONTENT_OBJECT.format(
            obj_num=obj_num,
            stream_length=stream_length,
            content=content,
        )

    def create(
        self,
        nb_pages: Optional[int] = None,
        texts: Optional[List[str]] = None,
        metadata: Optional[MetaData] = None,
        **kwargs,
    ) -> bytes:
        # Initialization
        if not nb_pages and not texts:
            raise ValueError(
                "Either `nb_pages` or `texts` arguments shall be given."
            )
        if texts:
            self.nb_pages: int = len(texts)
            self.texts = texts
        else:
            self.nb_pages: int = nb_pages or 1
            self.texts = self.faker.sentences(nb=self.nb_pages)

        if metadata:
            metadata.add_content(self.texts)

        # Construction
        pdf_bytes = io.BytesIO()

        pdf_bytes.write(b"%PDF-1.0\n")
        pdf_bytes.write(b"1 0 obj\n<</Type /Catalog/Pages 3 0 R>>\nendobj\n")
        pdf_bytes.write(
            b"2 0 obj\n<</Font <</F1 <</Type /Font/Subtype /Type1/BaseFont "
            b"/Helvetica>>>>\nendobj\n"
        )
        pdf_bytes.write(b"3 0 obj\n<</Type /Pages/Kids [")

        page_objs = []
        content_objs = []
        for i, page_text in enumerate(self.texts):
            page_obj_num = 4 + 2 * i
            content_obj_num = page_obj_num + 1
            page_objs.append(
                self._add_page_object(page_obj_num, content_obj_num)
            )
            content_objs.append(
                self._add_content_object(content_obj_num, page_text)
            )
            pdf_bytes.write(f"{page_obj_num} 0 R ".encode())

        pdf_bytes.write(f"] /Count {str(self.nb_pages)}>>\nendobj\n".encode())

        for page_obj in page_objs:
            pdf_bytes.write(page_obj.encode())
        for content_obj in content_objs:
            pdf_bytes.write(content_obj.encode())

        pdf_bytes.write(f"xref\n0 {str(4 + 2 * self.nb_pages)}\n".encode())
        pdf_bytes.write(b"0000000000 65535 f \n")
        pdf_bytes.write(
            b"0000000010 00000 n \n0000000057 00000 n \n0000000103 00000 n \n"
        )
        offset = 149
        for i in range(self.nb_pages):
            pdf_bytes.write(f"{offset:010} 00000 n \n".encode())
            offset += 78
            pdf_bytes.write(f"{offset:010} 00000 n \n".encode())
            offset += 73

        pdf_bytes.write(
            f"trailer\n<</Size {str(4 + 2 * self.nb_pages)}/Root 1 0 R>>\n"
            f"".encode()
        )
        pdf_bytes.write(b"startxref\n564\n%%EOF")

        return pdf_bytes.getvalue()


class GraphicPdfGenerator:
    """Graphic PDF generatr.

    Usage example:

    .. code-block:: python

        from pathlib import Path
        from fake import FAKER, GraphicPdfGenerator

        Path("/tmp/graphic_example.pdf").write_bytes(
            FAKER.pdf(nb_pages=100, generator=GraphicPdfGenerator)
        )
    """

    nb_pages: int
    image_size: Tuple[int, int]
    image_color: Tuple[int, int, int]

    def __init__(self, faker: "Faker") -> None:
        self.faker = faker

    def _create_raw_image_data(self):
        width, height = self.image_size
        # Create uncompressed raw RGB data
        raw_data = bytes(self.image_color) * width * height
        return zlib.compress(raw_data)

    def _add_image_object(self, pdf_bytes, obj_num):
        width, height = self.image_size
        image_stream = self._create_raw_image_data()
        stream_length = len(image_stream)
        pdf_bytes.write(
            PDF_GRAPHIC_TPL_IMAGE_OBJECT.format(
                obj_num=obj_num,
                width=width,
                height=height,
                stream_length=stream_length,
            ).encode()
        )
        pdf_bytes.write(image_stream)
        pdf_bytes.write(b"\nendstream\nendobj\n")

    def create(
        self,
        nb_pages: int = 1,
        image_size: Tuple[int, int] = (100, 100),
        image_color: Tuple[int, int, int] = (255, 0, 0),
        **kwargs,
    ) -> bytes:
        # Initialization
        self.nb_pages = nb_pages
        self.image_size = image_size
        self.image_color = image_color

        # Construction
        pdf_bytes = io.BytesIO()
        pdf_bytes.write(b"%PDF-1.0\n")

        # Image object number
        image_obj_num = 4

        # Positions in the PDF for the xref table
        positions = [pdf_bytes.tell()]

        # Add image object
        self._add_image_object(pdf_bytes, image_obj_num)
        positions.append(pdf_bytes.tell())

        # Add pages
        for i in range(self.nb_pages):
            page_obj_num = 5 + i
            content_obj_num = page_obj_num + self.nb_pages
            pdf_bytes.write(
                PDF_GRAPHIC_TPL_PAGE_OBJECT.format(
                    page_obj_num=page_obj_num,
                    image_obj_num=image_obj_num,
                    content_obj_num=content_obj_num,
                ).encode()
            )
            positions.append(pdf_bytes.tell())

            # Content stream that uses the image
            pdf_bytes.write(
                PDF_GRAPHIC_TPL_CONTENT_OBJECT.format(
                    content_obj_num=content_obj_num,
                    image_obj_num=image_obj_num,
                ).encode()
            )
            positions.append(pdf_bytes.tell())

        # Pages object
        pages_kids = " ".join([f"{5 + i} 0 R" for i in range(self.nb_pages)])
        pdf_bytes.write(
            PDF_GRAPHIC_TPL_PAGES_OBJECT.format(
                pages_kids=pages_kids,
                num_pages=self.nb_pages,
            ).encode()
        )
        positions.append(pdf_bytes.tell())

        # Catalog object
        pdf_bytes.write(PDF_GRAPHIC_TPL_CATALOG_OBJECT.encode())
        positions.append(pdf_bytes.tell())

        # xref table
        pdf_bytes.write(b"xref\n0 1\n0000000000 65535 f \n")
        for pos in positions:
            pdf_bytes.write(f"{pos:010} 00000 n \n".encode())

        # Trailer
        pdf_bytes.write(PDF_GRAPHIC_TPL_TRAILER_OBJECT.encode())
        pdf_bytes.write(f"{positions[-1]}\n".encode())
        pdf_bytes.write(b"%%EOF")

        return pdf_bytes.getvalue()


class AuthorshipData:
    _authorship_data: Dict[str, List[str]] = {}
    first_names: Set[str] = set()
    last_names: Set[str] = set()

    def _extract_info(self, file: TextIO) -> List[str]:
        return [
            line.strip()
            for line in file
            if "__author__" in line or "Author:" in line
        ]

    def _find_authorship_info(self, file_path: str) -> List[str]:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return self._extract_info(file)
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as file:
                return self._extract_info(file)

    def _extract_authorship_info_from_stdlib(self) -> None:
        stdlib_path = os.path.dirname(os.__file__)

        for root, dirs, files in os.walk(stdlib_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    authorship_info = self._find_authorship_info(file_path)
                    if authorship_info:
                        self._authorship_data[file_path] = authorship_info

    def _extract_names(self) -> None:
        """Extract first and last names from authorship information.
        Ensures that multi-part last names are treated as a single entity.
        """
        # Patterns for different cases
        patterns = {
            # For simple cases like '# Author: <author>'
            "simple": r"# Author: ([\w\s\-\']+)",
            # For cases like '__author__ = "<author> <email>"'
            "email_in_brackets": r'__author__\s*=\s*"([\w\s\-\']+)',
            # For multiple authors like '# Author: <author>, <author>'
            "multiple_authors": r"# Author: ([\w\s\-\']+), ([\w\s\-\']+)",
            # For cases like '# Author: <author>, <email>'
            "author_with_email": r"# Author: ([\w\s\-\']+), \w+@[\w\.-]+",
        }

        for info_list in self._authorship_data.values():
            for info in info_list:
                # Ignoring anything after '--', emails, and dates
                info = re.sub(
                    (
                        r"--.*|<[\w\.-]+@[\w\.-]+>|\b\d{4}\b|\bJanuary\b|"
                        r"\bFebruary\b|\bMarch\b|\bApril\b|\bMay\b|\bJune\b|"
                        r"\bJuly\b|\bAugust\b|\bSeptember\b|\bOctober\b|"
                        r"\bNovember\b|\bDecember\b"
                    ),
                    "",
                    info,
                )

                for pattern in patterns.values():
                    found_names = re.findall(pattern, info)
                    for name in found_names:
                        if isinstance(name, tuple):
                            # In case of multiple authors
                            for n in name:
                                split_name = n.strip().split()
                                if len(split_name) >= 2:
                                    if split_name[0] not in {"The"}:
                                        self.first_names.add(split_name[0])
                                    self.last_names.add(
                                        " ".join(split_name[1:])
                                    )  # Joining multi-part last names
                        else:
                            split_name = name.strip().split()
                            if len(split_name) >= 2:
                                if split_name[0] not in {"The"}:
                                    self.first_names.add(split_name[0])
                                self.last_names.add(
                                    " ".join(split_name[1:])
                                )  # Joining multi-part last names

    def __init__(self):
        self._extract_authorship_info_from_stdlib()
        self._extract_names()


class DocxGenerator:
    """DocxGenerator - generates a DOCX file with text.

    Usage example:

    .. code-block:: python

        from pathlib import Path
        from fake import FAKER

        Path("/tmp/example.docx").write_bytes(FAKER.docx(nb_pages=100))
    """

    def __init__(self, faker: "Faker") -> None:
        self.faker = faker

    def _create_page(self, text: str, is_last_page: bool) -> str:
        page_content = f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"
        if not is_last_page:
            page_content += '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
        return page_content

    def create(
        self,
        nb_pages: Optional[int] = None,
        texts: Optional[List[str]] = None,
        metadata: Optional[MetaData] = None,
    ) -> bytes:
        if not nb_pages and not texts:
            raise ValueError(
                "Either `nb_pages` or `texts` arguments shall be given."
            )
        if texts:
            nb_pages = len(texts)
        else:
            texts = self.faker.sentences(nb=nb_pages)

        if metadata:
            metadata.add_content(texts)  # type: ignore

        # Construct the main document content
        document_content = DOCX_TPL_DOC_HEADER
        for i, page_text in enumerate(texts):  # type: ignore
            document_content += self._create_page(
                page_text, i == nb_pages - 1  # type: ignore
            )
        document_content += DOCX_TPL_DOC_FOOTER

        # Basic structure of a DOCX file
        docx_structure = {
            "word/document.xml": document_content.encode(),
            "_rels/.rels": DOC_TPL_DOC_STRUCTURE_RELS,
            "word/_rels/document.xml.rels": DOC_TPL_DOC_STRUCTURE_WORD_RELS,
            "word/styles.xml": DOC_TPL_DOC_STRUCTURE_WORD_STYLES,
            "[Content_Types].xml": DOC_TPL_DOC_STRUCTURE_CONTENT_TYPES,
        }

        # Create the DOCX file (ZIP archive)
        docx_bytes = io.BytesIO()
        with zipfile.ZipFile(docx_bytes, "w") as docx:
            for path, content in docx_structure.items():
                docx.writestr(path, content)

        return docx_bytes.getvalue()


IMAGE_SERVICES = (
    "https://picsum.photos/{width}/{height}",
    "https://dummyimage.com/{width}x{height}",
    "https://placekitten.com/{width}/{height}",
    "https://loremflickr.com/{width}/{height}",
)

# Global registry for provider methods
UID_REGISTRY: Dict[str, "Faker"] = {}
ALIAS_REGISTRY: Dict[str, "Faker"] = {}
PROVIDER_REGISTRY: Dict[str, Set] = defaultdict(set)


class Provider:
    def __init__(self, func):
        self.func = func
        self.is_provider = True
        self.registered_name = None

    def __set_name__(self, owner, name):
        module = owner.__module__
        class_name = owner.__name__
        class_qualname = f"{module}.{class_name}"
        self.registered_name = f"{module}.{class_name}.{name}"
        PROVIDER_REGISTRY[class_qualname].add(self.func.__name__)

    def __get__(self, instance, owner):
        # Return a method bound to the instance or the unbound function
        return self.func.__get__(instance, owner)


def provider(func):
    return Provider(func)


class Faker:
    """fake.py - simplified, standalone alternative with no dependencies.

    ----

    Usage example:

    .. code-block:: python

        from fake import FAKER

        print(FAKER.first_name())  # Random first name
        print(FAKER.last_name())  # Random last name
        print(FAKER.name())  # Random name
        print(FAKER.word())  # Random word from the Zen of Python
        print(FAKER.words(nb=3))  # List of 3 random words from Zen of Python
        print(FAKER.sentence())  # Random sentence (5 random words by default)
        print(FAKER.paragraph())  # Paragraph (5 random sentences by default)
        print(FAKER.paragraphs())  # 3 random paragraphs
        print(FAKER.text())  # Random text up to 200 characters
        print(FAKER.file_name())  # Random filename with '.txt' extension
        print(FAKER.email())  # Random email
        print(FAKER.url())  # Random URL
        print(FAKER.pyint())  # Random integer
        print(FAKER.pybool())  # Random boolean
        print(FAKER.pystr())  # Random string
        print(FAKER.pyfloat())  # Random float

    ----

    PDF:

    .. code-block:: python

        from pathlib import Path
        from fake import FAKER, TextPdfGenerator, GraphicPdfGenerator

        Path("/tmp/graphic_pdf.pdf").write_bytes(
            FAKER.pdf(nb_pages=100, generator=GraphicPdfGenerator)
        )

        Path("/tmp/text_pdf.pdf").write_bytes(
            FAKER.pdf(nb_pages=100, generator=TextPdfGenerator)
        )

    ----

    Various image formats:

    .. code-block:: python

        from pathlib import Path
        from fake import FAKER

        Path("/tmp/image.png").write_bytes(FAKER.png())

        Path("/tmp/image.svg").write_bytes(FAKER.svg())

        Path("/tmp/image.bmp").write_bytes(FAKER.bmp())

        Path("/tmp/image.gif").write_bytes(FAKER.gif())

    Note, that all image formats accept `size` (default: `(100, 100)`)
    and `color`(default: `(255, 0, 0)`) arguments.
    """

    def __init__(self, alias: Optional[str] = None) -> None:
        self._words: List[str] = []
        self._first_names: List[str] = []
        self._last_names: List[str] = []

        self.uid = f"{self.__class__.__module__}.{self.__class__.__name__}"
        if alias and alias in ALIAS_REGISTRY:
            LOGGER.warning(
                f"Alias '{alias}' already registered. "
                f"Using '{self.uid}' as alias instead."
            )
            alias = None

        self.alias = alias or self.uid
        if self.uid not in UID_REGISTRY:
            UID_REGISTRY[self.uid] = self
        if self.alias not in ALIAS_REGISTRY:
            ALIAS_REGISTRY[self.alias] = self

        self.load_words()
        self.load_names()

    @staticmethod
    def get_by_uid(uid: str) -> Union["Faker", None]:
        return UID_REGISTRY.get(uid, None)

    @staticmethod
    def get_by_alias(alias: str) -> Union["Faker", None]:
        return ALIAS_REGISTRY.get(alias, None)

    def load_words(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            # Dynamically import 'this' module
            this = __import__("this")

        zen_encoded: str = this.s
        translation_map: Dict[str, str] = {v: k for k, v in this.d.items()}
        zen: str = self._rot13_translate(zen_encoded, translation_map)
        self._words = (
            zen.translate(str.maketrans("", "", string.punctuation))
            .lower()
            .split()
        )

    def load_names(self) -> None:
        authorship_data = AuthorshipData()
        self._first_names = list(authorship_data.first_names)
        self._last_names = list(authorship_data.last_names)

    @staticmethod
    def _rot13_translate(text: str, translation_map: Dict[str, str]) -> str:
        return "".join([translation_map.get(c, c) for c in text])

    @provider
    def uuid(self) -> UUID:
        return uuid.uuid4()

    @provider
    def uuids(self, nb: int = 5) -> List[UUID]:
        return [uuid.uuid4() for _ in range(nb)]

    @provider
    def first_name(self) -> str:
        return random.choice(self._first_names)

    @provider
    def first_names(self, nb: int = 5) -> List[str]:
        return [self.first_name() for _ in range(nb)]

    @provider
    def last_name(self) -> str:
        return random.choice(self._last_names)

    @provider
    def last_names(self, nb: int = 5) -> List[str]:
        return [self.last_name() for _ in range(nb)]

    @provider
    def name(self) -> str:
        return f"{self.first_name()} {self.last_name()}"

    @provider
    def names(self, nb: int = 5) -> List[str]:
        return [self.name() for _ in range(nb)]

    @provider
    def username(self) -> str:
        return (
            f"{self.word()}_{self.word()}_{self.word()}_{self.pystr()}"
        ).lower()

    @provider
    def usernames(self, nb: int = 5) -> List[str]:
        return [self.username() for _ in range(nb)]

    @provider
    def slug(self) -> str:
        return (
            f"{self.word()}-{self.word()}-{self.word()}-{self.pystr()}"
        ).lower()

    @provider
    def slugs(self, nb: int = 5) -> List[str]:
        return [self.slug() for _ in range(nb)]

    @provider
    def word(self) -> str:
        return random.choice(self._words).capitalize()

    @provider
    def words(self, nb: int = 5) -> List[str]:
        return [word.capitalize() for word in random.choices(self._words, k=nb)]

    @provider
    def sentence(self, nb_words: int = 5) -> str:
        return (
            f"{' '.join([self.word() for _ in range(nb_words)]).capitalize()}."
        )

    @provider
    def sentences(self, nb: int = 3) -> List[str]:
        return [self.sentence() for _ in range(nb)]

    @provider
    def paragraph(self, nb_sentences: int = 5) -> str:
        return " ".join([self.sentence() for _ in range(nb_sentences)])

    @provider
    def paragraphs(self, nb: int = 3) -> List[str]:
        return [self.paragraph() for _ in range(nb)]

    @provider
    def text(self, nb_chars: int = 200) -> str:
        current_text: str = ""
        while len(current_text) < nb_chars:
            sentence: str = self.sentence()
            current_text += f" {sentence}" if current_text else sentence
        return current_text[:nb_chars]

    @provider
    def texts(self, nb: int = 3) -> List[str]:
        return [self.text() for _ in range(nb)]

    @provider
    def file_name(self, extension: str = "txt") -> str:
        with NamedTemporaryFile(suffix=f".{extension}") as temp_file:
            return temp_file.name

    @provider
    def email(self, domain: str = "example.com") -> str:
        if not domain:
            domain = "example.com"
        return f"{self.word().lower()}@{domain}"

    @provider
    def url(
        self,
        protocols: Optional[Tuple[str]] = None,
        tlds: Optional[Tuple[str]] = None,
        suffixes: Optional[Tuple[str]] = None,
    ) -> str:
        protocol = random.choice(protocols or ("http", "https"))
        domain = self.word().lower()
        tld = random.choice(
            tlds
            or (
                "com",
                "org",
                "net",
                "io",
            )
        )
        suffix = random.choice(suffixes or (".html", ".php", ".go", "", "/"))
        return f"{protocol}://{domain}.{tld}/{self.word().lower()}{suffix}"

    @provider
    def image_url(
        self,
        width: int = 800,
        height: int = 600,
        service_url: Optional[str] = None,
    ) -> str:
        """Image URL."""
        if service_url is None:
            service_url = random.choice(IMAGE_SERVICES)
        return service_url.format(width=width, height=height)

    @provider
    def pyint(self, min_value: int = 0, max_value: int = 9999) -> int:
        return random.randint(min_value, max_value)

    @provider
    def pybool(self) -> bool:
        return random.choice(
            (
                True,
                False,
            )
        )

    @provider
    def pystr(self, nb_chars: int = 20) -> str:
        return "".join(random.choices(string.ascii_letters, k=nb_chars))

    @provider
    def pyfloat(
        self,
        min_value: float = 0.0,
        max_value: float = 10.0,
    ) -> float:
        return random.uniform(min_value, max_value)

    @provider
    def pydecimal(
        self,
        left_digits: int = 5,
        right_digits: int = 2,
        positive: bool = True,
    ) -> Decimal:
        """Generate a random Decimal number.

        :param left_digits: Number of digits to the left of the decimal point.
        :param right_digits: Number of digits to the right of the decimal point.
        :param positive: If True, the number will be positive, otherwise it
            can be negative.
        :return: A randomly generated Decimal number.
        """
        if left_digits < 0:
            raise ValueError("`left_digits` must be at least 0")
        if right_digits < 0:
            raise ValueError("`right_digits` must be at least 0")

        if left_digits > 0:
            # Generate the integer part
            __lower = 10 ** (left_digits - 1)
            __upper = (10**left_digits) - 1
            int_part = random.randint(__lower, __upper)
        else:
            int_part = 0

        if right_digits > 0:
            # Generate the fractional part
            __lower = 10 ** (right_digits - 1)
            __upper = (10**right_digits) - 1
            fractional_part = random.randint(__lower, __upper)
        else:
            fractional_part = 0

        # Combine both parts
        number = Decimal(f"{int_part}.{fractional_part}")

        # Make the number negative if needed
        if not positive:
            number = -number

        return number

    @provider
    def ipv4(self) -> str:
        return ".".join(str(random.randint(0, 255)) for _ in range(4))

    def _parse_date_string(
        self, date_str: str, tzinfo=timezone.utc
    ) -> datetime:
        """Parse date string with notation below into a datetime object:

        - '5M': 5 minutes from now
        - '-1d': 1 day ago
        - '-1H': 1 hour ago
        - '-365d': 365 days ago

        :param date_str: The date string with shorthand notation.
        :return: A datetime object representing the time offset.
        """
        if date_str in ["now", "today"]:
            return datetime.now(tzinfo)

        match = re.match(r"([+-]?\d+)([dHM])", date_str)
        if not match:
            raise ValueError(
                "Date string format is incorrect. Expected formats like "
                "'-1d', '+2H', '-30M'."
            )
        value, unit = match.groups()
        value = int(value)
        if unit == "d":  # Days
            return datetime.now(tzinfo) + timedelta(days=value)
        elif unit == "H":  # Hours
            return datetime.now(tzinfo) + timedelta(hours=value)

        # Otherwise it's minutes
        return datetime.now(tzinfo) + timedelta(minutes=value)

    @provider
    def date(
        self,
        start_date: str = "-7d",
        end_date: str = "+0d",
        tzinfo=timezone.utc,
    ) -> date:
        """Generate random date between `start_date` and `end_date`.

        :param start_date: The start date from which the random date should
            be generated in the shorthand notation.
        :param end_date: The end date up to which the random date should be
            generated in the shorthand notation.
        :param tzinfo: The timezone.
        :return: A string representing the formatted date.
        """
        start_datetime = self._parse_date_string(start_date, tzinfo)
        end_datetime = self._parse_date_string(end_date, tzinfo)
        time_between_dates = (end_datetime - start_datetime).days
        random_days = random.randrange(
            time_between_dates + 1
        )  # Include the end date
        random_date = start_datetime + timedelta(days=random_days)
        return random_date.date()

    @provider
    def date_time(
        self,
        start_date: str = "-7d",
        end_date: str = "+0d",
        tzinfo=timezone.utc,
    ) -> datetime:
        """Generate a random datetime between `start_date` and `end_date`.

        :param start_date: The start datetime from which the random datetime
            should be generated in the shorthand notation.
        :param end_date: The end datetime up to which the random datetime
            should be generated in the shorthand notation.
        :param tzinfo: The timezone.
        :return: A string representing the formatted datetime.
        """
        start_datetime = self._parse_date_string(start_date, tzinfo)
        end_datetime = self._parse_date_string(end_date, tzinfo)
        time_between_datetimes = int(
            (end_datetime - start_datetime).total_seconds()
        )
        random_seconds = random.randrange(
            time_between_datetimes + 1
        )  # Include the end date time
        random_date_time = start_datetime + timedelta(seconds=random_seconds)
        return random_date_time

    @provider
    def pdf(
        self,
        nb_pages: int = 1,
        generator: Union[
            Type[TextPdfGenerator], Type[GraphicPdfGenerator]
        ] = GraphicPdfGenerator,
        metadata: Optional[MetaData] = None,
        **kwargs,
    ) -> bytes:
        """Create a PDF document of a given size."""
        _pdf = generator(faker=self)
        return _pdf.create(nb_pages=nb_pages, metadata=metadata, **kwargs)

    @provider
    def png(
        self,
        size: Tuple[int, int] = (100, 100),
        color: Tuple[int, int, int] = (0, 0, 255),
    ) -> bytes:
        """Create a PNG image of a specified color.

        :param size: Tuple of width and height of the image in pixels.
        :param color: Color of the image in RGB format (tuple of three
            integers).
        :return: Byte content of the PNG image.
        """
        width, height = size

        # PNG file format header
        png_header = b"\x89PNG\r\n\x1a\n"

        # IHDR chunk: width, height, bit depth, color type, compression,
        # filter, interlace
        ihdr_content = (
            width.to_bytes(4, byteorder="big")
            + height.to_bytes(4, byteorder="big")
            + b"\x08\x02\x00\x00\x00"
        )
        ihdr = b"IHDR" + ihdr_content
        ihdr_chunk = (
            len(ihdr_content).to_bytes(4, byteorder="big")
            + ihdr
            + zlib.crc32(ihdr).to_bytes(4, byteorder="big")
        )

        # IDAT chunk: image data
        raw_data = (
            b"\x00" + bytes(color) * width
        )  # No filter, and RGB data for each pixel
        compressed_data = zlib.compress(raw_data * height)  # Compress the data
        idat_chunk = (
            len(compressed_data).to_bytes(4, byteorder="big")
            + b"IDAT"
            + compressed_data
            + zlib.crc32(b"IDAT" + compressed_data).to_bytes(
                length=4,
                byteorder="big",
            )
        )

        # IEND chunk: marks the image end
        iend_chunk = b"\x00\x00\x00\x00IEND\xAE\x42\x60\x82"

        # Combine all chunks
        png_data = png_header + ihdr_chunk + idat_chunk + iend_chunk

        return png_data

    @provider
    def svg(
        self,
        size: Tuple[int, int] = (100, 100),
        color: Tuple[int, int, int] = (0, 0, 255),
    ) -> bytes:
        """Create a SVG image of a specified color.

        :param size: Tuple of width and height of the image in pixels.
        :param color: Color of the image in RGB format (tuple of three
            integers).
        :return: Byte content of the SVG image.
        """
        width, height = size
        return SVG_TPL.format(width=width, height=height, color=color).encode()

    @provider
    def bmp(
        self,
        size: Tuple[int, int] = (100, 100),
        color: Tuple[int, int, int] = (0, 0, 255),
    ) -> bytes:
        """Create a BMP image of a specified color.

        :param size: Tuple of width and height of the image in pixels.
        :param color: Color of the image in RGB format (tuple of three
            integers).
        :return: Byte content of the BMP image.
        """
        width, height = size

        # BMP Header and DIB Header (BITMAPINFOHEADER format)
        file_header = b"BM"  # Signature
        dib_header = b"\x28\x00\x00\x00"  # DIB Header size (40 bytes)

        # Image width and height
        width_bytes = width.to_bytes(4, byteorder="little")
        height_bytes = height.to_bytes(4, byteorder="little")

        # Image pixel data
        # BMP files are padded to be a multiple of 4 bytes wide
        row_padding = (4 - (3 * width) % 4) % 4
        pixel_data = bytes(color[::-1]) * width + b"\x00" * row_padding
        image_data = pixel_data * height

        # File size
        file_size = (
            14 + 40 + len(image_data)
        )  # 14 bytes file header, 40 bytes DIB header
        file_size_bytes = file_size.to_bytes(4, byteorder="little")

        # Final assembly of the BMP file
        return (
            file_header
            + file_size_bytes
            + b"\x00\x00\x00\x00"
            + b"\x36\x00\x00\x00"  # Reserved 4 bytes
            # Pixel data offset (54 bytes: 14 for file header, 40 for DIB
            # header)
            + dib_header
            + width_bytes
            + height_bytes
            + b"\x01\x00"
            + b"\x18\x00"  # Number of color planes
            + b"\x00\x00\x00\x00"  # Bits per pixel (24 for RGB)
            + len(image_data).to_bytes(  # Compression method (0 for none)
                4, byteorder="little"
            )
            + b"\x13\x0B\x00\x00"  # Size of the raw bitmap data
            # Print resolution of the image (2835 pixels/meter)
            + b"\x13\x0B\x00\x00"
            + b"\x00\x00\x00\x00"
            + b"\x00\x00\x00\x00"  # Number of colors in the palette
            + image_data  # Important colors
        )

    @provider
    def gif(
        self,
        size: Tuple[int, int] = (100, 100),
        color: Tuple[int, int, int] = (0, 0, 255),
    ) -> bytes:
        """Create a GIF image of a specified color.

        :param size: Tuple of width and height of the image in pixels.
        :param color: Color of the image in RGB format (tuple of three
            integers).
        :return: Byte content of the GIF image.
        """
        width, height = size

        # Header
        header = b"GIF89a"

        # Logical Screen Descriptor
        screen_width = width.to_bytes(2, byteorder="little")
        screen_height = height.to_bytes(2, byteorder="little")
        # Global Color Table Flag set to 1, Color resolution, and Sort Flag
        # to 0
        packed_field = b"\xF7"
        bg_color_index = b"\x00"  # Background Color Index
        pixel_aspect_ratio = b"\x00"  # No aspect ratio information

        # Global Color Table.
        # Since it's a single color, we only need one entry in our table,
        # rest are black.
        # Each color is 3 bytes (RGB).
        color_table = bytes(color) + b"\x00" * (3 * 255)

        # Image Descriptor
        image_descriptor = (
            b"\x2C"
            + b"\x00\x00\x00\x00"
            + screen_width
            + screen_height
            + b"\x00"
        )

        # Image Data
        lzw_min_code_size = b"\x08"  # Set to 8 for no compression

        # Image Data Blocks for a single color.
        # Simplest LZW encoding for a single color: clear code, followed
        # by color index, end code.
        image_data_blocks = bytearray(
            [0x02, 0x4C, 0x01, 0x00]
        )  # Compressed data

        # Footer
        footer = b"\x3B"

        # Combine all parts
        return (
            header
            + screen_width
            + screen_height
            + packed_field
            + bg_color_index
            + pixel_aspect_ratio
            + color_table
            + image_descriptor
            + lzw_min_code_size
            + image_data_blocks
            + footer
        )

    @provider
    def image(
        self,
        image_format: Literal["png", "svg", "bmp", "gif"] = "png",
        size: Tuple[int, int] = (100, 100),
        color: Tuple[int, int, int] = (0, 0, 255),
    ) -> bytes:
        if image_format not in {"png", "svg", "bmp", "gif"}:
            raise ValueError()
        image_func = getattr(self, image_format)
        return image_func(size=size, color=color)

    @provider
    def docx(
        self,
        nb_pages: Optional[int] = 1,
        texts: Optional[List[str]] = None,
        metadata: Optional[MetaData] = None,
    ) -> bytes:
        _docx = DocxGenerator(faker=self)
        return _docx.create(nb_pages=nb_pages, texts=texts, metadata=metadata)

    @provider
    def pdf_file(
        self,
        nb_pages: int = 1,
        generator: Union[
            Type[TextPdfGenerator], Type[GraphicPdfGenerator]
        ] = GraphicPdfGenerator,
        metadata: Optional[MetaData] = None,
        storage: Optional[BaseStorage] = None,
        basename: Optional[str] = None,
        prefix: Optional[str] = None,
        **kwargs,
    ) -> StringValue:
        if storage is None:
            storage = FileSystemStorage()
        filename = storage.generate_filename(
            extension="pdf",
            prefix=prefix,
            basename=basename,
        )
        if not metadata:
            metadata = MetaData()
        data = self.pdf(
            nb_pages=nb_pages, generator=generator, metadata=metadata, **kwargs
        )
        storage.write_bytes(filename=filename, data=data)
        file = StringValue(storage.relpath(filename))
        file.data = {
            "storage": storage,
            "filename": filename,
            "content": metadata.content,
        }
        FILE_REGISTRY.add(file)
        return file

    def _image_file(
        self,
        extension: str,
        size: Tuple[int, int] = (100, 100),
        color: Tuple[int, int, int] = (0, 0, 255),
        storage: Optional[BaseStorage] = None,
        basename: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> StringValue:
        if storage is None:
            storage = FileSystemStorage()
        filename = storage.generate_filename(
            extension=extension,
            prefix=prefix,
            basename=basename,
        )
        data = self.png(size=size, color=color)
        storage.write_bytes(filename=filename, data=data)
        file = StringValue(storage.relpath(filename))
        file.data = {"storage": storage, "filename": filename}
        FILE_REGISTRY.add(file)
        return file

    @provider
    def png_file(
        self,
        size: Tuple[int, int] = (100, 100),
        color: Tuple[int, int, int] = (0, 0, 255),
        storage: Optional[BaseStorage] = None,
        basename: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> StringValue:
        return self._image_file(
            extension="png",
            size=size,
            color=color,
            storage=storage,
            basename=basename,
            prefix=prefix,
        )

    @provider
    def svg_file(
        self,
        size: Tuple[int, int] = (100, 100),
        color: Tuple[int, int, int] = (0, 0, 255),
        storage: Optional[BaseStorage] = None,
        basename: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> StringValue:
        return self._image_file(
            extension="svg",
            size=size,
            color=color,
            storage=storage,
            basename=basename,
            prefix=prefix,
        )

    @provider
    def bmp_file(
        self,
        size: Tuple[int, int] = (100, 100),
        color: Tuple[int, int, int] = (0, 0, 255),
        storage: Optional[BaseStorage] = None,
        basename: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> StringValue:
        return self._image_file(
            extension="bmp",
            size=size,
            color=color,
            storage=storage,
            basename=basename,
            prefix=prefix,
        )

    @provider
    def gif_file(
        self,
        size: Tuple[int, int] = (100, 100),
        color: Tuple[int, int, int] = (0, 0, 255),
        storage: Optional[BaseStorage] = None,
        basename: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> StringValue:
        return self._image_file(
            extension="gif",
            size=size,
            color=color,
            storage=storage,
            basename=basename,
            prefix=prefix,
        )

    @provider
    def docx_file(
        self,
        nb_pages: int = 1,
        texts: Optional[List[str]] = None,
        metadata: Optional[MetaData] = None,
        storage: Optional[BaseStorage] = None,
        basename: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> StringValue:
        if storage is None:
            storage = FileSystemStorage()
        filename = storage.generate_filename(
            extension="docx",
            prefix=prefix,
            basename=basename,
        )
        if not metadata:
            metadata = MetaData()
        data = self.docx(texts=texts, metadata=metadata)
        storage.write_bytes(filename=filename, data=data)
        file = StringValue(storage.relpath(filename))
        file.data = {
            "storage": storage,
            "filename": filename,
            "content": metadata.content,
        }
        FILE_REGISTRY.add(file)
        return file

    @provider
    def txt_file(
        self,
        nb_chars: Optional[int] = 200,
        storage: Optional[BaseStorage] = None,
        basename: Optional[str] = None,
        prefix: Optional[str] = None,
        text: Optional[str] = None,
    ) -> StringValue:
        if storage is None:
            storage = FileSystemStorage()
        filename = storage.generate_filename(
            extension="txt",
            prefix=prefix,
            basename=basename,
        )
        if not text:
            if not nb_chars:
                nb_chars = 200
            text = self.text(nb_chars=nb_chars)
        storage.write_text(filename=filename, data=text)  # type: ignore
        file = StringValue(storage.relpath(filename))
        file.data = {
            "storage": storage,
            "filename": filename,
            "content": text,
        }
        FILE_REGISTRY.add(file)
        return file

    @provider
    def generic_file(
        self,
        content: Union[bytes, str],
        extension: str,
        storage: Optional[BaseStorage] = None,
        basename: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> StringValue:
        if storage is None:
            storage = FileSystemStorage()
        filename = storage.generate_filename(
            extension=extension,
            prefix=prefix,
            basename=basename,
        )

        if isinstance(content, bytes):
            storage.write_bytes(filename, content)
        else:
            storage.write_text(filename, content)

        file = StringValue(storage.relpath(filename))
        file.data = {
            "content": content,
            "filename": filename,
            "storage": storage,
        }
        FILE_REGISTRY.add(file)
        return file


FAKER = Faker(alias="default")


class FactoryMethod:
    def __init__(
        self,
        method_name: str,
        faker: Optional[Faker] = None,
        **kwargs,
    ):
        self.method_name = method_name
        self.kwargs = kwargs
        self.faker = faker or FAKER

    def __call__(self):
        method = getattr(self.faker, self.method_name)
        return method(**self.kwargs)


def create_factory_method(method_name):
    def method(self, **kwargs):
        return FactoryMethod(method_name, faker=self.faker, **kwargs)

    return method


class SubFactory:
    def __init__(self, factory_class, **kwargs):
        self.factory_class = factory_class
        self.factory_kwargs = kwargs

    def __call__(self):
        # Initialize the specified factory class and create an instance
        return self.factory_class.create(**self.factory_kwargs)


class Factory:
    """Factory."""

    def __init__(self, faker: Optional[Faker] = None) -> None:
        # Directly use the setter to ensure provider methods are added
        self.faker = faker or FAKER

    @property
    def faker(self):
        return self._faker

    @faker.setter
    def faker(self, value):
        self._faker = value
        self._add_provider_methods(value)

    def _add_provider_methods(self, faker_instance):
        for class_name, methods in PROVIDER_REGISTRY.items():
            if (
                class_name == f"{__name__}.{Faker.__name__}"
                or class_name == self.faker.uid
            ):
                for method_name in methods:
                    if hasattr(faker_instance, method_name):
                        bound_method = create_factory_method(method_name)
                        setattr(self, method_name, bound_method.__get__(self))


FACTORY = Factory(faker=FAKER)


def pre_save(func):
    func.is_pre_save = True
    return func


def post_save(func):
    func.is_post_save = True
    return func


def trait(func):
    func.is_trait = True
    return func


class LazyAttribute:
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        value = self.func(obj)
        setattr(obj, self.func.__name__, value)
        return value


class LazyFunction:
    def __init__(self, func):
        self.func = func

    def __call__(self):
        return self.func()

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self.func()


class PreSave:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def execute(self, instance):
        self.func(instance, *self.args, **self.kwargs)


class PostSave:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def execute(self, instance):
        self.func(instance, *self.args, **self.kwargs)


class ModelFactory:
    """ModelFactory."""

    class Meta:
        get_or_create = ("id",)  # Default fields for get_or_create

    def __init_subclass__(cls, **kwargs):
        base_meta = getattr(
            cls.__bases__[0],
            "_meta",
            {
                attr: getattr(cls.__bases__[0].Meta, attr)  # type: ignore
                for attr in dir(cls.__bases__[0].Meta)  # type: ignore
                if not attr.startswith("_")
            },
        )
        cls_meta = {
            attr: getattr(cls.Meta, attr)
            for attr in dir(cls.Meta)
            if not attr.startswith("_")
        }

        cls._meta = {**base_meta, **cls_meta}  # type: ignore

    @classmethod
    def _run_hooks(cls, hooks, instance):
        for method in hooks:
            getattr(cls, method)(cls, instance)

    @classmethod
    def _apply_traits(cls, instance, **kwargs) -> None:
        for name, method in cls.__dict__.items():
            if getattr(method, "is_trait", False) and kwargs.get(name, False):
                method(cls, instance)

    @classmethod
    def _apply_lazy_attributes(cls, instance, model_data):
        for _field, value in model_data.items():
            if isinstance(value, LazyAttribute):
                # Trigger computation and setting of the attribute
                setattr(instance, _field, value.__get__(instance, cls))

    @classmethod
    def create(cls, **kwargs):
        model = cls.Meta.model  # type: ignore
        trait_keys = {
            name
            for name, method in cls.__dict__.items()
            if getattr(method, "is_trait", False)
        }

        # Collect PreSave, PostSave methods and prepare model data
        pre_save_methods = {}
        post_save_methods = {}
        model_data = {}
        for _field, value in cls.__dict__.items():
            if isinstance(value, PreSave):
                pre_save_methods[_field] = value
            elif isinstance(value, PostSave):
                post_save_methods[_field] = value
            elif not _field.startswith(
                (
                    "_",
                    "Meta",
                )
            ):
                if (
                    not getattr(value, "is_trait", False)
                    and not getattr(value, "is_pre_save", False)
                    and not getattr(value, "is_post_save", False)
                ):
                    model_data[_field] = (
                        value()
                        if isinstance(
                            value, (FactoryMethod, SubFactory, LazyFunction)
                        )
                        else value
                    )

        # Update model_data with non-trait kwargs and collect PreSave from
        # kwargs.
        for key, value in kwargs.items():
            if isinstance(value, PreSave):
                pre_save_methods[key] = value
            elif isinstance(value, PostSave):
                post_save_methods[key] = value
            elif key not in trait_keys and key not in pre_save_methods:
                model_data[key] = value

        # Create a new instance
        instance = model(**model_data)

        # Apply traits
        cls._apply_traits(instance, **kwargs)

        # Apply LazyAttribute values
        cls._apply_lazy_attributes(instance, model_data)

        # Execute PreSave methods
        for __pre_save_method in pre_save_methods.values():
            __pre_save_method.execute(instance)

        # Pre-save hooks
        pre_save_hooks = [
            method
            for method in dir(cls)
            if getattr(getattr(cls, method), "is_pre_save", False)
        ]
        cls._run_hooks(pre_save_hooks, instance)

        # Save the instance
        cls.save(instance)

        # Execute PostSave methods
        for __post_save_method in post_save_methods.values():
            __post_save_method.execute(instance)

        # Post-save hooks
        post_save_hooks = [
            method
            for method in dir(cls)
            if getattr(getattr(cls, method), "is_post_save", False)
        ]
        cls._run_hooks(post_save_hooks, instance)

        return instance

    @classmethod
    def create_batch(cls, count, **kwargs):
        return [cls.create(**kwargs) for _ in range(count)]

    def __new__(cls, **kwargs):
        return cls.create(**kwargs)

    @classmethod
    def save(cls, instance):
        """Save the instance."""


class DjangoModelFactory(ModelFactory):
    """Django ModelFactory."""

    @classmethod
    def save(cls, instance):
        instance.save()

    @classmethod
    def create(cls, **kwargs):
        model = cls.Meta.model  # type: ignore
        unique_fields = cls._meta.get("get_or_create", ["id"])  # type: ignore

        trait_keys = {
            name
            for name, method in cls.__dict__.items()
            if getattr(method, "is_trait", False)
        }

        # Construct a query for unique fields
        query = {
            _field: kwargs[_field]
            for _field in unique_fields
            if _field in kwargs
        }

        # Try to get an existing instance
        if query:
            instance = model.objects.filter(**query).first()
            if instance:
                return instance

        # Collect PreSave methods and prepare model data
        pre_save_methods = {}
        post_save_methods = {}
        model_data = {}
        for _field, value in cls.__dict__.items():
            if isinstance(value, PreSave):
                pre_save_methods[_field] = value
            elif isinstance(value, PostSave):
                post_save_methods[_field] = value
            elif not _field.startswith(
                (
                    "_",
                    "Meta",
                )
            ):
                if (
                    not getattr(value, "is_trait", False)
                    and not getattr(value, "is_pre_save", False)
                    and not getattr(value, "is_post_save", False)
                ):
                    model_data[_field] = (
                        value()
                        if isinstance(
                            value, (FactoryMethod, SubFactory, LazyFunction)
                        )
                        else value
                    )

        # Update model_data with non-trait kwargs and collect PreSave
        # from kwargs.
        for key, value in kwargs.items():
            if isinstance(value, PreSave):
                pre_save_methods[key] = value
            elif isinstance(value, PostSave):
                post_save_methods[key] = value

        # Separate nested attributes and direct attributes
        nested_attrs = {k: v for k, v in kwargs.items() if "__" in k}
        direct_attrs = {k: v for k, v in kwargs.items() if "__" not in k}

        # Update direct attributes with callable results
        for _field, value in model_data.items():
            if isinstance(value, (FactoryMethod, SubFactory)):
                model_data[_field] = (
                    value()
                    if _field not in direct_attrs
                    else direct_attrs[_field]
                )

        # Update model_data with non-trait kwargs and collect PreSave
        # and PostSave from direct_attrs.
        for key, value in direct_attrs.items():
            if isinstance(value, PreSave):
                pre_save_methods[key] = value
            elif isinstance(value, PostSave):
                post_save_methods[key] = value
            elif key not in trait_keys and key not in pre_save_methods:
                model_data[key] = value

        # Create a new instance if none found
        instance = model(**model_data)

        # Apply traits
        cls._apply_traits(instance, **kwargs)

        # Apply LazyAttribute values
        cls._apply_lazy_attributes(instance, model_data)

        # Handle nested attributes
        for attr, value in nested_attrs.items():
            field_name, nested_attr = attr.split("__", 1)
            if isinstance(getattr(cls, field_name, None), SubFactory):
                related_instance = getattr(
                    cls, field_name
                ).factory_class.create(**{nested_attr: value})
                setattr(instance, field_name, related_instance)

        # Execute PreSave methods
        for __pre_save_method in pre_save_methods.values():
            __pre_save_method.execute(instance)

        # Run pre-save hooks
        pre_save_hooks = [
            method
            for method in dir(cls)
            if getattr(getattr(cls, method), "is_pre_save", False)
        ]
        cls._run_hooks(pre_save_hooks, instance)

        # Save instance
        cls.save(instance)

        # Execute PostSave methods
        for __post_save_method in post_save_methods.values():
            __post_save_method.execute(instance)

        # Run post-save hooks
        post_save_hooks = [
            method
            for method in dir(cls)
            if getattr(getattr(cls, method), "is_post_save", False)
        ]
        cls._run_hooks(post_save_hooks, instance)

        return instance


def run_async_in_thread(coroutine):
    """Run an asynchronous coroutine in a separate thread.

    :param coroutine: An asyncio coroutine to be run.
    :return: The result of the coroutine.
    """

    def thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coroutine)

    with ThreadPoolExecutor() as executor:
        future = executor.submit(thread_target)
        return future.result()


class TortoiseModelFactory(ModelFactory):
    """Tortoise ModelFactory."""

    @classmethod
    def save(cls, instance):
        async def async_save():
            await instance.save()

        run_async_in_thread(async_save())

    @classmethod
    def create(cls, **kwargs):
        model = cls.Meta.model  # type: ignore
        unique_fields = cls._meta.get("get_or_create", ["id"])  # type: ignore

        trait_keys = {
            name
            for name, method in cls.__dict__.items()
            if getattr(method, "is_trait", False)
        }

        # Construct a query for unique fields
        query = {
            _field: kwargs[_field]
            for _field in unique_fields
            if _field in kwargs
        }

        # Try to get an existing instance
        if query:

            async def async_filter():
                return await model.filter(**query).first()

            instance = run_async_in_thread(async_filter())
            if instance:
                return instance

        # Collect PreSave, PostSave methods and prepare model data
        pre_save_methods = {}
        post_save_methods = {}
        model_data = {}
        for _field, value in cls.__dict__.items():
            if isinstance(value, PreSave):
                pre_save_methods[_field] = value
            elif isinstance(value, PostSave):
                post_save_methods[_field] = value
            elif not _field.startswith(
                (
                    "_",
                    "Meta",
                )
            ):
                if (
                    not getattr(value, "is_trait", False)
                    and not getattr(value, "is_pre_save", False)
                    and not getattr(value, "is_post_save", False)
                ):
                    model_data[_field] = (
                        value()
                        if isinstance(
                            value, (FactoryMethod, SubFactory, LazyFunction)
                        )
                        else value
                    )

        # Update model_data with non-trait kwargs and collect PreSave
        # and PostSave from kwargs.
        for key, value in kwargs.items():
            if isinstance(value, PreSave):
                pre_save_methods[key] = value
            elif isinstance(value, PostSave):
                post_save_methods[key] = value

        # Separate nested attributes and direct attributes
        nested_attrs = {k: v for k, v in kwargs.items() if "__" in k}
        direct_attrs = {k: v for k, v in kwargs.items() if "__" not in k}

        # Update direct attributes with callable results
        for _field, value in model_data.items():
            if isinstance(value, (FactoryMethod, SubFactory)):
                model_data[_field] = (
                    value()
                    if _field not in direct_attrs
                    else direct_attrs[_field]
                )

        # Update model_data with non-trait kwargs and collect PreSave
        # from direct_attrs.
        for key, value in direct_attrs.items():
            if isinstance(value, PreSave):
                pre_save_methods[key] = value
            elif isinstance(value, PostSave):
                post_save_methods[key] = value
            elif key not in trait_keys and key not in pre_save_methods:
                model_data[key] = value

        # Create a new instance if none found
        instance = model(**model_data)

        # Apply traits
        cls._apply_traits(instance, **kwargs)

        # Apply LazyAttribute values
        cls._apply_lazy_attributes(instance, model_data)

        # Handle nested attributes
        for attr, value in nested_attrs.items():
            field_name, nested_attr = attr.split("__", 1)
            if isinstance(getattr(cls, field_name, None), SubFactory):

                async def async_related_instance():
                    return getattr(cls, field_name).factory_class.create(
                        **{nested_attr: value}
                    )

                related_instance = run_async_in_thread(async_related_instance())
                setattr(instance, field_name, related_instance)

        # Execute PreSave methods
        for __pre_save_method in pre_save_methods.values():
            __pre_save_method.execute(instance)

        # Run pre-save hooks
        pre_save_hooks = [
            method
            for method in dir(cls)
            if getattr(getattr(cls, method), "is_pre_save", False)
        ]
        cls._run_hooks(pre_save_hooks, instance)

        # Save instance
        cls.save(instance)

        # Execute PostSave methods
        for __post_save_method in post_save_methods.values():
            __post_save_method.execute(instance)

        # Run post-save hooks
        post_save_hooks = [
            method
            for method in dir(cls)
            if getattr(getattr(cls, method), "is_post_save", False)
        ]
        cls._run_hooks(post_save_hooks, instance)

        return instance


class SQLAlchemyModelFactory(ModelFactory):
    """SQLAlchemy ModelFactory."""

    @classmethod
    def save(cls, instance):
        session = cls.MetaSQLAlchemy.get_session()  # type: ignore
        session.add(instance)
        session.commit()

    @classmethod
    def create(cls, **kwargs):
        session = cls.MetaSQLAlchemy.get_session()  # type: ignore

        model = cls.Meta.model  # type: ignore
        unique_fields = cls._meta.get("get_or_create", ["id"])  # type: ignore

        trait_keys = {
            name
            for name, method in cls.__dict__.items()
            if getattr(method, "is_trait", False)
        }

        # Check for existing instance
        if unique_fields:
            query_kwargs = {
                _field: kwargs.get(_field) for _field in unique_fields
            }
            instance = session.query(model).filter_by(**query_kwargs).first()
            if instance:
                return instance

        # Collect PreSave, PostSave methods and prepare model data
        pre_save_methods = {}
        post_save_methods = {}
        model_data = {}
        for _field, value in cls.__dict__.items():
            if isinstance(value, PreSave):
                pre_save_methods[_field] = value
            elif isinstance(value, PostSave):
                post_save_methods[_field] = value
            elif not _field.startswith(
                (
                    "_",
                    "Meta",
                )
            ):
                if (
                    not getattr(value, "is_trait", False)
                    and not getattr(value, "is_pre_save", False)
                    and not getattr(value, "is_post_save", False)
                ):
                    model_data[_field] = (
                        value()
                        if isinstance(
                            value, (FactoryMethod, SubFactory, LazyFunction)
                        )
                        else value
                    )

        # Update model_data with non-trait kwargs and collect PreSave
        # from kwargs.
        for key, value in kwargs.items():
            if isinstance(value, PreSave):
                pre_save_methods[key] = value
            elif isinstance(value, PostSave):
                post_save_methods[key] = value

        # Separate nested attributes and direct attributes
        nested_attrs = {k: v for k, v in kwargs.items() if "__" in k}
        direct_attrs = {k: v for k, v in kwargs.items() if "__" not in k}

        # Update direct attributes with callable results
        for _field, value in model_data.items():
            if isinstance(value, (FactoryMethod, SubFactory)):
                model_data[_field] = (
                    value()
                    if _field not in direct_attrs
                    else direct_attrs[_field]
                )

        # Update model_data with non-trait kwargs and collect PreSave
        # from direct_attrs.
        for key, value in direct_attrs.items():
            if isinstance(value, PreSave):
                pre_save_methods[key] = value
            elif isinstance(value, PostSave):
                post_save_methods[key] = value
            elif key not in trait_keys and key not in pre_save_methods:
                model_data[key] = value

        # Create a new instance
        instance = model(**model_data)

        # Apply traits
        cls._apply_traits(instance, **kwargs)

        # Apply LazyAttribute values
        cls._apply_lazy_attributes(instance, model_data)

        # Handle nested attributes
        for attr, value in nested_attrs.items():
            field_name, nested_attr = attr.split("__", 1)
            if isinstance(getattr(cls, field_name, None), SubFactory):
                related_instance = getattr(
                    cls, field_name
                ).factory_class.create(**{nested_attr: value})
                setattr(instance, field_name, related_instance)

        # Execute PreSave methods
        for __pre_save_method in pre_save_methods.values():
            __pre_save_method.execute(instance)

        # Run pre-save hooks
        pre_save_hooks = [
            method
            for method in dir(cls)
            if getattr(getattr(cls, method), "is_pre_save", False)
        ]
        cls._run_hooks(pre_save_hooks, instance)

        # Save instance
        cls.save(instance)

        # Execute PostSave methods
        for __post_save_method in post_save_methods.values():
            __post_save_method.execute(instance)

        # Run post-save hooks
        post_save_hooks = [
            method
            for method in dir(cls)
            if getattr(getattr(cls, method), "is_post_save", False)
        ]
        cls._run_hooks(post_save_hooks, instance)

        return instance


# ************************************************
# ******************* Internal *******************
# ************************************************


# TODO: Remove once Python 3.8 support is dropped
class ClassProperty(property):
    """ClassProperty."""

    def __get__(self, cls, owner):
        """Get."""
        return classmethod(self.fget).__get__(None, owner)()  # type: ignore


classproperty = ClassProperty


def xor_transform(val: str, key: int = 10) -> str:
    """Simple, deterministic string encoder/decoder.

    Usage example:

    .. code-block:: python

        val = "abcd"
        encoded_val = xor_transform(val)
        decoded_val = xor_transform(encoded_val)
    """
    return "".join(chr(ord(__c) ^ key) for __c in val)


class BaseDataFiller:
    TYPE_TO_PROVIDER = {
        bool: FAKER.pybool,
        int: FAKER.pyint,
        str: FAKER.pystr,
        datetime: FAKER.date_time,
        date: FAKER.date,
        float: FAKER.pyfloat,
        Decimal: FAKER.pydecimal,
    }

    FIELD_NAME_TO_PROVIDER = {
        "name": FAKER.word,
        "title": FAKER.sentence,
        "slug": FAKER.slug,
        "content": FAKER.text,
        "category": FAKER.word,
        "username": FAKER.username,
        "email": FAKER.email,
        "headline": FAKER.sentence,
        "first_name": FAKER.first_name,
        "last_name": FAKER.last_name,
        "uuid": FAKER.uuid,
        "body": FAKER.text,
        "summary": FAKER.paragraph,
        "date_of_birth": FAKER.date,
        "dob": FAKER.date,
        "age": partial(FAKER.pyint, min_value=1, max_value=100),
        "url": FAKER.url,
    }

    @classmethod
    def get_provider_for_field_name(cls, field_name) -> Optional[Callable]:
        return BaseDataFiller.FIELD_NAME_TO_PROVIDER.get(field_name)


class DataclassDataFiller(BaseDataFiller):
    @classmethod
    def get_provider_for_type(cls, field_type) -> Optional[Callable]:
        """Get provider function for the type given."""
        # Extract the base type from Optional
        if get_origin(field_type) is Optional:
            field_type = get_args(field_type)[0]
        return cls.TYPE_TO_PROVIDER.get(field_type)

    @classmethod
    def fill(cls, dataclass_type: Type) -> Any:
        """Fill dataclass with data."""
        if not is_dataclass(dataclass_type):
            raise ValueError("The provided type must be a dataclass")

        kwargs = {}
        for _field in fields(dataclass_type):
            provider_func = cls.get_provider_for_field_name(_field.name)
            if not provider_func:
                if is_dataclass(_field.type):
                    # Recursive call for nested dataclass
                    def provider_func():
                        return cls.fill(_field.type)

                else:
                    provider_func = cls.get_provider_for_type(_field.type)

            if provider_func:
                kwargs[_field.name] = provider_func()
            else:
                # Skip if no provider function is defined
                continue

        return dataclass_type(**kwargs)


fill_dataclass = DataclassDataFiller.fill


class PydanticDataFiller(BaseDataFiller):
    @classmethod
    def get_provider_for_type(cls, field_type) -> Optional[Callable]:
        if isinstance(field_type, type) and issubclass(
            field_type, (list, dict, set)
        ):
            return None
        if (
            hasattr(field_type, "__origin__")
            and field_type.__origin__ is Optional  # noqa
        ):
            field_type = field_type.__args__[0]  # noqa
        return cls.TYPE_TO_PROVIDER.get(field_type)

    @classmethod
    def is_class_type(cls, type_hint):
        return isinstance(type_hint, type) and not any(
            issubclass(type_hint, primitive)
            for primitive in (int, str, float, bool, Decimal)
        )

    @classmethod
    def fill(cls, object_type: Type) -> Any:
        if not (
            hasattr(object_type, "__fields__")
            and hasattr(object_type, "Config")
        ):
            raise ValueError("The provided type must be a Pydantic model")

        type_hints = get_type_hints(object_type)

        kwargs = {}
        for field_name, field_type in type_hints.items():
            # Check for Pydantic's default_factory
            default_factory = getattr(
                object_type.__fields__[field_name], "default_factory", None
            )
            if default_factory is not None:
                kwargs[field_name] = default_factory()
                continue

            provider_func = cls.get_provider_for_field_name(field_name)

            if not provider_func:
                if cls.is_class_type(field_type):
                    kwargs[field_name] = cls.fill(field_type)
                else:
                    provider_func = cls.get_provider_for_type(field_type)
                    if provider_func:
                        kwargs[field_name] = provider_func()
                    else:
                        continue
            else:
                kwargs[field_name] = provider_func()
        return object_type(**kwargs)


fill_pydantic_model = PydanticDataFiller.fill
