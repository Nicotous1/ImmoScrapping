from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Generic, Iterable, Protocol, TypeVar, Union

import boto3

from . import nexity

REGION_NAME: str = "eu-west-3"
ME_EMAIL: str = "ntoussai29@gmail.com"

SES_CLIENT = Any
S3_CLIENT = Any


def build_client_email() -> SES_CLIENT:
    client = boto3.client("ses", region_name=REGION_NAME)
    return client


def send_text_email(
    client: SES_CLIENT, author: str, to: str, title: str, text: str
) -> None:
    response = client.send_email(
        Source=author,
        Destination={
            "ToAddresses": [
                to,
            ],
        },
        Message={
            "Subject": {
                "Data": title,
            },
            "Body": {
                "Text": {
                    "Data": text,
                },
                "Html": {
                    "Data": text,
                },
            },
        },
    )


def send_me_email_with_text(client: SES_CLIENT, title: str, text: str) -> None:
    send_text_email(client, ME_EMAIL, ME_EMAIL, title, text)


def create_client_and_send_me_email_with_text(title: str, text: str) -> None:
    client = build_client_email()
    send_me_email_with_text(client, title, text)


def create_client_S3() -> S3_CLIENT:
    return boto3.client("s3", region_name=REGION_NAME)


def create_resource_s3() -> Any:
    s3 = boto3.resource("s3")
    return s3


BUCKET = Any


def iter_aws_object_desc_from_bucket_to_S3File(
    object_descs: Iterable[Any], bucket: "S3Bucket"
) -> Iterable["S3File"]:
    for desc in object_descs:
        yield S3File.create_from_aws_object_desc_and_bucket(desc, bucket)


@dataclass
class S3Bucket:
    name: str
    aws: Any

    def upload(self, file: Path, key: str) -> None:
        self.aws.upload_file(str(file), key)

    def upload_to_root(self, file: Path) -> None:
        s3_file = S3File.create_root_file_for_bucket_from_path(self, file)
        s3_file.upload(file)

    def iter_files(self) -> Iterable["S3File"]:
        return iter_aws_object_desc_from_bucket_to_S3File(self.aws.objects.all(), self)

    def download_all_to_folder(self, folder: Path) -> None:
        for file in self.iter_files():
            file.download_to_folder(folder)

    def download_all_missing_to_folder(self, folder: Path) -> None:
        for file in self.iter_files():
            file.download_to_folder_if_missing(folder)

    def iter_files_prefixed(self, prefix: str):
        return iter_aws_object_desc_from_bucket_to_S3File(
            self.aws.objects.filter(Prefix=prefix), self
        )

    def check_key_exists(self, key: str) -> bool:
        for file_with_prefix in self.iter_files_prefixed(key):
            if file_with_prefix.key == key:
                return True
        return False

    def check_same_bucket(self, bucket: "S3Bucket") -> bool:
        return bucket.name == self.name

    def check_contains_s3_file(self, file: "S3File") -> bool:
        same_bucket = self.check_same_bucket(file.bucket)
        has_same_file = self.check_key_exists(file.key)
        contains_file = same_bucket and has_same_file
        return contains_file

    def upload_folder_files_missing_from_root(self, folder: Path) -> None:
        return self.upload_files_missing_from_root(folder.iterdir())

    def upload_files_missing_from_root(self, files: Iterable[Path]) -> None:
        for source in files:
            s3_file = S3File.create_root_file_for_bucket_from_path(self, source)
            s3_file.upload_if_not_exists(source)


def create_s3_object_from_bucket_and_key(bucket: str, key: str) -> Any:
    s3 = boto3.resource("s3")
    object = s3.Object(bucket, key)  # type: ignore
    return object


@dataclass
class S3File:
    key: str
    bucket: S3Bucket
    aws: Any

    @classmethod
    def create_from_aws_object_desc_and_bucket(
        cls, aws_desc: Any, bucket: S3Bucket
    ) -> "S3File":
        bucket_name = bucket.name
        key = aws_desc.key
        aws_obj = create_s3_object_from_bucket_and_key(
            bucket_name,
            key,
        )
        return S3File(key, bucket, aws_obj)

    @classmethod
    def creat_from_bucket_and_key(cls, bucket: S3Bucket, key: str) -> "S3File":
        aws = create_s3_object_from_bucket_and_key(bucket.name, key)
        return S3File(key, bucket, aws)

    @classmethod
    def create_root_file_for_bucket_from_path(
        cls, bucket: S3Bucket, path: Path
    ) -> "S3File":
        key = path.name
        return cls.creat_from_bucket_and_key(bucket, key)

    def download_to(self, path: Path) -> None:
        print(f"{self.key} download to -> {path}")
        self.aws.download_file(str(path))

    def download_to_folder(self, folder: Path) -> None:
        path = folder / self.key
        self.download_to(path)

    def download_to_folder_if_missing(self, folder: Path) -> None:
        path = folder / self.key
        if not path.exists():
            self.download_to(path)

    def check_if_exists(self) -> bool:
        return self.bucket.check_contains_s3_file(self)

    def upload(self, source: Path) -> None:
        self.bucket.upload(source, self.key)

    def upload_if_not_exists(self, source: Path) -> None:
        exists_already = self.check_if_exists()
        if not (exists_already):
            self.upload(source)


def create_bucket_from_name(name: str) -> S3Bucket:
    s3 = create_resource_s3()
    bucket = s3.Bucket(name)
    return S3Bucket(name, bucket)


NEXITY_S3_NAME: str = "nexity-web-scrapping"


def create_nexity_bucket() -> S3Bucket:
    return create_bucket_from_name(NEXITY_S3_NAME)


def iter_extension_of_folder(folder: Path, ext: str) -> Iterable[Path]:
    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() == f".{ext.lower()}":
            yield file


def upload_new_htmls_to_nexity_bucket(folder: Path) -> None:
    bucket = create_nexity_bucket()
    html_files = iter_extension_of_folder(folder, "html")
    bucket.upload_files_missing_from_root(html_files)


@dataclass
class NexityS3File:
    s3_file: S3File
    date: date


def create_NexityS3File_from_s3_file(file: S3File) -> NexityS3File:
    name = file.key
    date = nexity.extract_date_from_signal_html_file(name)
    return NexityS3File(file, date)


def iter_nexity_s3_file_of_bucket(bucket: S3Bucket) -> Iterable[NexityS3File]:
    for signal_s3_file in bucket.iter_files_prefixed(nexity.NEXITY_FILE_PREFIX):
        yield create_NexityS3File_from_s3_file(signal_s3_file)


from . import histories, nexity

NEXITY_S3_OS_HISTORY = histories.ShortHistory[Union[NexityS3File, nexity.NexityFile]]


def create_history_from_s3_bucket_and_current_file(
    bucket: S3Bucket, current: nexity.NexityFile
) -> NEXITY_S3_OS_HISTORY:
    s3_files = iter_nexity_s3_file_of_bucket(bucket)
    return histories.create_short_history_from_iterable(current, s3_files)


def download_if_nexity_s3file(folder: Path, data: Any) -> None:
    if isinstance(data, NexityS3File):
        data.s3_file.download_to_folder(folder)


def download_history_previous_and_orignal_to_folder(
    history: NEXITY_S3_OS_HISTORY, folder: Path
) -> None:
    download_if_nexity_s3file(folder, history.previous)
    download_if_nexity_s3file(folder, history.original)
